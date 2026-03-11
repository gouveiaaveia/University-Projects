"""
Controller de APIs REST.
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse
import os

router = APIRouter(prefix="/api")


def get_index_service():
    """Dependency injection para IndexService."""
    from services.index_service import IndexService
    return IndexService(
        host=os.getenv("GATEWAY_HOST", "localhost"),
        port=int(os.getenv("GATEWAY_PORT", 8183))
    )


def get_search_service():
    """Dependency injection para SearchService."""
    from services.search_service import SearchService
    return SearchService(
        host=os.getenv("GATEWAY_HOST", "localhost"),
        port=int(os.getenv("GATEWAY_PORT", 8183))
    )


def get_ai_service():
    """Dependency injection para AIService."""
    from services.ai_service import AIService
    return AIService()


@router.post("/index")
async def api_index_url(url: str = Form(...)):
    """Recebe um URL manualmente e envia para indexação."""
    service = get_index_service()
    success, msg = service.index_url(url)
    return JSONResponse({"success": success, "message": msg})


@router.get("/search")
async def api_search(q: str = "", p: int = 0, page_size: int = 10):
    """
    API REST para pesquisa - retorna resultados em JSON.
    """
    if not q:
        return JSONResponse({
            "success": False,
            "error": "Query vazia",
            "results": [],
            "total": 0,
            "has_more": False
        })
    
    try:
        service = get_search_service()
        response = service.search(q, p, page_size)
        
        return JSONResponse({
            "success": True,
            "query": q,
            "page": p,
            "results": [r.to_dict() for r in response.results],
            "total": response.total,
            "has_more": response.has_more
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "results": [],
            "total": 0,
            "has_more": False
        })


@router.post("/hackernews-search")
async def api_hackernews_search(request: Request):
    """
    Pesquisa as top 50 stories do Hacker News que contêm os termos da pesquisa.
    """
    try:
        data = await request.json()
        query = data.get("query", "")
    except:
        return JSONResponse({"success": False, "count": 0, "message": "Erro ao processar pedido."})
    
    if not query:
        return JSONResponse({"success": False, "count": 0, "message": "Nenhum termo de pesquisa fornecido."})
    
    service = get_index_service()
    count, msg = service.index_hacker_news(query, limit=50)
    return JSONResponse({"success": True, "count": count, "message": msg})


@router.post("/ai-summary")
async def api_ai_summary(request: Request):
    """
    Endpoint para gerar resumo de IA baseado nos resultados de pesquisa.
    """
    try:
        data = await request.json()
        query = data.get("query", "")
        results = data.get("results", [])
        
        if not query or not results:
            return JSONResponse({"summary": ""})
        
        service = get_ai_service()
        summary = service.generate_search_summary(query, results)
        return JSONResponse({"summary": summary})
        
    except Exception as e:
        return JSONResponse({"summary": ""})
