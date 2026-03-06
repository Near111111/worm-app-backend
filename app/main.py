import asyncio
import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from zeroconf import ServiceInfo, Zeroconf

from app.services.mqtt_service import MQTTService
from app.services.notification_service import NotificationService  # ← NEW

from app.routes.camera_ws import router as camera_router
from app.routes.notify_ws import router as notify_router
from app.routes.sensor_ws import router as sensor_router
from app.routes.delete_notifications import router as delete_notifications_router
from app.routes.delete_images_route import router as delete_images_router
from app.api.ip_handler import router as api_router


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    local_ip = get_local_ip()

    # Start MQTT
    MQTTService.start(loop)

    # Start monitoring loop ONCE globally ← KEY FIX
    NotificationService.ensure_monitoring_started()

    # Register mDNS
    zeroconf = None
    service_info = None
    try:
        zeroconf = Zeroconf()
        service_info = ServiceInfo(
            "_camera-stream._tcp.local.",
            "CameraStreamServer._camera-stream._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=8000,
            properties={
                "path": "/ws/camera",
                "notify_path": "/ws/notify",
                "sensor_path": "/ws/sensors",
            },
        )
        zeroconf.register_service(service_info)
        print("✅ mDNS service registered")
    except Exception as e:
        print(f"⚠️  mDNS registration failed: {e}")

    print(f"\n{'='*50}")
    print(f"🚀 Server running on {local_ip}:8000")
    print(f"📹 Camera   WS : ws://{local_ip}:8000/ws/camera")
    print(f"🔔 Notify   WS : ws://{local_ip}:8000/ws/notify")
    print(f"🌡️  Sensors  WS : ws://{local_ip}:8000/ws/sensors")
    print(f"🗑️  Delete Images        : http://{local_ip}:8000/api/images/delete-all")
    print(f"🗑️  Delete Notifications : http://{local_ip}:8000/api/notifications/delete-all")
    print(f"{'='*50}\n")

    yield

    # Cleanup
    NotificationService.stop_monitoring()   # ← stop the loop cleanly
    MQTTService.stop()

    if zeroconf and service_info:
        zeroconf.unregister_service(service_info)
        zeroconf.close()
        print("\n🛑 mDNS service unregistered")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/api/server-info")
def server_info():
    return {
        "ip": get_local_ip(),
        "port": 8000,
        "websockets": {
            "camera":  "/ws/camera",
            "notify":  "/ws/notify",
            "sensors": "/ws/sensors",
        },
    }

app.include_router(api_router)
app.include_router(delete_notifications_router)
app.include_router(delete_images_router)
app.include_router(camera_router)
app.include_router(notify_router)
app.include_router(sensor_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)