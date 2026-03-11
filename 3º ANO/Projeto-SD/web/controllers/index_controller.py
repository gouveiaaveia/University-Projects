"""
Controller de Indexação.
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "../templates"))


def get_index_service():
    """Dependency injection para IndexService."""
    from services.index_service import IndexService
    return IndexService(
        host=os.getenv("GATEWAY_HOST", "localhost"),
        port=int(os.getenv("GATEWAY_PORT", 8183))
    )


@router.get("/index-link", response_class=HTMLResponse)
async def index_link_page(request: Request):
    """Página para indexar novos URLs."""
    return templates.TemplateResponse("./IndexLinkPage/indexLink.html", {
        "request": request,
        "message": None,
        "success": False
    })


@router.post("/index-link", response_class=HTMLResponse)
async def index_link_submit(request: Request, url: str = Form(...)):
    """Recebe um URL e envia para indexação."""
    service = get_index_service()
    success, message = service.index_url(url)
    
    return templates.TemplateResponse("./IndexLinkPage/indexLink.html", {
        "request": request,
        "message": message,
        "success": success
    })
