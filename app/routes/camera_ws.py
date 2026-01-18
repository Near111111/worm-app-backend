from fastapi import APIRouter, WebSocket
from app.services.camera_live_stream import LiveStreamService

router = APIRouter()

@router.websocket("/ws/camera")
async def camera_ws(websocket: WebSocket):
    await websocket.accept()
    await LiveStreamService.start(websocket)