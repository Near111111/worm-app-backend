# app/services/session_service.py
"""
Single-user session lock with heartbeat.

How it works:
- When a client connects, it calls POST /api/session/lock
- Server checks if there's an active session
- If no active session → grants lock, returns session_id
- If active session → rejects with "server busy"
- Client sends POST /api/session/heartbeat every 10 seconds
- If no heartbeat for 30 seconds → session auto-expires
- Client calls POST /api/session/release on disconnect

Add to your main.py:
    from app.routes.session_route import router as session_router
    app.include_router(session_router)
"""

import time
import uuid
import asyncio
from datetime import datetime


class SessionService:
    _current_session_id: str | None = None
    _last_heartbeat: float = 0
    _client_info: str = ""
    _lock = asyncio.Lock()

    # Config
    HEARTBEAT_TIMEOUT = 30  # seconds — no heartbeat for 30s = auto-release

    @classmethod
    async def try_lock(cls, client_info: str = "") -> dict:
        """Try to acquire the session lock."""
        async with cls._lock:
            # Check if current session expired
            cls._check_expired()

            if cls._current_session_id is not None:
                return {
                    "success": False,
                    "message": "Server is currently in use by another device.",
                    "locked_by": cls._client_info,
                    "locked_since": datetime.fromtimestamp(cls._last_heartbeat).isoformat(),
                }

            # Grant new session
            cls._current_session_id = str(uuid.uuid4())
            cls._last_heartbeat = time.time()
            cls._client_info = client_info
            print(f"🔒 Session locked: {cls._current_session_id} ({client_info})")

            return {
                "success": True,
                "session_id": cls._current_session_id,
                "message": "Session granted.",
            }

    @classmethod
    async def heartbeat(cls, session_id: str) -> dict:
        """Renew the heartbeat for an active session."""
        async with cls._lock:
            cls._check_expired()

            if cls._current_session_id is None:
                return {"success": False, "message": "No active session."}

            if cls._current_session_id != session_id:
                return {"success": False, "message": "Invalid session ID."}

            cls._last_heartbeat = time.time()
            return {"success": True, "message": "Heartbeat received."}

    @classmethod
    async def release(cls, session_id: str) -> dict:
        """Release the session lock."""
        async with cls._lock:
            if cls._current_session_id is None:
                return {"success": True, "message": "No active session."}

            if cls._current_session_id != session_id:
                return {"success": False, "message": "Invalid session ID."}

            print(f"🔓 Session released: {cls._current_session_id} ({cls._client_info})")
            cls._current_session_id = None
            cls._last_heartbeat = 0
            cls._client_info = ""
            return {"success": True, "message": "Session released."}

    @classmethod
    async def status(cls) -> dict:
        """Get current session status."""
        async with cls._lock:
            cls._check_expired()
            return {
                "locked": cls._current_session_id is not None,
                "client_info": cls._client_info if cls._current_session_id else None,
            }

    @classmethod
    def _check_expired(cls):
        """Auto-release if heartbeat timed out. Call inside lock."""
        if cls._current_session_id is not None:
            elapsed = time.time() - cls._last_heartbeat
            if elapsed > cls.HEARTBEAT_TIMEOUT:
                print(f"⏰ Session expired (no heartbeat for {elapsed:.0f}s): {cls._current_session_id}")
                cls._current_session_id = None
                cls._last_heartbeat = 0
                cls._client_info = ""