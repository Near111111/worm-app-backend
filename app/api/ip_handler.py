import socket
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ServerInfo(BaseModel):
    ip: str
    port: int
    status: str

class CameraInfo(BaseModel):
    ip: str
    port: int
    websocket_url: str
    status: str

class NotificationInfo(BaseModel):
    ip: str
    port: int
    websocket_url: str
    status: str

def get_local_ip() -> str:
    """Get the local IP address of the server"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

@router.get("/api/server-info", response_model=ServerInfo)
async def get_server_info():
    """
    Returns basic server information
    """
    local_ip = get_local_ip()
    
    return ServerInfo(
        ip=local_ip,
        port=8000,
        status="online"
    )

@router.get("/api/camera-info", response_model=CameraInfo)
async def get_camera_info():
    """
    Returns camera WebSocket endpoint information
    """
    local_ip = get_local_ip()
    
    return CameraInfo(
        ip=local_ip,
        port=8000,
        websocket_url=f"ws://{local_ip}:8000/ws/camera",
        status="online"
    )

@router.get("/api/notification-info", response_model=NotificationInfo)
async def get_notification_info():
    """
    Returns notification WebSocket endpoint information
    """
    local_ip = get_local_ip()
    
    return NotificationInfo(
        ip=local_ip,
        port=8000,
        websocket_url=f"ws://{local_ip}:8000/ws/notify",
        status="online"
    )

@router.get("/api/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "ok",
        "message": "Server is running"
    }