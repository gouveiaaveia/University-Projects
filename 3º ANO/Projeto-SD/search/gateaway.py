from concurrent import futures
import grpc
import index_pb2
import index_pb2_grpc
from google.protobuf import empty_pb2
import time
import sys
import queue       
import threading        
import collections 
import pickle      
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from pybloom_live import BloomFilter
from cachetools import TTLCache

# Carregar variáveis de ambiente da raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / '.env')

class Gateway(index_pb2_grpc.IndexServicer):
    
    GATEWAY_STATE_FILE = 'gateway_state.pkl'
    GATEWAY_BLOOM_FILE = 'gateway_bloom.bin'
    CHECKPOINT_INTERVAL_SECONDS = 20
    BARREL_TIMEOUT_SECONDS = 30 
    LEASE_TIMEOUT_SECONDS = 120 
    
    AOF_FILE = 'gateway_aof.log'
    
    BLOOM_CAPACITY = 1000000 
    BLOOM_ERROR_RATE = 0.001 
    
    CACHE_MAX_SIZE = 256
    CACHE_TTL_SECONDS = 30 
    
    SEARCH_TIMES_MAX_LEN = 1000

    def __init__(self):
        
        print("Gateway a iniciar em modo dinâmico (Registo de Serviços).")
        self.active_barrels = collections.OrderedDict() 
        self.barrel_lock = threading.Lock()
        self.barrel_channels = {}
        self.barrel_stubs = {}
        self.search_times = {}
        
        # Contador de pesquisas (centralizado no Gateway)
        self.search_queries = {}
        self.search_queries_lock = threading.Lock()
        
        # Sistema de notificações event-driven para estatísticas
        self._stats_observers = []  # Lista de callbacks a notificar
        self._stats_observers_lock = threading.Lock()
        self._stats_changed = threading.Event()  # Flag que indica mudança
        self._last_stats_snapshot = None  # Cache do último estado
        
        self.rr_lock = threading.Lock()
        self.round_robin_index = 0

        self.queue_lock = threading.Lock()
        self.save_lock = threading.Lock()
        self.leased_urls = {} 

        self.aof_lock = threading.Lock()
        try:
            self.aof_file = open(self.AOF_FILE, 'a')
        except Exception as e:
            print(f"ERRO CRÍTICO: Não foi possível abrir o ficheiro AOF: {e}")
            sys.exit(1)

        print(f"A iniciar Cache de Pesquisas (TTL, maxsize={self.CACHE_MAX_SIZE}, ttl={self.CACHE_TTL_SECONDS})...")
        self.search_cache = TTLCache(maxsize=self.CACHE_MAX_SIZE, ttl=self.CACHE_TTL_SECONDS)
        self.cache_lock = threading.Lock()

        self.load_state() 
        self.load_aof()
        
        # Iniciar thread de notificação de eventos
        self._start_stats_notifier()

        self.stop_event = threading.Event()
        
        print(f"A iniciar thread de checkpointing da Fila (a cada {self.CHECKPOINT_INTERVAL_SECONDS}s)...")
        self.checkpoint_thread = threading.Thread(
            target=self._checkpoint_loop, 
            daemon=True
        )
        self.checkpoint_thread.start()
        
        print(f"A iniciar thread de verificação de heartbeats (timeout: {self.BARREL_TIMEOUT_SECONDS}s)...")
        self.heartbeat_check_thread = threading.Thread(
            target=self._check_barrel_heartbeats, 
            daemon=True
        )
        self.heartbeat_check_thread.start()
        
        print(f"A iniciar thread de verificação de Leases (timeout: {self.LEASE_TIMEOUT_SECONDS}s)...")
        self.lease_check_thread = threading.Thread(
            target=self._check_leases,
            daemon=True
        )
        self.lease_check_thread.start()


    # ========== Sistema de Eventos (Event-Driven Stats) ==========
    
    def _start_stats_notifier(self):
        """Inicia a thread que notifica observers quando há mudanças."""
        print("[Gateway Events] A iniciar sistema de notificação event-driven...")
        self._notifier_thread = threading.Thread(
            target=self._stats_notifier_loop,
            daemon=True
        )
        self._notifier_thread.start()
    
    def _stats_notifier_loop(self):
        """Thread que aguarda eventos e notifica observers."""
        while not self.stop_event.is_set():
            # Espera por um evento de mudança ou timeout (para verificar barrels)
            # Timeout de 5 segundos para verificar mudanças nos barrels
            changed = self._stats_changed.wait(timeout=5.0)
            
            if self.stop_event.is_set():
                break
            
            # Limpa a flag se foi sinalizada
            if changed:
                self._stats_changed.clear()
            
            # Verificar se realmente houve mudança nas stats
            current_snapshot = self._get_stats_snapshot()
            
            if current_snapshot != self._last_stats_snapshot:
                self._last_stats_snapshot = current_snapshot
                self._broadcast_to_observers(current_snapshot)
    
    def _get_stats_snapshot(self) -> dict:
        """Obtém um snapshot das estatísticas atuais."""
        all_barrel_infos = []
        
        with self.barrel_lock:
            stubs_snapshot = list(self.barrel_stubs.items())
        
        for addr, stub in stubs_snapshot:
            try:
                stats = stub.getStatistics(empty_pb2.Empty())
                times = self.search_times.get(addr, [])
                avg_response_time = (sum(times) / len(times)) if times else 0.0
                
                barrel_info = stats.barrels[0]
                all_barrel_infos.append({
                    'barrel_id': barrel_info.barrel_id,
                    'indexed_words_count': barrel_info.indexed_words_count,
                    'avg_response_time': avg_response_time
                })
            except grpc.RpcError:
                pass
        
        with self.search_queries_lock:
            top_10 = sorted(self.search_queries.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'top_searches': [{'query': q, 'count': c} for q, c in top_10],
            'barrels': all_barrel_infos
        }
    
    def _broadcast_to_observers(self, stats: dict):
        """Envia as estatísticas para todos os observers registados."""
        with self._stats_observers_lock:
            observers = list(self._stats_observers)
        
        for callback in observers:
            try:
                callback(stats)
            except Exception as e:
                print(f"[Gateway Events] Erro ao notificar observer: {e}")
    
    def _notify_stats_changed(self):
        """Sinaliza que houve uma mudança nas estatísticas."""
        self._stats_changed.set()
    
    def register_stats_observer(self, callback):
        """Regista um callback para receber notificações de estatísticas."""
        with self._stats_observers_lock:
            self._stats_observers.append(callback)
            print(f"[Gateway Events] Novo observer registado. Total: {len(self._stats_observers)}")
    
    def unregister_stats_observer(self, callback):
        """Remove um callback da lista de observers."""
        with self._stats_observers_lock:
            if callback in self._stats_observers:
                self._stats_observers.remove(callback)
                print(f"[Gateway Events] Observer removido. Total: {len(self._stats_observers)}")

    # ========== Checkpoint e Estado ==========
    
    def _checkpoint_loop(self):
        while not self.stop_event.wait(self.CHECKPOINT_INTERVAL_SECONDS):
            print("\n[Gateway Checkpoint] A guardar estado (Fila e Filtro de Bloom)...")
            self.save_state()
            print("[Gateway Checkpoint] Estado guardado.")
        print("[Gateway Checkpoint] Thread de checkpoint a encerrar.")

    def stop_checkpoint_thread(self):
        print("A parar a thread de checkpoint da Fila...")
        self.stop_event.set()
        if hasattr(self, 'checkpoint_thread') and self.checkpoint_thread.is_alive():
            self.checkpoint_thread.join()
        if hasattr(self, 'heartbeat_check_thread') and self.heartbeat_check_thread.is_alive():
            self.heartbeat_check_thread.join()
        if hasattr(self, 'lease_check_thread') and self.lease_check_thread.is_alive():
            self.lease_check_thread.join()
        print("Threads de background paradas.")
        
    def initialize_empty_state(self):
        print("Gateway a iniciar com fila vazia e novo Filtro de Bloom.")
        self.urls_to_index = queue.Queue()
        self.processed_filter = BloomFilter(
            capacity=self.BLOOM_CAPACITY, 
            error_rate=self.BLOOM_ERROR_RATE
        )
        self.leased_urls = {} 
        print(f"  - Filtro de Bloom criado (Capacidade: {self.BLOOM_CAPACITY}, Erro: {self.BLOOM_ERROR_RATE})")

    def load_aof(self):
        """Recupera o estado do AOF (operações desde o último checkpoint)."""
        print(f"A carregar operações não guardadas do AOF ('{self.AOF_FILE}')...")
        processed_count = 0
        put_count = 0
        try:
            with open(self.AOF_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                        
                    parts = line.split(' ', 1)
                    if len(parts) != 2:
                        continue

                    op, url = parts
                    
                    with self.queue_lock:
                        if op == "ACK":
                            self.processed_filter.add(url)
                            processed_count += 1
                        
                        elif op == "PUT":
                            if url not in self.processed_filter:
                                self.urls_to_index.put(url)
                            put_count += 1
                        
        except FileNotFoundError:
            print("Ficheiro AOF não encontrado (normal na primeira execução).")
        except Exception as e:
            print(f"ERRO CRÍTICO ao carregar AOF: {e}. O estado pode estar incompleto.")
        
        print(f"Recuperação AOF concluída: {processed_count} ACKs, {put_count} PUTs.")

    def load_state(self):
        if not os.path.exists(self.GATEWAY_STATE_FILE) or not os.path.exists(self.GATEWAY_BLOOM_FILE):
            print(f"Ficheiro de estado da Fila ('{self.GATEWAY_STATE_FILE}') ou")
            print(f"Ficheiro do Filtro de Bloom ('{self.GATEWAY_BLOOM_FILE}') não encontrado.")
            self.initialize_empty_state()
            return

        try:
            with self.save_lock: 
                with open(self.GATEWAY_STATE_FILE, 'rb') as f:
                    state = pickle.load(f)
            
            self.urls_to_index = queue.Queue()
            urls_list = state.get('urls_to_index_list', [])
            for url in urls_list:
                self.urls_to_index.put(url)
            
            leased_urls_list = state.get('leased_urls_list', [])
            if leased_urls_list:
                 print(f"  - A recolocar {len(leased_urls_list)} URLs (lease interrompido).")
                 for url in leased_urls_list:
                     self.urls_to_index.put(url)
            self.leased_urls = {} 
            
            # Carregar contadores de pesquisa
            with self.search_queries_lock:
                self.search_queries = state.get('search_queries', {})
            search_count = len(self.search_queries)
            
            print(f"Estado da Fila carregado de '{self.GATEWAY_STATE_FILE}'.")
            print(f"  - {self.urls_to_index.qsize()} URLs na fila.")
            print(f"  - {search_count} termos de pesquisa no histórico.")

            with self.queue_lock:
                 with open(self.GATEWAY_BLOOM_FILE, 'rb') as f:
                    self.processed_filter = BloomFilter.fromfile(f)
            print(f"Filtro de Bloom carregado de '{self.GATEWAY_BLOOM_FILE}'.")

        except Exception as e:
            print(f"ERRO CRÍTICO ao carregar estado (Fila ou Filtro): {e}")
            print("A iniciar com estado vazio para segurança.")
            self.initialize_empty_state()

    def save_state(self):
        """Guarda o estado 'pickle' e 'bloom' e limpa o AOF."""
        
        with self.save_lock:
        
            with self.queue_lock:
                urls_list = list(self.urls_to_index.queue)
                leased_list = list(self.leased_urls.keys())
            
            # Incluir contadores de pesquisa no estado
            with self.search_queries_lock:
                search_queries_copy = self.search_queries.copy()
            
            state = {
                'urls_to_index_list': urls_list,
                'leased_urls_list': leased_list,
                'search_queries': search_queries_copy
            }
            
            try:
                temp_file = self.GATEWAY_STATE_FILE + '.tmp'
                with open(temp_file, 'wb') as f:
                    pickle.dump(state, f, pickle.HIGHEST_PROTOCOL)
                os.replace(temp_file, self.GATEWAY_STATE_FILE)
            except Exception as e:
                print(f"\n[Gateway] ERRO CRÍTICO ao guardar o estado da Fila: {e}")
                return 

        with self.queue_lock: 
            try:
                temp_file_bloom = self.GATEWAY_BLOOM_FILE + '.tmp'
                with open(temp_file_bloom, 'wb') as f:
                    self.processed_filter.tofile(f)
                os.replace(temp_file_bloom, self.GATEWAY_BLOOM_FILE)
            except Exception as e:
                print(f"\n[Gateway] ERRO CRÍTICO ao guardar o Filtro de Bloom: {e}")
                return 
        
        try:
            with self.aof_lock:
                self.aof_file.truncate(0)
        except Exception as e:
            print(f"\n[Gateway] ERRO CRÍTICO ao limpar o AOF: {e}")
            

    def _check_leases(self):
        """Thread que verifica leases expirados e recoloca URLs na fila."""
        while not self.stop_event.is_set():
            self.stop_event.wait(self.LEASE_TIMEOUT_SECONDS / 2) 
            
            now = time.time()
            requeue_urls = []
            
            try:
                with self.queue_lock:
                    for url, lease_time in list(self.leased_urls.items()):
                        if now - lease_time > self.LEASE_TIMEOUT_SECONDS:
                            print(f"[Gateway Lease] URL expirado: {url}")
                            requeue_urls.append(url)
                            self.leased_urls.pop(url, None) 
                
                    if requeue_urls:
                        print(f"[Gateway Lease] A recolocar {len(requeue_urls)} URLs na fila principal.")
                        for url in requeue_urls:
                            if url not in self.processed_filter:
                                self.urls_to_index.put(url)
            except Exception as e:
                 print(f"[Gateway Lease] Erro na thread _check_leases: {e}")

    def takeNext(self, request, context):
        """Entrega o próximo URL da fila e o "aluga" (atómico)."""
        
        try:
            with self.queue_lock: 
                url = self.urls_to_index.get_nowait()
                # Adiciona ao lease DENTRO do mesmo lock
                self.leased_urls[url] = time.time()
                
            return index_pb2.TakeNextResponse(url=url)
        
        except queue.Empty:
            return index_pb2.TakeNextResponse() 

    def putNew(self, request, context):
        """Adiciona um URL à fila central se ainda não foi processado (thread-safe)."""
        url = request.url
        added_to_queue = False
        
        with self.queue_lock: 
            if url not in self.processed_filter:
                self.urls_to_index.put(url)
                added_to_queue = True
        
        if added_to_queue:
            try:
                with self.aof_lock:
                    self.aof_file.write(f"PUT {url}\n")
                    self.aof_file.flush()
            except Exception as e:
                print(f"[Gateway AOF] ERRO CRÍTICO ao escrever PUT no AOF: {e}")
                
        return empty_pb2.Empty()
    
    def AcknowledgeUrl(self, request, context):
        """Downloader chama este método para confirmar que processou o URL."""
        url = request.url
        
        # FIX 1.1: Usar o self.queue_lock
        with self.queue_lock: 
            # 1. Adiciona ao filtro
            self.processed_filter.add(url)
            # 2. Remove da lista de lease
            self.leased_urls.pop(url, None)
        
        try:
            with self.aof_lock:
                self.aof_file.write(f"ACK {url}\n")
                self.aof_file.flush()
        except Exception as e:
            print(f"[Gateway AOF] ERRO CRÍTICO ao escrever ACK no AOF: {e}")
            
        return empty_pb2.Empty()
    
    
    def IndexPageData(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Método de Escrita. Chame diretamente os Barrels, não o Gateway.')
        return index_pb2.IndexWordsResponse()

    def AddPageLinks(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Método de Escrita. Chame diretamente os Barrels, não o Gateway.')
        return empty_pb2.Empty()

    def _execute_read(self, rpc_call_function, empty_response):
        stubs_list = []
        num_barrels = 0
        
        with self.barrel_lock:
            stubs_list = list(self.barrel_stubs.items())
            num_barrels = len(stubs_list)
        
        if not stubs_list:
            print(f"Gateway: ERRO CRÍTICO! Nenhum barrel disponível para leitura.")
            return empty_response

        start_index = 0
        with self.rr_lock: 
            if num_barrels > 0:
                start_index = self.round_robin_index % num_barrels
                self.round_robin_index = (start_index + 1) % num_barrels
            else:
                self.round_robin_index = 0
        
        stubs_to_try = stubs_list[start_index:] + stubs_list[:start_index]

        for addr, stub in stubs_to_try:
            try:
                start_time = time.time()
                resp = rpc_call_function(stub) 
                elapsed_time = time.time() - start_time
                
                self.search_times[addr].append(elapsed_time) 
             
                if len(self.search_times[addr]) > self.SEARCH_TIMES_MAX_LEN:
                    self.search_times[addr] = self.search_times[addr][-self.SEARCH_TIMES_MAX_LEN:]
                
                return resp 
            except grpc.RpcError as e:
                print(f"Gateway: Falha ao ler de {addr}: {e.details()}. A tentar outro barrel (failover)...")
        
        print(f"Gateway: ERRO CRÍTICO! Todos os barrels estão indisponíveis.")
        return empty_response

    def searchWord(self, request, context):
        query = request.word.strip()
        page = request.page
        
        # Normalizar query para minúsculas (para contagem)
        # "Portugal" e "portugal" contam como a mesma pesquisa
        query_normalized = query.lower()
        
        # Contar pesquisa APENAS na primeira página (page == 0)
        # Isto garante que:
        # 1. Paginação não conta como nova pesquisa
        # 2. Pesquisas em cache são contadas (porque contamos ANTES de verificar cache)
        if query_normalized and page == 0:
            with self.search_queries_lock:
                self.search_queries[query_normalized] = self.search_queries.get(query_normalized, 0) + 1
                print(f"  [Gateway Stats] Pesquisa contada: '{query_normalized}' (total: {self.search_queries[query_normalized]})")
            # Notificar que houve mudança nas estatísticas (event-driven)
            self._notify_stats_changed()
        
        cache_key = (request.word, request.page, request.page_size)
        
        try:
            with self.cache_lock:
                cached_response = self.search_cache.get(cache_key)
            if cached_response:
                print(f"  [Gateway Cache] HIT: '{request.word}' (Pág {request.page})")
                return cached_response 
        except Exception as e:
            print(f"[Gateway Cache] ERRO (ignorado): {e}")

        print(f"  [Gateway Cache] MISS: '{request.word}' (Pág {request.page})")

        response = self._execute_read(
            lambda stub: stub.searchWord(request),
            index_pb2.SearchWordResponse(results=[], total_results=0, current_page=0, has_more=False)
        )
        
        if response and getattr(response, 'total_results', 0) > 0:
            try:
                with self.cache_lock:
                    self.search_cache[cache_key] = response
            except Exception as e:
                print(f"[Gateway Cache] ERRO ao guardar (ignorado): {e}")

        return response

    def searchListPages(self, request, context):
        cache_key = f"links_to:{request.url}" 
        
        try:
            with self.cache_lock:
                cached_response = self.search_cache.get(cache_key)
            if cached_response:
                print(f"  [Gateway Cache] HIT: (links para) '{request.url}'")
                return cached_response
        except Exception as e:
            print(f"[Gateway Cache] ERRO (ignorado): {e}")

        print(f"  [Gateway Cache] MISS: (links para) '{request.url}'")

        response = self._execute_read(
            lambda stub: stub.searchListPages(request),
            index_pb2.SearchListPagesResponse(urls=[])
        )
        
        if response and getattr(response, 'urls', []):
            try:
                with self.cache_lock:
                    self.search_cache[cache_key] = response
            except Exception as e:
                print(f"[Gateway Cache] ERRO ao guardar (ignorado): {e}")

        return response

    def getStatistics(self, request, context):
        all_barrel_infos = []

        with self.barrel_lock:
            stubs_snapshot = list(self.barrel_stubs.items())
        
        for addr, stub in stubs_snapshot:
            try:
                stats = stub.getStatistics(empty_pb2.Empty())
                
                times = self.search_times.get(addr, [])
                avg_response_time = (sum(times) / len(times)) if times else 0.0
                
                barrel_info = stats.barrels[0] 
                updated_barrel_info = index_pb2.BarrelInfo(
                    barrel_id=barrel_info.barrel_id,
                    indexed_words_count=barrel_info.indexed_words_count,
                    avg_response_time=avg_response_time
                )
                all_barrel_infos.append(updated_barrel_info)

            except grpc.RpcError:
                print(f"Gateway: Não foi possível obter estatísticas de {addr}.")
                all_barrel_infos.append(index_pb2.BarrelInfo(
                    barrel_id=f"Barrel-{addr.split(':')[-1]} (Offline)",
                    indexed_words_count=0,
                    avg_response_time=0.0
                ))
        
        # Usar contadores de pesquisa do Gateway (centralizados)
        with self.search_queries_lock:
            top_10 = sorted(self.search_queries.items(), key=lambda x: x[1], reverse=True)[:10]
        
        final_top_searches = [index_pb2.SearchStat(query=q, count=c) for q, c in top_10]
        
        return index_pb2.StatisticsResponse(
            top_searches=final_top_searches,
            barrels=all_barrel_infos
        )

    def _check_barrel_heartbeats(self):
        while not self.stop_event.is_set():
            self.stop_event.wait(self.BARREL_TIMEOUT_SECONDS / 2)
            
            with self.barrel_lock:
                now = time.time()
                to_remove = [addr for addr, last_seen in self.active_barrels.items() 
                             if now - last_seen > self.BARREL_TIMEOUT_SECONDS]
                
                for addr in to_remove:
                    print(f"\n[Gateway] Barrel {addr} timed out. A remover da lista ativa.")
                    del self.active_barrels[addr]
                    
                    if addr in self.barrel_stubs:
                        try:
                            self.barrel_channels[addr].close()
                        except Exception:
                            pass
                        del self.barrel_stubs[addr]
                        del self.barrel_channels[addr]
                        if addr in self.search_times:
                            del self.search_times[addr]
            
            # Notificar que houve mudança (barrel removido)
            if to_remove:
                self._notify_stats_changed()

    def RegisterBarrel(self, request, context):
        addr = request.barrel_address
        is_new_barrel = False
        
        with self.barrel_lock:
            print(f"\n[Gateway] Novo Barrel registado: {addr}")
            self.active_barrels[addr] = time.time()
            
            if addr not in self.barrel_stubs:
                channel = grpc.insecure_channel(addr)
                stub = index_pb2_grpc.IndexStub(channel)
                self.barrel_channels[addr] = channel
                self.barrel_stubs[addr] = stub
                self.search_times[addr] = []  # Inicializa o histórico de tempos
                is_new_barrel = True
        
        # Notificar que houve mudança (novo barrel)
        if is_new_barrel:
            self._notify_stats_changed()
        
        return empty_pb2.Empty()

    def SendHeartbeat(self, request, context):
        addr = request.barrel_address
        needs_registration = False
        
        with self.barrel_lock:
            if addr in self.active_barrels:
                self.active_barrels[addr] = time.time()
            else:
                needs_registration = True
        
        if needs_registration:
            return self.RegisterBarrel(request, context)

        return empty_pb2.Empty()

    def GetActiveBarrels(self, request, context):
        with self.barrel_lock:
            active_addrs = list(self.active_barrels.keys())
        return index_pb2.BarrelListResponse(addresses=active_addrs)
    
    def GetFullState(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('GetFullState deve ser chamado num Barrel, não no Gateway.')
        return index_pb2.FullStateResponse() 

    def close(self):
        print("Gateway a fechar canais para barrels...")
        with self.barrel_lock:
            for channel in self.barrel_channels.values():
                try:
                    channel.close()
                except Exception:
                    pass
        try:
            self.aof_file.close()
        except Exception as e:
            print(f"Erro ao fechar ficheiro AOF: {e}")

def serve(gateway, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    index_pb2_grpc.add_IndexServicer_to_server(gateway, server)
    server.add_insecure_port(f"0.0.0.0:{port}")
    server.start()
    print(f"Gateway gRPC (Modo Dinâmico) iniciado na porta {port}")
    return server

def main():

    gateway = Gateway()
    PORT = int(os.getenv('GATEWAY_PORT', '8183'))

    server = serve(gateway, PORT)

    print("GATEWAY - Gestor de Fila Central e Registo de Serviços (com Round-Robin)")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nEncerrando gateway...")
        gateway.stop_checkpoint_thread()
        print("A guardar estado final (Fila e Filtro de Bloom)...")
        gateway.save_state()
        gateway.close()
        server.stop(0)
        print("Gateway encerrado. Estado guardado.")

if __name__ == '__main__':
    main()