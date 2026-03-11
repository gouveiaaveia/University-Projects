import grpc
from google.protobuf import empty_pb2
import index_pb2
import index_pb2_grpc
import requests
from bs4 import BeautifulSoup as jsoup
from urllib.parse import urljoin
import re
import os
import time
import argparse 
import threading 
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente da raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / '.env')

class Downloader:
    
    DISCOVERY_INTERVAL_SECONDS = 15
    
    INITIAL_BACKOFF_SECONDS = 1
    MAX_BACKOFF_SECONDS = 60

    def __init__(self, gateway_host: str):
        
        print(f"A conectar ao Gateway: {gateway_host}")
        self.gateway_channel = grpc.insecure_channel(gateway_host)
        self.gateway_stub = index_pb2_grpc.IndexStub(self.gateway_channel)

        print("Downloader em modo dinâmico. A descobrir Barrels...")
        
        self.stubs_lock = threading.Lock() 
        self.barrel_channels = {} 
        self.barrel_stubs = {}    
        
        self.processed_count = 0
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.stop_event = threading.Event()
        self.discovery_thread = threading.Thread(
            target=self._discover_barrels, 
            daemon=True
        )
        self.discovery_thread.start()

    def _discover_barrels(self):
        """(Sem alterações)"""
        while not self.stop_event.is_set():
            try:
                response = self.gateway_stub.GetActiveBarrels(empty_pb2.Empty())
                active_addrs = set(response.addresses)
                
                with self.stubs_lock:
                    current_addrs = set(self.barrel_stubs.keys())
                    
                    to_add = active_addrs - current_addrs
                    for addr in to_add:
                        print(f"\n[Downloader Discovery] Descobriu novo Barrel: {addr}")
                        channel = grpc.insecure_channel(addr)
                        stub = index_pb2_grpc.IndexStub(channel)
                        self.barrel_channels[addr] = channel
                        self.barrel_stubs[addr] = stub
                        
                    to_remove = current_addrs - active_addrs
                    for addr in to_remove:
                        print(f"\n[Downloader Discovery] Perdeu contacto com Barrel: {addr}")
                        try:
                            self.barrel_channels[addr].close()
                        except Exception:
                            pass
                        del self.barrel_channels[addr]
                        del self.barrel_stubs[addr]
                        
            except grpc.RpcError as e:
                print(f"\n[Downloader Discovery] Falha ao descobrir Barrels: {e.details()}")
            
            self.stop_event.wait(self.DISCOVERY_INTERVAL_SECONDS)

    def _multicast_write(self, rpc_call_function, request_description: str):
    
        with self.stubs_lock:
            stubs_snapshot = dict(self.barrel_stubs)
        
        if not stubs_snapshot:
            print(f"  [Downloader Multicast] Aviso: Nenhum Barrel ativo para '{request_description}'.")
            return empty_pb2.Empty()

        stubs_to_process = stubs_snapshot
        first_response = None
        current_backoff = self.INITIAL_BACKOFF_SECONDS
        
        while stubs_to_process and current_backoff <= self.MAX_BACKOFF_SECONDS:
            failed_stubs = {} 

            for addr, stub in stubs_to_process.items():
                try:
                    response = rpc_call_function(stub)
                    if first_response is None:
                        first_response = response
                    
                except grpc.RpcError as e:
                    # Se o barrel foi removido (pela thread de discovery), não tentar mais
                    with self.stubs_lock:
                        if addr not in self.barrel_stubs:
                            print(f"  [Downloader Multicast] Barrel {addr} removido da lista. A desistir permanentemente.")
                            continue
                    
                    if e.code() == grpc.StatusCode.UNAVAILABLE:
                        if "syncing" in e.details():
                             print(f"  [Downloader Multicast] Barrel {addr} está a sincronizar. A tentar novamente (em {current_backoff}s)...")
                        else:
                             print(f"  [Downloader Multicast] Barrel {addr} indisponível. A tentar novamente (em {current_backoff}s)...")
                    else:
                        print(f"  [Downloader Multicast] Falha em {addr}: {e.details()}. A tentar novamente (em {current_backoff}s)...")

                    failed_stubs[addr] = stub
            
            stubs_to_process = failed_stubs
            
            if stubs_to_process:
                print(f"  [Downloader Multicast] {len(stubs_to_process)} barrels falharam. A tentar novamente em {current_backoff}s...")
                self.stop_event.wait(current_backoff) 
                current_backoff *= 2 # Exponential backoff
        
        if stubs_to_process:
            print(f"  [Downloader Multicast] ERRO: Desistiu de {len(stubs_to_process)} barrels após exceder backoff máximo para '{request_description}'.")

        return first_response if first_response else empty_pb2.Empty()

    def _clean_word(self, word):

        word = re.sub(r'[^\w\s]', '', word)
        return word.lower().strip()

    def _extract_metadata(self, soup):

        try:
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "Sem título"
            
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            text = ' '.join(text.split()) 
            citation = text[:150] + "..." if len(text) > 150 else text
            
            return title, citation
        except Exception as e:
            print(f"  Erro ao extrair metadados: {e}")
            return "Sem título", ""

    def _extract_words(self, soup):
        """
        Extrai palavras únicas de uma página HTML.
        Remove scripts, estilos e palavras curtas.
        """
        try:
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            words = text.split()
            unique_words = set()
            
            for word in words:
                cleaned_word = self._clean_word(word)
                if cleaned_word and len(cleaned_word) > 2:
                    unique_words.add(cleaned_word)
                    
            return list(unique_words)
        except Exception as e:
            print(f"  Erro ao extrair palavras: {e}")
            return []

    def _extract_links(self, base_url, soup):

        links = soup.select("a[href]")
        
        target_links_for_barrel = []
        new_urls_for_gateway = []
        
        for link in links:
            href = link.get('href')
            if href:
                try:
                    absolute_url = urljoin(base_url, href)
                    
                    if not (absolute_url.startswith('http://') or absolute_url.startswith('https://')):
                        continue
                    
                    target_links_for_barrel.append(absolute_url)
                    new_urls_for_gateway.append(absolute_url)
                    
                except Exception as e:
                    print(f"  Erro ao processar link '{href}': {e}")
        
        return target_links_for_barrel, new_urls_for_gateway


    def _try_get(self, url, timeout=10):
        """Tenta obter a página com variações de headers/session para contornar 403 simples."""
        session = requests.Session()
        session.headers.update(self.headers)

        # Variações de headers para tentar contornar bloqueios simples
        header_variants = [
            self.headers,
            {**self.headers, "Referer": url},
            {**self.headers, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
            {**self.headers, "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
        ]

        last_exc = None
        for hdrs in header_variants:
            try:
                resp = session.get(url, headers=hdrs, timeout=timeout, allow_redirects=True)
                resp.raise_for_status()
                return resp
            except requests.HTTPError as e:
                last_exc = e
                # se for 403, tenta próximo variant; para outros códigos, não insiste tanto
                if resp is not None and resp.status_code == 403:
                    continue
                else:
                    raise
            except requests.RequestException as e:
                last_exc = e
                # tentar próximo variant para falhas transitórias
                continue

        # se todas as tentativas falharam, relança último erro
        if last_exc:
            raise last_exc
        raise requests.RequestException("Falha desconhecida ao obter URL")

    def fetch_and_process_url(self, url):
        try:
            self.processed_count += 1
            print(f"\n[{self.processed_count}] Processando: {url}")
            
            # usa o novo _try_get que tenta contornar 403 simples
            response = self._try_get(url)
            
            soup = jsoup(response.text, 'html.parser')
            
            title, citation = self._extract_metadata(soup)
            words = self._extract_words(soup)
            
            soup_for_links = jsoup(response.text, 'html.parser')
            target_links, new_urls_for_gateway = self._extract_links(url, soup_for_links)

            index_req = index_pb2.IndexRequest(
                url=url,
                title=title,
                citation=citation,
                words=words
            )
            index_response = self._multicast_write(
                lambda stub: stub.IndexPageData(index_req),
                f"IndexPageData({url})"
            )
            
            words_count = 0
            try:
                words_count = getattr(index_response, 'count', 0)
            except Exception:
                words_count = 0

            if target_links:
                links_req = index_pb2.AddLinksRequest(
                    source_url=url,
                    target_links=target_links
                )
                self._multicast_write(
                    lambda stub: stub.AddPageLinks(links_req),
                    f"AddPageLinks({url})"
                )

            print(f"  Palavras extraídas: {words_count}")
            print(f"  Links extraídos: {len(target_links)}")

            if new_urls_for_gateway:
                print(f"  A submeter {len(new_urls_for_gateway)} novos URLs para a Gateway...")
                for new_url in new_urls_for_gateway:
                    try:
                        self.gateway_stub.putNew(index_pb2.PutNewRequest(url=new_url))
                    except grpc.RpcError as e:
                        print(f"    Erro ao submeter {new_url}: {e.details()}")
            
            try:
                self.gateway_stub.AcknowledgeUrl(index_pb2.AcknowledgeUrlRequest(url=url))
                print(f"  ACK enviado para Gateway: {url}")
            except grpc.RpcError as e:
                print(f"  ERRO CRÍTICO: Falha ao enviar ACK para {url}: {e.details()}")
            
            return True
            
        except requests.RequestException as e:
            print(f"  Erro ao descarregar URL: {e}")
            return False 
        except Exception as e:
            print(f"  Erro inesperado: {e}")
            return False 

    def run(self):
        print("Aguardando URLs da fila do Gateway...")
        print("Pressione Ctrl+C para parar.\n")
        try:
            while True:
                try:
                    response = self.gateway_stub.takeNext(empty_pb2.Empty())
                    url = response.url
                    
                    if not url:
                        time.sleep(2)
                        continue
                    
                    self.fetch_and_process_url(url)
                    
                except grpc.RpcError as e:
                    if e.code() == grpc.StatusCode.UNAVAILABLE:
                        print(f"Gateway indisponível. A tentar reconectar...")
                    else:
                        print(f"Erro RPC (Gateway?): {e.code()} - {e.details()}")
                    time.sleep(3)
                    
        except KeyboardInterrupt:
            print(f"\nDownloader encerrado. Total de URLs processados: {self.processed_count}")
        finally:
            self.close()
        
    def close(self):
        self.stop_event.set()
        try:
            self.gateway_channel.close()
        except Exception:
            pass
        
        print("Downloader a fechar canais para barrels...")
        with self.stubs_lock:
            for channel in self.barrel_channels.values():
                try:
                    channel.close()
                except Exception:
                    pass

def main():

    parser = argparse.ArgumentParser(description="Downloader do Motor de Pesquisa (Modo Dinâmico)")
    
    DEFAULT_GW_HOST = os.getenv("GATEWAY_HOST", "localhost")
    DEFAULT_GW_PORT = os.getenv("GATEWAY_PORT", "8183")
    DEFAULT_GW_ADDR = f"{DEFAULT_GW_HOST}:{DEFAULT_GW_PORT}"
    
    parser.add_argument('--gateway_host', type=str, default=DEFAULT_GW_ADDR,
                        help='Endereço (host:porta) do Gateway gRPC')
    args = parser.parse_args()

    print("Downloader - Responsável pelo Multicast de Escrita (Modo Dinâmico)")
    print("Digite Ctrl+C para encerrar.\n")
    
    downloader = Downloader(gateway_host=args.gateway_host)
    downloader.run()

if __name__ == '__main__':
    main()