"""
Models para pesquisa e indexação.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchResult:
    """Representa um resultado de pesquisa individual."""
    url: str
    title: str = "Sem título"
    citation: str = ""
    
    def to_dict(self) -> dict:
        return {
            'url': self.url,
            'title': self.title,
            'citation': self.citation
        }


@dataclass
class SearchResponse:
    """Resposta completa de uma pesquisa."""
    results: List[SearchResult] = field(default_factory=list)
    total: int = 0
    has_more: bool = False
    current_page: int = 0
    
    def to_dict(self) -> dict:
        return {
            'results': [r.to_dict() for r in self.results],
            'total': self.total,
            'has_more': self.has_more,
            'current_page': self.current_page
        }


@dataclass
class PageInfo:
    """Informação sobre uma página indexada."""
    url: str
    title: str = "Sem título"
    citation: str = ""
    words: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)


@dataclass
class IndexRequest:
    """Pedido de indexação de URL."""
    url: str
    success: bool = False
    message: str = ""
