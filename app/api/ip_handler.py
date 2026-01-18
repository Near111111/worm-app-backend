import socket
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ServerInfo(BaseModel):
    ip: str
    port: int
    websockets: dict
    status: str

def get_local_ip() -> str:
    """Get the local IP address of the server"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to external address (doesn't actually send data)
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
    Returns current server IP and WebSocket endpoints
    React Native app can call this to discover the server
    """
    local_ip = get_local_ip()
    
    return ServerInfo(
        ip=local_ip,
        port=8000,
        websockets={
            "camera": f"ws://{local_ip}:8000/ws/camera",
            "notify": f"ws://{local_ip}:8000/ws/notify"
        },
        status="online"
    )

@router.get("/api/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "ok",
        "message": "Server is running"
    }