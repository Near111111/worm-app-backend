# app/routes/camera_ws.py

from fastapi import APIRouter, WebSocket
from app.services.camera_live_stream import LiveStreamService

router = APIRouter()

@router.websocket("/ws/camera")
async def camera_ws(websocket: WebSocket):
    await websocket.accept()
    await LiveStreamService.start_video_stream(websocket)

@router.websocket("/ws/camera-stats")  #Eto yung sa live stats Rai
async def camera_stats_ws(websocket: WebSocket):
    await websocket.accept()
    await LiveStreamService.start_stats_stream(websocket)