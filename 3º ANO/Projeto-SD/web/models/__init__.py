# Models - Camada de dados e lógica de negócio
from .search import SearchResult, SearchResponse, PageInfo
from .statistics import BarrelInfo, SearchStat, SystemStats
from .ai import AIMessage, ChatHistory

__all__ = [
    'SearchResult', 'SearchResponse', 'PageInfo',
    'BarrelInfo', 'SearchStat', 'SystemStats',
    'AIMessage', 'ChatHistory'
]
