# Controllers - Rotas e handling de requests
from .home_controller import router as home_router
from .search_controller import router as search_router
from .index_controller import router as index_router
from .stats_controller import router as stats_router
from .ai_controller import router as ai_router
from .api_controller import router as api_router

__all__ = [
    'home_router',
    'search_router',
    'index_router',
    'stats_router',
    'ai_router',
    'api_router'
]
