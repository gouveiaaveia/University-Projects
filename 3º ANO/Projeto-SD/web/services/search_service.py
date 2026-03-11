"""
Service de Pesquisa - Lógica de negócio para pesquisas.
"""
import sys
import os
from typing import List, Optional

# Adiciona a pasta '../search' ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
search_dir = os.path.join(current_dir, '../../search')
sys.path.append(search_dir)

import grpc
import index_pb2
import index_pb2_grpc

from models.search import SearchResult, SearchResponse


class SearchService:
    """Service responsável por operações de pesquisa."""
    
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
            print(f"[SearchService] Erro ao conectar ao Gateway: {e}")
    
    def _ensure_connection(self):
        """Reconecta se necessário."""
        if self.channel is None or self.stub is None:
            self._connect()
    
    def search(self, query: str, page: int = 0, page_size: int = 10) -> SearchResponse:
        
        self._ensure_connection()
        
        try:
            req = index_pb2.SearchWordRequest(
                word=query, 
                page=page, 
                page_size=page_size
            )
            response = self.stub.searchWord(req)
            
            results = [
                SearchResult(
                    url=res.url,
                    title=res.title or "Sem título",
                    citation=res.citation or ""
                )
                for res in response.results
            ]
            
            return SearchResponse(
                results=results,
                total=response.total_results,
                has_more=response.has_more,
                current_page=page
            )
            
        except grpc.RpcError as e:
            print(f"[SearchService] Erro na pesquisa: {e}")
            return SearchResponse()
    
    def get_links_to(self, url: str) -> List[str]:
        self._ensure_connection()
        
        try:
            response = self.stub.searchListPages(
                index_pb2.SearchListPagesRequest(url=url)
            )
            return list(response.urls)
        except grpc.RpcError:
            return []
    
    def close(self):
        """Fecha a conexão."""
        if self.channel:
            self.channel.close()
