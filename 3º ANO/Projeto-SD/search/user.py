import grpc
import index_pb2
import index_pb2_grpc
import os
import time 
from pathlib import Path
from google.protobuf import empty_pb2
from dotenv import load_dotenv

# Carregar variáveis de ambiente da raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / '.env')

class UserInterface:
    
    MAX_RETRIES = 3 # Número de tentativas antes de desistir
    RETRY_BACKOFF_SECONDS = 2 # Tempo base de espera (aumenta a cada falha)

    def __init__(self):

        GATEWAY_HOST = os.getenv("GATEWAY_HOST", "localhost")
        GATEWAY_PORT = os.getenv("GATEWAY_PORT", "8183")
        self.gateway_addr = f"{GATEWAY_HOST}:{GATEWAY_PORT}"

        print(f"Interface de Utilizador a ligar ao Gateway em: {self.gateway_addr}")
    
        self.gateway_channel = None
        self.gateway_stub = None
        # CORREÇÃO: Faltava o 'self.' aqui
        self._reconnect_gateway()

    def _reconnect_gateway(self):
        """Fecha o canal antigo (se existir) e cria um novo canal e stub."""
        print(f"[Sistema] A ligar ao Gateway em {self.gateway_addr}...")
        
        if self.gateway_channel:
            try:
                self.gateway_channel.close()
            except Exception:
                pass # Ignora erros ao fechar canal antigo
        
        try:
            self.gateway_channel = grpc.insecure_channel(self.gateway_addr)
            self.gateway_stub = index_pb2_grpc.IndexStub(self.gateway_channel)
        
            self.gateway_channel.unary_unary(
                '/grpc.health.v1.Health/Check',
                request_serializer=lambda _: b'',
                response_deserializer=lambda _: None,
            ).future(None).result(timeout=1.0) # Envia um ping "falso"
            
            print(f"[Sistema] Ligação à Gateway estabelecida.")
            
        except Exception as e:
           
            if isinstance(e, (grpc.FutureTimeoutError, grpc.RpcError)):
                if isinstance(e, grpc.RpcError) and e.code() == grpc.StatusCode.UNIMPLEMENTED:
                    print(f"[Sistema] Ligação à Gateway (sem health check) estabelecida.")
                else:
                    print(f"[Sistema] Aviso: Gateway parece estar offline no arranque. {e}")
            else:
                 print(f"[Sistema] Aviso: Gateway parece estar offline no arranque. {e}")

            # Mesmo que o ping falhe, o canal e o stub são criados para a próxima tentativa
            if not self.gateway_channel:
                self.gateway_channel = grpc.insecure_channel(self.gateway_addr)
            if not self.gateway_stub:
                self.gateway_stub = index_pb2_grpc.IndexStub(self.gateway_channel)


    def _execute_with_retry(self, rpc_call):
        """
        Executa uma chamada gRPC com lógica de retry e reconexão.
        :param rpc_call: Uma função lambda que executa o stub gRPC (ex: lambda: self.gateway_stub.metodo(request))
        """
        retries = 0
        while retries < self.MAX_RETRIES:
            try:
                if self.gateway_stub is None:
                    # Se não temos stub, tenta reconectar primeiro
                    raise grpc.RpcError("Stub não inicializado", grpc.StatusCode.UNAVAILABLE)

                # Tenta executar a chamada
                return rpc_call()
            
            except grpc.RpcError as e:
                # A Gateway está indisponível?
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    print(f"\n[Aviso] Gateway indisponível. A tentar reconectar (Tentativa {retries + 1}/{self.MAX_RETRIES})...")
                    retries += 1
                    
                    # Espera antes de tentar reconectar
                    time.sleep(retries * self.RETRY_BACKOFF_SECONDS) 
                    
                    self._reconnect_gateway()
                
                else:
                    # Outro erro gRPC (ex: NOT_FOUND, INTERNAL), não tentar novamente.
                    print(f"Erro gRPC (não recuperável): {e.details()}")
                    return None # Retorna None para indicar falha
            
            except Exception as e:
                # Erro inesperado
                print(f"Erro inesperado no cliente: {e}")
                return None # Retorna None para indicar falha

        print(f"Erro: Falha ao ligar à Gateway após {self.MAX_RETRIES} tentativas.")
        return None

    def add_url(self, url):
        request = index_pb2.PutNewRequest(url=url)
        
        response = self._execute_with_retry(lambda: self.gateway_stub.putNew(request))
        
        if response is not None:
            print(f"URL '{url}' added successfully.")
        # Se response for None, o wrapper já imprimiu o erro.

    def search_word(self, word):
        page = 0
        page_size = 10
        
        while True:
            request = index_pb2.SearchWordRequest(word=word, page=page, page_size=page_size)
            
            response = self._execute_with_retry(lambda: self.gateway_stub.searchWord(request))

            if response is None:
                print(f"Erro ao contactar a Gateway. A voltar ao menu.")
                break # Sai do loop de paginação
            
            results = getattr(response, 'results', [])
            total_results = getattr(response, 'total_results', 0)
            has_more = getattr(response, 'has_more', False)
            
            if page == 0 and not results:
                print(f"\nNo results for '{word}'.")
                return
            
            if page == 0:
                print(f"\nSearch results for '{word}' (Total: {total_results}):")
               
            start_num = page * page_size + 1
            for idx, r in enumerate(results, start=start_num):
                title = r.title or "<sem título>"
                url = r.url or "<sem url>"
                citation = r.citation or ""
                
                print(f"\n[{idx}] {title}")
                print(f"    {url}")
                if citation:
                    print(f"    {citation}")
            
            
            if has_more:
                print(f"Mostrando {start_num}-{start_num + len(results) - 1} de {total_results}")
                choice = input("\nPressione ENTER para ver mais, 'q' para voltar ao menu: ").strip().lower()
                
                if choice == 'q':
                    break
                page += 1
            else:
                print(f"\n Fim dos resultados ({total_results} no total)")
                break

    def show_pages_linking_to(self, url):
        """Mostra todas as páginas que ligam para a URL especificada"""
        request = index_pb2.SearchListPagesRequest(url=url)
        
        # Executa a chamada através do wrapper
        response = self._execute_with_retry(lambda: self.gateway_stub.searchListPages(request))

        if response is None:
            print(f"Erro ao contactar a Gateway.")
            return # Sai da função

        urls = getattr(response, 'urls', [])
        if not urls:
            print(f"\nNenhuma página conhecida liga para '{url}'.")
            return
        
        print(f"\nPáginas que ligam para '{url}':")
        for i, linking_url in enumerate(urls, 1):
            print(f"{i}. {linking_url}")

    def show_statistics(self):
        """Mostra estatísticas do sistema"""
        request = empty_pb2.Empty()
        
        response = self._execute_with_retry(lambda: self.gateway_stub.getStatistics(request))

        if response is None:
            print(f"Erro ao contactar a Gateway.")
            return # Sai da função
                    
        try:
            print("\nTop 10 Pesquisas Mais Comuns:")
            top_searches = getattr(response, 'top_searches', [])
            if top_searches:
                for i, stat in enumerate(top_searches, 1):
                    query = getattr(stat, 'query', '')
                    count = getattr(stat, 'count', 0)
                    print(f"{i:2d}. '{query}' - {count} pesquisa(s)")
            else:
                print("   Nenhuma pesquisa realizada ainda.")
            
            print("\nBarrels Ativos:")
            barrels = getattr(response, 'barrels', [])
            if barrels:
                for barrel in barrels:
                    barrel_id = getattr(barrel, 'barrel_id', 'Unknown')
                    words_count = getattr(barrel, 'indexed_words_count', 0)
                    avg_time = getattr(barrel, 'avg_response_time', 0.0)
                    
                    print(f"\n   ID: {barrel_id}")
                    print(f"   Palavras Indexadas: {words_count}")
                    print(f"   Tempo Médio de Resposta: {avg_time:.4f}s")
            else:
                print("   Nenhum barrel ativo.")
                
        except Exception as e:
            print(f"Error displaying statistics: {e}")

    def display_menu(self):
        print("\nMenu:")
        print("1. Add URL")
        print("2. Search for a word")
        print("3. Show pages linking to a URL")
        print("4. Show statistics")
        print("5. Exit")

    def run(self):
        try:
            while True:
                self.display_menu()
                choice = input("Choose an option: ")

                if choice == '1':
                    url = input("Enter the URL to add: ")
                    self.add_url(url)
                elif choice == '2':
                    word = input("Enter the word to search: ")
                    self.search_word(word)
                elif choice == '3':
                    url = input("Enter the URL to check linking pages: ")
                    self.show_pages_linking_to(url)
                elif choice == '4':
                    self.show_statistics()
                elif choice == '5':
                    print("Exiting...")
                    break
                else:
                    print("Invalid choice. Please try again.")
        finally:
            try:
                if self.gateway_channel:
                    self.gateway_channel.close()
            except Exception:
                pass

if __name__ == '__main__':
    user_interface = UserInterface()
    user_interface.run()