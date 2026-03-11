"""
Service de Estatísticas - Lógica de negócio para estatísticas do sistema.
"""
import sys
import os

# Adiciona a pasta '../search' ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
search_dir = os.path.join(current_dir, '../../search')
sys.path.append(search_dir)

import grpc
from google.protobuf import empty_pb2
import index_pb2
import index_pb2_grpc

from models.statistics import SearchStat, BarrelInfo, SystemStats


class StatsService:
    """Service responsável por estatísticas do sistema."""
    
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
            print(f"[StatsService] Erro ao conectar ao Gateway: {e}")
    
    def _ensure_connection(self):
        """Reconecta se necessário."""
        if self.channel is None or self.stub is None:
            self._connect()
    
    def get_system_stats(self) -> SystemStats:
        """
        Obtém estatísticas do sistema.
        
        Returns:
            SystemStats com top searches e info dos barrels
        """
        self._ensure_connection()
        
        try:
            stats = self.stub.getStatistics(empty_pb2.Empty())
            
            top_searches = [
                SearchStat(query=s.query, count=s.count)
                for s in stats.top_searches
            ]
            
            barrels = [
                BarrelInfo(
                    barrel_id=b.barrel_id,
                    indexed_words_count=b.indexed_words_count,
                    avg_response_time=b.avg_response_time
                )
                for b in stats.barrels
            ]
            
            return SystemStats(top_searches=top_searches, barrels=barrels)
            
        except grpc.RpcError:
            return SystemStats()
    
    def close(self):
        """Fecha a conexão."""
        if self.channel:
            self.channel.close()
