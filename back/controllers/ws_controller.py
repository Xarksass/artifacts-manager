# routers/ws.py
from core.ws_manager import manager
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/ws/")
async def character_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # on n'attend rien de précis du front pour l'instant — juste garder
            # la connexion ouverte jusqu'à ce que le client la ferme
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)