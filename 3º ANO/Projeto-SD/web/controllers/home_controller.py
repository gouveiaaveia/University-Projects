"""
Controller da Página Inicial.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "../templates"))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página Inicial."""
    return templates.TemplateResponse("./HomePage/home.html", {"request": request})
