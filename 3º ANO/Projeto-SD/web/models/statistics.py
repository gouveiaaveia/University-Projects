"""
Models para estatísticas do sistema.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class SearchStat:
    """Estatística de uma pesquisa."""
    query: str
    count: int = 0
    
    def to_dict(self) -> dict:
        return {
            'query': self.query,
            'count': self.count
        }


@dataclass
class BarrelInfo:
    """Informação sobre um Barrel."""
    barrel_id: str
    indexed_words_count: int = 0
    avg_response_time: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            'barrel_id': self.barrel_id,
            'indexed_words_count': self.indexed_words_count,
            'avg_response_time': self.avg_response_time
        }


@dataclass
class SystemStats:
    """Estatísticas globais do sistema."""
    top_searches: List[SearchStat] = field(default_factory=list)
    barrels: List[BarrelInfo] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'top_searches': [s.to_dict() for s in self.top_searches],
            'barrels': [b.to_dict() for b in self.barrels]
        }
