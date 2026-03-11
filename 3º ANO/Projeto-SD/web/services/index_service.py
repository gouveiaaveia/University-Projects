"""
Service de Indexação - Lógica de negócio para indexar URLs.
"""
import sys
import os
import requests
from typing import Tuple

# Adiciona a pasta '../search' ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
search_dir = os.path.join(current_dir, '../../search')
sys.path.append(search_dir)

import grpc
import index_pb2
import index_pb2_grpc


class IndexService:
    """Service responsável por operações de indexação."""
    
    HN_SEARCH_URL = "http://hn.algolia.com/api/v1/search"
    
    def __init__(self, host: str = 'localhost', port: int = 8183):
        self.gateway_addr = f"{host}:{port}"
        self.channel = None
        self.stub = None
        self._connect()
    
    def _connect(self):
        """Estabelece conexão com o Gateway."""
        try:
            self.channel = grpc.insecure_channel(self.gateway_addr)
            self.stub = index_pb2_grpc.IndexStub(self.channel)
        except Exception as e:
            print(f"[IndexService] Erro ao conectar ao Gateway: {e}")
    
    def _ensure_connection(self):
        """Reconecta se necessário."""
        if self.channel is None or self.stub is None:
            self._connect()
    
    def index_url(self, url: str) -> Tuple[bool, str]:
    
        self._ensure_connection()
        
        try:
            self.stub.putNew(index_pb2.PutNewRequest(url=url))
            return True, "URL enviado para a fila de indexação."
        except grpc.RpcError as e:
            return False, f"Gateway indisponível ou erro gRPC: {e.code()}"
    
    def index_hacker_news(self, query: str, limit: int = 50) -> Tuple[int, str]:
    
        self._ensure_connection()
        count = 0
        
        try:
            params = {
                'query': query,
                'tags': 'story',
                'hitsPerPage': limit
            }
            
            print(f"[IndexService] A pesquisar HN por '{query}'...")
            resp = requests.get(self.HN_SEARCH_URL, params=params, timeout=10)
            
            if resp.status_code != 200:
                return 0, f"Erro na API HN: {resp.status_code}"
            
            data = resp.json()
            hits = data.get('hits', [])
            
            if not hits:
                return 0, f"Nenhuma notícia encontrada sobre '{query}'."
            
            for item in hits:
                url = item.get('url')
                if url:
                    print(f"[IndexService] A indexar: {url}")
                    success, _ = self.index_url(url)
                    if success:
                        count += 1
            
            return count, f"Sucesso: {count} de {len(hits)} notícias sobre '{query}' enviadas para indexação."
            
        except requests.RequestException as e:
            print(f"[IndexService] Erro HTTP: {e}")
            return 0, f"Erro ao contactar Hacker News: {str(e)}"
        except Exception as e:
            print(f"[IndexService] Exceção: {e}")
            return 0, f"Erro interno: {str(e)}"
    
    def close(self):
        """Fecha a conexão."""
        if self.channel:
            self.channel.close()
