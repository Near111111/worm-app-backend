# app/routes/session_route.py
"""
Session lock endpoints.

Add to main.py:
    from app.routes.session_route import router as session_router
    app.include_router(session_router)
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.services.session_service import SessionService

router = APIRouter(prefix="/api/session", tags=["Session"])


class LockRequest(BaseModel):
    client_info: str = ""


class SessionRequest(BaseModel):
    session_id: str


@router.post("/lock")
async def lock_session(req: LockRequest, request: Request):
    """
    Try to acquire the session lock.
    Returns session_id if successful, or error if server is busy.
    """
    client_host = request.client.host if request.client else "unknown"
    info = req.client_info or client_host
    return await SessionService.try_lock(info)


@router.post("/heartbeat")
async def heartbeat(req: SessionRequest):
    """
    Send heartbeat to keep session alive.
    Must be called every 10 seconds.
    """
    return await SessionService.heartbeat(req.session_id)


@router.post("/release")
async def release_session(req: SessionRequest):
    """
    Release the session lock.
    """
    return await SessionService.release(req.session_id)


@router.get("/status")
async def session_status():
    """
    Check if server is currently locked by another user.
    """
    return await SessionService.status()