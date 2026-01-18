from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routes.camera_ws import router as camera_router
from app.routes.notify_ws import router as notify_router

app = FastAPI()

@app.get("/")
def home():
    return FileResponse("static/index.html")  # Serve index.html directly from static folder

app.mount(
    "/static",
    StaticFiles(directory="static"),  # No "app" prefix, since static is outside
    name="static"
)

app.include_router(camera_router)  # WebSocket for camera stream
app.include_router(notify_router)  # WebSocket for notifications
