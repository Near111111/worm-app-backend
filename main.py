from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routes.camera_ws import router as camera_router

app = FastAPI()

@app.get("/")
def home():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(camera_router)
