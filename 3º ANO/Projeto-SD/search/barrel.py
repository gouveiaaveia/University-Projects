import grpc
from google.protobuf import empty_pb2
import index_pb2
import index_pb2_grpc
import queue
import threading 
import pickle  
import os      
import sys
import random
import argparse
import json
import heapq

from pathlib import Path
from concurrent import futures
from dotenv import load_dotenv

# Carregar variáveis de ambiente da raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / '.env')

class Barrel(index_pb2_grpc.IndexServicer):

    CHECKPOINT_INTERVAL_SECONDS = 20
    HEARTBEAT_INTERVAL_SECONDS = 10 
    MAX_MESSAGE_LENGTH = 100 * 1024 * 1024  
    
    SYNC_INDEX_CHUNK_SIZE = 5000 

    def __init__(self, port: int, gateway_host: str):

        self.port = port
        
        ADVERTISE_HOST = os.getenv("BARREL_ADVERTISE_HOST", "localhost")
        
        GATEWAY_HOST_FALLBACK = gateway_host.split(':')[0] if ':' in gateway_host else gateway_host
        GATEWAY_PORT_FALLBACK = gateway_host.split(':')[1] if ':' in gateway_host else "8183"

        GATEWAY_HOST = os.getenv("GATEWAY_HOST", GATEWAY_HOST_FALLBACK)
        GATEWAY_PORT = os.getenv("GATEWAY_PORT", GATEWAY_PORT_FALLBACK)
        
        self.address = f"{ADVERTISE_HOST}:{port}" 
        self.barrel_id = f"Barrel-{self.port}"
        self.STATE_FILE = f'barrel_state_{self.port}.pkl'
     
        self.AOF_FILE = f'barrel_aof_{self.port}.log'
        
        print(f"[{self.barrel_id}] A inicializar (Servidor ainda não iniciado)...")
        print(f"[{self.barrel_id}] A anunciar-se como: {self.address}")
        
        TARGET_ADDRESS = f"{GATEWAY_HOST}:{GATEWAY_PORT}"
        self.gateway_host = TARGET_ADDRESS

        try:
            self.gateway_channel = grpc.insecure_channel(TARGET_ADDRESS)
            self.gateway_stub = index_pb2_grpc.IndexStub(self.gateway_channel)
        except Exception as e:
            print(f"[{self.barrel_id}] ERRO CRÍTICO: Não foi possível criar canal para o Gateway: {e}")
            sys.exit(1)
        
        self.state_lock = threading.RLock()
        
        self.checkpoint_lock = threading.Lock() 
        self.aof_lock = threading.Lock()        
        self.sync_lock = threading.Lock()       
        self.is_syncing = True 

        try:
            self.aof_file = open(self.AOF_FILE, 'a')
        except Exception as e:
            print(f"[{self.barrel_id}] ERRO CRÍTICO: Não foi possível abrir o ficheiro AOF: {e}")
            sys.exit(1)

        self.initialize_empty_state()
        
        self.urlsToIndex = queue.Queue() 
        self.stop_event = threading.Event()
        
    
    def start_background_tasks(self):
        
        print(f"[{self.barrel_id}] Servidor está no ar. A iniciar tarefas de background...")

        self.load_state()
        self.load_aof()
        
        if self._is_state_empty():
            print(f"[{self.barrel_id}] Estado local vazio. A tentar sincronizar de um peer...")
            self.sync_state_from_peer()
        else:
            print(f"[{self.barrel_id}] Estado local carregado. A ficar operacional.")
            with self.sync_lock:
                self.is_syncing = False
        
        print(f"[{self.barrel_id}] A iniciar thread de checkpointing...")
        self.checkpoint_thread = threading.Thread(
            target=self._checkpoint_loop, 
            daemon=True 
        )
        self.checkpoint_thread.start()
        
        print(f"[{self.barrel_id}] A iniciar thread de heartbeat/registo para {self.gateway_host}...")
        self.heartbeat_thread = threading.Thread(
            target=self._send_heartbeats, 
            daemon=True
        )
        self.heartbeat_thread.start()

    def _is_state_empty(self):
        """Verifica se o estado em memória está vazio."""
        with self.state_lock:
            return (len(self.url_para_docid) == 0 and 
                    len(self.word_para_wordid) == 0 and 
                    len(self.indice_otimizado) == 0)
        
    
    def sync_state_from_peer(self):
        """Tenta copiar o estado de um peer. Se falhar, termina o processo."""
        print(f"[{self.barrel_id}] A pedir lista de Barrels ao Gateway {self.gateway_host}...")
        try:
            response = self.gateway_stub.GetActiveBarrels(empty_pb2.Empty())
            peer_addresses = [addr for addr in response.addresses if addr != self.address]
            
            if not peer_addresses:
                print(f"[{self.barrel_id}] Nenhum outro Barrel encontrado. A iniciar como primeiro Barrel.")
                with self.sync_lock:
                    self.is_syncing = False
                print(f"[{self.barrel_id}] Estado vazio. Barrel está OPERACIONAL.")
                return

            random.shuffle(peer_addresses)
            for addr in peer_addresses:
                peer_channel = None
                try:
                    print(f"[{self.barrel_id}] A tentar sincronizar estado de {addr}...")
                    peer_channel = grpc.insecure_channel(
                        addr,
                        options=[
                            ('grpc.max_send_message_length', self.MAX_MESSAGE_LENGTH),
                            ('grpc.max_receive_message_length', self.MAX_MESSAGE_LENGTH),
                        ]
                    )
                    peer_stub = index_pb2_grpc.IndexStub(peer_channel)
                    
                    self.initialize_empty_state()
                
                    stream = peer_stub.GetFullState(empty_pb2.Empty(), timeout=300) 
                    
                    with self.state_lock:
                        for chunk in stream:
                            data = pickle.loads(chunk.chunk_data)
                            
                            if chunk.type == index_pb2.StateChunk.DOC_INFO:
                                self.docid_para_info = data
                            elif chunk.type == index_pb2.StateChunk.URL_TO_DOCID:
                                self.url_para_docid = data
                            elif chunk.type == index_pb2.StateChunk.WORD_TO_WORDID:
                                self.word_para_wordid = data
                            elif chunk.type == index_pb2.StateChunk.WORDID_TO_WORD:
                                self.wordid_para_word = data
                            elif chunk.type == index_pb2.StateChunk.LINKS_TO_DOCID:
                                self.links_to_docid = data
                            elif chunk.type == index_pb2.StateChunk.SEARCH_QUERIES:
                                self.search_queries = data
                            elif chunk.type == index_pb2.StateChunk.COUNTERS:
                                self.doc_id_counter = data['doc']
                                self.word_id_counter = data['word']
                            elif chunk.type == index_pb2.StateChunk.INDEX_CHUNK:
                                self.indice_otimizado.update(data) 
                    
                    print(f"[{self.barrel_id}] Estado sincronizado com sucesso de {addr}.")
                    peer_channel.close()
                    self.save_state() 
                    
                    with self.sync_lock:
                        self.is_syncing = False
                    print(f"[{self.barrel_id}] Sincronização concluída. Barrel está OPERACIONAL.")
                    return # SUCESSO
                
                except Exception as e:
                    print(f"[{self.barrel_id}] Falha ao sincronizar de {addr}: {e}")
                    if peer_channel:
                        peer_channel.close()
            
            print(f"[{self.barrel_id}] ERRO CRÍTICO: Falha ao sincronizar de todos os peers.")
            print(f"[{self.barrel_id}] O Barrel não pode ficar online em estado inconsistente. A encerrar.")
            sys.exit(1) # Termina o processo

        except grpc.RpcError as e:
            print(f"[{self.barrel_id}] Erro ao contactar Gateway para sync: {e.details()}. A iniciar com estado vazio.")
            with self.sync_lock:
                self.is_syncing = False
            print(f"[{self.barrel_id}] Estado vazio. Barrel está OPERACIONAL.")

    def _send_heartbeats(self):
        while not self.stop_event.is_set():
            try:
                self.gateway_stub.SendHeartbeat(
                    index_pb2.HeartbeatRequest(barrel_address=self.address)
                )
            except grpc.RpcError as e:
                print(f"[{self.barrel_id}] Aviso: Falha no envio do heartbeat/registo: {e.details()}")
            
            self.stop_event.wait(self.HEARTBEAT_INTERVAL_SECONDS)

    def GetFullState(self, request, context):
        """Um novo peer chama este método para obter o estado completo (via stream)."""
        print(f"[{self.barrel_id}] A servir estado completo para um novo peer (stream)...")
        
        copies = {}

        try:
            with self.state_lock: 
                print(f"[{self.barrel_id}] GetFullState: Lock adquirido, a criar snapshot...")
                copies['docid_para_info'] = self.docid_para_info.copy()
                copies['url_para_docid'] = self.url_para_docid.copy()
                copies['counters'] = {'doc': self.doc_id_counter, 'word': self.word_id_counter}
                copies['word_para_wordid'] = self.word_para_wordid.copy()
                copies['wordid_para_word'] = self.wordid_para_word.copy()
                copies['search_queries'] = self.search_queries.copy()
                copies['links_to_docid'] = self.links_to_docid.copy()
                copies['indice_otimizado_items'] = list(self.indice_otimizado.items())
            
            print(f"[{self.barrel_id}] GetFullState: Snapshot criado, lock libertado. A iniciar stream...")

            # 2. Enviar os dados copiados (sem lock)
            yield index_pb2.StateChunk(type=index_pb2.StateChunk.DOC_INFO, chunk_data=pickle.dumps(copies['docid_para_info']))
            yield index_pb2.StateChunk(type=index_pb2.StateChunk.URL_TO_DOCID, chunk_data=pickle.dumps(copies['url_para_docid']))
            yield index_pb2.StateChunk(type=index_pb2.StateChunk.WORD_TO_WORDID, chunk_data=pickle.dumps(copies['word_para_wordid']))
            yield index_pb2.StateChunk(type=index_pb2.StateChunk.WORDID_TO_WORD, chunk_data=pickle.dumps(copies['wordid_para_word']))
            yield index_pb2.StateChunk(type=index_pb2.StateChunk.LINKS_TO_DOCID, chunk_data=pickle.dumps(copies['links_to_docid']))
            yield index_pb2.StateChunk(type=index_pb2.StateChunk.SEARCH_QUERIES, chunk_data=pickle.dumps(copies['search_queries']))
            yield index_pb2.StateChunk(type=index_pb2.StateChunk.COUNTERS, chunk_data=pickle.dumps(copies['counters']))
            
            indice_items = copies['indice_otimizado_items']
            print(f"[{self.barrel_id}] A enviar índice ({len(indice_items)} palavras) em chunks...")
            temp_index_chunk = {}
            for i, (word_id, doc_set) in enumerate(indice_items):
                temp_index_chunk[word_id] = doc_set
                if (i + 1) % self.SYNC_INDEX_CHUNK_SIZE == 0:
                    yield index_pb2.StateChunk(type=index_pb2.StateChunk.INDEX_CHUNK, chunk_data=pickle.dumps(temp_index_chunk))
                    temp_index_chunk = {}
            
            if temp_index_chunk: 
                yield index_pb2.StateChunk(type=index_pb2.StateChunk.INDEX_CHUNK, chunk_data=pickle.dumps(temp_index_chunk))
            
            print(f"[{self.barrel_id}] Envio de estado concluído.")

        except Exception as e:
            # Se o cliente (receiver) desligar a meio, pode dar 'BrokenPipeError'
            print(f"[{self.barrel_id}] Erro ao enviar estado (stream): {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Erro ao enviar estado: {e}")

    # --- Lógica de Checkpointing ---
    def _checkpoint_loop(self):
        while not self.stop_event.wait(self.CHECKPOINT_INTERVAL_SECONDS):
            print(f"\n[{self.barrel_id} | Checkpoint] A guardar estado automático em background...")
            self.save_state()
            print(f"[{self.barrel_id} | Checkpoint] Estado guardado.")
        
        print(f"[{self.barrel_id} | Checkpoint] Thread de checkpoint a encerrar.")

    def stop_checkpoint_thread(self):
        print(f"[{self.barrel_id}] A parar a thread de checkpoint...")
        self.stop_event.set()
        if hasattr(self, 'checkpoint_thread') and self.checkpoint_thread.is_alive():
            self.checkpoint_thread.join() 
        if hasattr(self, 'heartbeat_thread') and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join()
        print(f"[{self.barrel_id}] Threads de background paradas.")

    def load_aof(self):
        print(f"[{self.barrel_id}] A carregar operações não guardadas do AOF ('{self.AOF_FILE}')...")
        idx_count = 0
        lnk_count = 0
        try:
            with open(self.AOF_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                        
                    parts = line.split(' ', 1)
                    if len(parts) != 2:
                        continue
                    
                    op, data_json = parts
                    data_dict = json.loads(data_json)
                    
                    if op == "IDX":
                        req = index_pb2.IndexRequest(
                            url=data_dict.get('url'),
                            title=data_dict.get('title'),
                            citation=data_dict.get('citation'),
                            words=data_dict.get('words', [])
                        )
                        self._internal_apply_index_data(req)
                        idx_count += 1
                    
                    elif op == "LNK":
                        req = index_pb2.AddLinksRequest(
                            source_url=data_dict.get('source_url'),
                            target_links=data_dict.get('target_links', [])
                        )
                        self._internal_apply_links_data(req)
                        lnk_count += 1
                        
        except FileNotFoundError:
            print(f"[{self.barrel_id}] Ficheiro AOF não encontrado (normal na primeira execução).")
        except Exception as e:
            print(f"[{self.barrel_id}] ERRO CRÍTICO ao carregar AOF: {e}. O estado pode estar incompleto.")
        
        print(f"[{self.barrel_id}] Recuperação AOF concluída: {idx_count} Index, {lnk_count} Links.")

    def load_state(self):
        if not os.path.exists(self.STATE_FILE):
            print(f"[{self.barrel_id}] Ficheiro de estado '{self.STATE_FILE}' não encontrado. A iniciar com estado vazio.")
            return

        try:
            with self.checkpoint_lock: 
                with open(self.STATE_FILE, 'rb') as f:
                    state = pickle.load(f)
                
            with self.state_lock:
                self.indice_otimizado = state['indice_otimizado']
                self.docid_para_info  = state['docid_para_info']
                self.url_para_docid   = state['url_para_docid']
                self.word_para_wordid = state['word_para_wordid']
                self.wordid_para_word = state['wordid_para_word']
                self.links_to_docid   = state['links_to_docid']
                self.doc_id_counter   = state['doc_id_counter']
                self.word_id_counter  = state['word_id_counter']
                self.search_queries   = state['search_queries']
            
            print(f"[{self.barrel_id}] Estado carregado com sucesso de '{self.STATE_FILE}'.")
            print(f"  - {len(self.url_para_docid)} URLs processados.")
            print(f"  - {len(self.word_para_wordid)} palavras únicas no índice.")

        except Exception as e:
            print(f"[{self.barrel_id}] Erro ao carregar o estado de '{self.STATE_FILE}': {e}")
            print(f"[{self.barrel_id}] A iniciar com estado vazio para segurança.")
            self.initialize_empty_state()

    def save_state(self):
        """Guarda o estado 'pickle' e limpa o AOF."""
        
        # A cópia (lenta) acontece DENTRO do checkpoint_lock E do state_lock
        # Isto é necessário para um snapshot atómico.
        # É a causa do "congelamento" temporário, mas é o preço da consistência.
        with self.checkpoint_lock:
            state_copy = {}
            try:
                with self.state_lock:
                    state_copy = {
                        'indice_otimizado': self.indice_otimizado.copy(),
                        'docid_para_info': self.docid_para_info.copy(),
                        'url_para_docid': self.url_para_docid.copy(),
                        'word_para_wordid': self.word_para_wordid.copy(),
                        'wordid_para_word': self.wordid_para_word.copy(),
                        'links_to_docid': self.links_to_docid.copy(),
                        'doc_id_counter': self.doc_id_counter,
                        'word_id_counter': self.word_id_counter,
                        'search_queries': self.search_queries.copy()
                    }
            except Exception as e:
                print(f"[{self.barrel_id}] ERRO CRÍTICO ao *copiar* estado para guardar: {e}")
                return 

            try:
                temp_file = self.STATE_FILE + '.tmp'
                with open(temp_file, 'wb') as f:
                    pickle.dump(state_copy, f, pickle.HIGHEST_PROTOCOL)
                
                os.replace(temp_file, self.STATE_FILE)

            except Exception as e:
                print(f"\n[{self.barrel_id}] ERRO CRÍTICO ao *escrever* o estado no disco: {e}")
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception:
                    pass
                return 

        try:
            with self.aof_lock:
                self.aof_file.truncate(0)
        except Exception as e:
            print(f"\n[{self.barrel_id}] ERRO CRÍTICO ao limpar o AOF: {e}")

    def initialize_empty_state(self):
        """Define todas as estruturas de dados como vazias."""
        with self.state_lock:
            self.indice_otimizado = {}
            self.docid_para_info = {}
            self.url_para_docid = {}
            self.word_para_wordid = {}
            self.wordid_para_word = {}
            self.links_to_docid = {}
            self.doc_id_counter = 1
            self.word_id_counter = 1
            self.search_queries = {}
   
    def get_or_create_doc_id(self, url: str) -> int:
        with self.state_lock:
            doc_id = self.url_para_docid.get(url)
            if doc_id:
                return doc_id
            
            new_id = self.doc_id_counter
            self.doc_id_counter += 1
            self.url_para_docid[url] = new_id
            self.docid_para_info[new_id] = {'url': url, 'title': 'Sem título', 'citation': ''}
            return new_id

    def get_or_create_word_id(self, word: str) -> int:
        with self.state_lock:
            word_id = self.word_para_wordid.get(word)
            if word_id:
                return word_id

            new_id = self.word_id_counter
            self.word_id_counter += 1
            self.word_para_wordid[word] = new_id
            self.wordid_para_word[new_id] = word
            return new_id

    def _write_aof_atomic(self, operation: str, data_dict: dict) -> bool:

        try:
            with self.aof_lock:
                self.aof_file.write(f"{operation} {json.dumps(data_dict)}\n")
                self.aof_file.flush()
                os.fsync(self.aof_file.fileno())
            return True
        except Exception as e:
            print(f"[{self.barrel_id}] ERRO CRÍTICO AOF ({operation}): {e}")
            return False

    def _internal_apply_index_data(self, request):
        """Aplica os dados de indexação (lógica interna)."""
        try:
            with self.state_lock:
                url = request.url
                doc_id = self.get_or_create_doc_id(url) 
                
                self.docid_para_info[doc_id] = {
                    'url': url,
                    'title': request.title,
                    'citation': request.citation
                }
                
                for word in request.words:
                    word_id = self.get_or_create_word_id(word) 
                    if word_id not in self.indice_otimizado:
                        self.indice_otimizado[word_id] = set()
                    self.indice_otimizado[word_id].add(doc_id)
                
            return index_pb2.IndexWordsResponse(count=len(request.words))
        except Exception as e:
            print(f"[{self.barrel_id}] ERRO CRÍTICO em _internal_apply_index_data: {e}")
            return index_pb2.IndexWordsResponse(count=0)


    def IndexPageData(self, request, context):
        
        with self.sync_lock:
            if self.is_syncing:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Barrel is initializing/syncing state. Please retry.")
                return index_pb2.IndexWordsResponse()
        
        req_dict = {
            'url': request.url,
            'title': request.title,
            'citation': request.citation,
            'words': list(request.words)
        }
        if not self._write_aof_atomic("IDX", req_dict):
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Erro AOF: Falha ao persistir a operação.")
            return index_pb2.IndexWordsResponse()
        
        return self._internal_apply_index_data(request)

    def _internal_apply_links_data(self, request):

        try:
            with self.state_lock:
                source_doc_id = self.get_or_create_doc_id(request.source_url)
                
                for target_link in request.target_links:
                    target_doc_id = self.get_or_create_doc_id(target_link)
                    if target_doc_id not in self.links_to_docid:
                        self.links_to_docid[target_doc_id] = set()
                    self.links_to_docid[target_doc_id].add(source_doc_id)
        except Exception as e:
            print(f"[{self.barrel_id}] Erro em _internal_apply_links_data (ID): {e}")
        return empty_pb2.Empty()

    def AddPageLinks(self, request, context):
        """NOVO RPC: Recebe um batch de links do Downloader."""
        
        with self.sync_lock:
            if self.is_syncing:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("Barrel is initializing/syncing state. Please retry.")
                return empty_pb2.Empty()

        req_dict = {
            'source_url': request.source_url,
            'target_links': list(request.target_links)
        }
        if not self._write_aof_atomic("LNK", req_dict):
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Erro AOF: Falha ao persistir a operação.")
            return empty_pb2.Empty()
        
        return self._internal_apply_links_data(request)

    def searchWord(self, request, context):
        query = request.word.strip()
        page = max(0, request.page) if request.page else 0
        page_size = request.page_size if request.page_size > 0 else 10
        
        word_ids = []
        common_doc_ids = None
        total_results = 0
        
        with self.state_lock:
            # NOTA: A contagem de pesquisas é feita no Gateway (centralizada)
            # para evitar problemas com cache e paginação
        
            for word in query.split():
                cleaned = word.lower().strip() 
                if cleaned and len(cleaned) > 2:
                    word_id = self.word_para_wordid.get(cleaned) 
                    if word_id:
                        word_ids.append(word_id)
                    else:
                        word_ids = [] 
                        break 
            
            if not word_ids:
                return index_pb2.SearchWordResponse(
                    results=[], total_results=0, current_page=page, has_more=False
                )
            
            for word_id in word_ids:
                doc_id_set = self.indice_otimizado.get(word_id, set()) 
                if common_doc_ids is None:
                    common_doc_ids = doc_id_set.copy() 
                else:
                    common_doc_ids.intersection_update(doc_id_set)
                if not common_doc_ids:
                    break
        
        if common_doc_ids is None:
            common_doc_ids = set()
        
        total_results = len(common_doc_ids)
        start_idx = page * page_size
        end_idx = start_idx + page_size
        has_more = end_idx < total_results

        # Ordenar TODOS os resultados por relevância (número de inbound links)
        # e depois fazer slice para a página pedida
        with self.state_lock:
            # Criar lista de (inbound_count, doc_id) para todos os documentos
            scored_docs = []
            for doc_id in common_doc_ids:
                inbound_count = len(self.links_to_docid.get(doc_id, set()))
                scored_docs.append((inbound_count, doc_id))
            
            # Ordenar por inbound_count decrescente, depois por doc_id crescente (desempate)
            scored_docs.sort(key=lambda x: (-x[0], x[1]))
            
            # Extrair apenas a página pedida
            page_docs = scored_docs[start_idx:end_idx]
            
            results = []
            for inbound_count, doc_id in page_docs:
                info = self.docid_para_info.get(doc_id) 
                if not info:
                    info = {'title': 'Erro: Info não encontrada', 'url': f'DocID: {doc_id}', 'citation': ''}

                result = index_pb2.SearchResult(
                    title=info.get('title', 'Sem título'),
                    url=info.get('url', '<sem url>'),
                    citation=info.get('citation', '')
                )
                results.append(result)
        
        return index_pb2.SearchWordResponse(
            results=results,
            total_results=total_results,
            current_page=page,
            has_more=has_more
        )

    def searchListPages(self, request, context):
        linking_urls = []
        
        with self.state_lock:
            url = request.url
            doc_id = self.url_para_docid.get(url)
            if not doc_id:
                return index_pb2.SearchListPagesResponse(urls=[])
            
            linking_doc_ids = self.links_to_docid.get(doc_id, set()).copy()
            
            for linker_id in linking_doc_ids:
                info = self.docid_para_info.get(linker_id)
                if info and info.get('url'):
                    linking_urls.append(info['url'])
        
        return index_pb2.SearchListPagesResponse(urls=sorted(linking_urls))

    def getStatistics(self, request, context):
        with self.state_lock: 
            top_10 = sorted(self.search_queries.items(), key=lambda x: x[1], reverse=True)[:10]
            indexed_words_count = len(self.word_para_wordid)
        
        top_searches = [index_pb2.SearchStat(query=q, count=c) for q, c in top_10]
        
        barrel_info = index_pb2.BarrelInfo(
            barrel_id=self.barrel_id,
            indexed_words_count=indexed_words_count,
            avg_response_time=0.0
        )
        
        return index_pb2.StatisticsResponse(
            top_searches=top_searches,
            barrels=[barrel_info]
        )
    
    # --- Métodos de Fila (Proibidos) ---
    def takeNext(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Método de Fila. Chame o Gateway.')
        return index_pb2.TakeNextResponse()
    
    def putNew(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Método de Fila. Chame o Gateway.')
        return empty_pb2.Empty()

    def close(self):
        try:
            if hasattr(self, 'gateway_channel') and self.gateway_channel:
                self.gateway_channel.close()
        except Exception:
            pass
        try:
            self.aof_file.close()
        except Exception as e:
            print(f"[{self.barrel_id}] Erro ao fechar ficheiro AOF: {e}")
        
def serve(barrel, port):
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[ 
            ('grpc.max_send_message_length', Barrel.MAX_MESSAGE_LENGTH),
            ('grpc.max_receive_message_length', Barrel.MAX_MESSAGE_LENGTH),
        ]
    )
    index_pb2_grpc.add_IndexServicer_to_server(barrel, server)
    server.add_insecure_port(f"0.0.0.0:{port}")
    server.start()
    print(f"[{barrel.barrel_id}] Servidor gRPC iniciado na porta {port}")
    return server

def main():
    
    parser = argparse.ArgumentParser(description="Barrel do Motor de Pesquisa")
    parser.add_argument('port', type=int, help='Porta para este Barrel (ex: 8184)')
    
    DEFAULT_GW_HOST = os.getenv("GATEWAY_HOST", "localhost")
    DEFAULT_GW_PORT = os.getenv("GATEWAY_PORT", "8183")
    DEFAULT_GW_ADDR = f"{DEFAULT_GW_HOST}:{DEFAULT_GW_PORT}"
    
    parser.add_argument('--gateway_host', type=str, default=DEFAULT_GW_ADDR,
                        help='Endereço (host:porta) do Gateway gRPC')
    args = parser.parse_args()

    try:
        port = args.port
        if not (1024 <= port <= 65535):
            raise ValueError("A porta deve estar entre 1024 e 65535")
    except ValueError as e:
        print(f"Erro: Porta inválida '{port}'. {e}")
        sys.exit(1)

    barrel = Barrel(port=port, gateway_host=args.gateway_host)
    server = serve(barrel, port)
    
    barrel.start_background_tasks()
    
    print(f"BARREL ({barrel.barrel_id}) - (Modo Dinâmico, Sync, Persistência)")
    
    barrel_instance = barrel
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        barrel_id_str = getattr(barrel_instance, 'barrel_id', 'Barrel')
        print(f"\n[{barrel_id_str}] Encerrando barrel (Ctrl+C)...")
        
        barrel_instance.stop_checkpoint_thread()
        
        print(f"[{barrel_id_str}] A guardar o estado final...")
        barrel_instance.save_state()
        
        barrel_instance.close() 
        server.stop(0)
        print(f"[{barrel_id_str}] Servidor encerrado. Estado guardado.")

if __name__ == '__main__':
    main()