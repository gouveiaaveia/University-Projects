"""
Controller de Estatísticas.
Implementação Event-Driven: Só envia dados quando há mudanças reais.
"""
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio
import os
import json

router = APIRouter()

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "../templates"))


def get_stats_service():
    """Dependency injection para StatsService."""
    from services.stats_service import StatsService
    return StatsService(
        host=os.getenv("GATEWAY_HOST", "localhost"),
        port=int(os.getenv("GATEWAY_PORT", 8183))
    )


@router.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    """Página de estatísticas com WebSocket."""
    return templates.TemplateResponse("./StatsPage/stats.html", {"request": request})


def _stats_to_comparable(stats_dict: dict) -> str:
    """
    Converte estatísticas para string comparável (ordenada).
    Usado para detetar mudanças nos dados.
    """
    return json.dumps(stats_dict, sort_keys=True)


@router.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):

    await websocket.accept()
    service = get_stats_service()
    
    # Snapshot do último estado enviado (para comparação)
    last_snapshot = None
    
    try:
        while True:
            # Buscar dados frescos ao Gateway
            stats = service.get_system_stats()
            current_dict = stats.to_dict()
            
            # Criar snapshot comparável (hash dos dados)
            current_snapshot = _stats_to_comparable(current_dict)
            
            # Só envia se houver mudança (Event-Driven)
            if current_snapshot != last_snapshot:
                await websocket.send_json(current_dict)
                last_snapshot = current_snapshot
                print(f"[WebSocket] Estatísticas atualizadas (mudança detetada)")
            
            # Verificar mudanças a cada 500ms (half-second resolution)
            # Nota: Não é polling cego - só envia quando há mudança
            await asyncio.sleep(0.5)
            
    except WebSocketDisconnect:
        print("[WebSocket] Cliente desconectado.")
    except Exception as e:
        print(f"[WebSocket] Erro: {e}")
        await websocket.close()
