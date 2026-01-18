# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from zeroconf import ServiceInfo, Zeroconf
import socket

from app.routes.camera_ws import router as camera_router
from app.routes.notify_ws import router as notify_router
from app.api.ip_handler import router as api_router

app = FastAPI()

# Add CORS middleware for React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local network
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(api_router)  # API routes
app.include_router(camera_router)  # WebSocket for camera
app.include_router(notify_router)  # WebSocket for notifications

# Get local IP function
def get_local_ip():
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

# API endpoint to get server info
@app.get("/api/server-info")
def server_info():
    return {
        "ip": get_local_ip(),
        "port": 8000,
        "websockets": {
            "camera": "/ws/camera",
            "notify": "/ws/notify"
        }
    }

# Global variables for mDNS
zeroconf = None
service_info = None

@app.on_event("startup")
async def startup_event():
    global zeroconf, service_info
    
    local_ip = get_local_ip()
    print(f"\n{'='*50}")
    print(f"🚀 Server starting on {local_ip}:8000")
    print(f"{'='*50}\n")
    
    # Register mDNS service
    try:
        zeroconf = Zeroconf()
        
        service_info = ServiceInfo(
            "_camera-stream._tcp.local.",
            "CameraStreamServer._camera-stream._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=8000,
            properties={
                'path': '/ws/camera',
                'notify_path': '/ws/notify'
            },
        )
        
        zeroconf.register_service(service_info)
        print(f"✅ mDNS service registered")
        print(f"📡 Broadcasting as 'CameraStreamServer'")
        print(f"🌐 Accessible at: http://{local_ip}:8000")
        print(f"📹 Camera WS: ws://{local_ip}:8000/ws/camera")
        print(f"🔔 Notify WS: ws://{local_ip}:8000/ws/notify\n")
        
    except Exception as e:
        print(f"⚠️  mDNS registration failed: {e}")
        print(f"💡 Server still accessible manually at http://{local_ip}:8000\n")

@app.on_event("shutdown")
async def shutdown_event():
    global zeroconf, service_info
    
    if zeroconf and service_info:
        zeroconf.unregister_service(service_info)
        zeroconf.close()
        print("\n🛑 mDNS service unregistered")