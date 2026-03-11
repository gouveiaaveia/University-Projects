"""
Controller de IA.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "../templates"))


def get_ai_service():
    """Dependency injection para AIService."""
    from services.ai_service import AIService
    return AIService()


@router.get("/ai-mode", response_class=HTMLResponse)
async def ai_mode_page(request: Request):
    """Renderiza a página dedicada Googol IA."""
    return templates.TemplateResponse("./AIPage/ai.html", {"request": request})


@router.get("/api/ai-stream")
async def api_ai_stream(q: str):
    """
    Endpoint que retorna texto em stream.
    O browser vai ler isto chunk a chunk.
    """
    if not q:
        return "Por favor faça uma pergunta."
    
    service = get_ai_service()
    return StreamingResponse(service.stream_answer(q), media_type="text/plain")


@router.post("/api/ai-chat")
async def api_ai_chat(request: Request):
    """
    Endpoint de chat com suporte a histórico de conversa.
    Recebe a mensagem atual e o histórico via JSON.
    """
    service = get_ai_service()
    
    try:
        data = await request.json()
        message = data.get("message", "")
        history = data.get("history", [])
        
        if not message:
            return StreamingResponse(
                iter(["Por favor escreve uma mensagem."]), 
                media_type="text/plain"
            )
        
        return StreamingResponse(
            service.stream_chat_with_history(message, history), 
            media_type="text/plain"
        )
    except Exception as e:
        return StreamingResponse(
            iter([f"Erro ao processar pedido: {str(e)}"]), 
            media_type="text/plain"
        )
