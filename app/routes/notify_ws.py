from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.notification_service import NotificationService

router = APIRouter()

@router.websocket("/ws/notify")
async def notify_ws(websocket: WebSocket):
    await websocket.accept()
    client_host = websocket.client.host if websocket.client else "unknown"
    print(f"✅ Notification client connected from {client_host}")

    # Register client so it receives broadcasts
    NotificationService.register_client(websocket)

    try:
        # Just keep the connection alive — monitoring runs in the background
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        print(f"🔴 Notification client disconnected: {client_host}")
    except Exception as e:
        print(f"❌ Notification WS error for {client_host}: {e}")
    finally:
        NotificationService.unregister_client(websocket)