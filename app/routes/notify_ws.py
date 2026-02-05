from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.notification_service import NotificationService

router = APIRouter()

@router.websocket("/ws/notify")
async def notify_ws(websocket: WebSocket):
    await websocket.accept()
    client_host = websocket.client.host if websocket.client else "unknown"
    print(f"✅ Notification client connected from {client_host}")

    try:
        await NotificationService.start_monitoring(websocket)  # ← CHANGED HERE
    except WebSocketDisconnect:
        print(f"🔴 Notification client disconnected: {client_host}")
    except Exception as e:
        print(f"❌ Notification error for {client_host}: {e}")