from fastapi import APIRouter, WebSocket
from app.services.notification_service import NotificationService

router = APIRouter()

@router.websocket("/ws/notify")
async def notify_ws(websocket: WebSocket):
    await websocket.accept()
    print("Notification client connected")

    await NotificationService.start_heartbeat(websocket)  # Start sending notifications
