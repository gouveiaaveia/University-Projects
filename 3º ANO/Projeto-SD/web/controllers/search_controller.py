"""
Controller de Pesquisa.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "../templates"))


def get_search_service():
    """Dependency injection para SearchService."""
    from services.search_service import SearchService
    return SearchService(
        host=os.getenv("GATEWAY_HOST", "localhost"),
        port=int(os.getenv("GATEWAY_PORT", 8183))
    )


@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = "", p: int = 0):
    """Página de Resultados de Pesquisa."""
    service = get_search_service()
    page_size = 10
    
    if q:
        response = service.search(q, p, page_size)
        results = [r.to_dict() for r in response.results]
        total = response.total
        has_more = response.has_more
    else:
        results = []
        total = 0
        has_more = False
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    inicio = p * page_size + 1 if total > 0 else 0
    fim = min(inicio + page_size - 1, total)
    
    return templates.TemplateResponse("./SearchPage/search.html", {
        "request": request,
        "query": q,
        "page": p,
        "results": results,
        "total": total,
        "has_more": has_more,
        "total_pages": total_pages,
        "inicio": inicio,
        "fim": fim
    })


@router.get("/links-to", response_class=HTMLResponse)
async def links_to_page(request: Request, url: str = "", p: int = 0):
    """Página de links que apontam para um URL (com paginação)."""
    service = get_search_service()
    page_size = 10
    
    all_links = service.get_links_to(url) if url else []
    
    total_links = len(all_links)
    total_pages = max(1, (total_links + page_size - 1) // page_size)
    
    # Paginar os resultados
    start = p * page_size
    end = start + page_size
    paginated_links = all_links[start:end]
    
    return templates.TemplateResponse("./LinksToPage/linksTo.html", {
        "request": request,
        "target_url": url,
        "links": paginated_links,
        "total_links": total_links,
        "page": p,
        "total_pages": total_pages
    })
