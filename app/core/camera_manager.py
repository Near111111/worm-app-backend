import cv2
import threading
import time


class CameraManager:
    """
    Singleton camera manager.
    - Single VideoCapture(0) shared across all services
    - Auto-reconnects if camera dies or is released
    - Thread-safe reads
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cap = None
            cls._instance._cap_lock = threading.Lock()
            cls._instance._running = True
            cls._instance._connect()
        return cls._instance

    def _connect(self):
        """Open or reopen the camera."""
        with self._cap_lock:
            if self._cap is not None:
                self._cap.release()
            self._cap = cv2.VideoCapture(0)
            if self._cap.isOpened():
                print("📷 Camera connected (CameraManager)")
            else:
                print("❌ Camera failed to open (CameraManager)")

    def read(self):
        """
        Thread-safe frame read with auto-reconnect.
        Returns (ret, frame) same as cv2.VideoCapture.read()
        """
        with self._cap_lock:
            if self._cap is None or not self._cap.isOpened():
                print("🔄 Camera not open, reconnecting...")
                self._cap = cv2.VideoCapture(0)
                time.sleep(1)

            ret, frame = self._cap.read()

            # Auto-reconnect if read fails
            if not ret:
                print("⚠️ Frame read failed, reconnecting camera...")
                self._cap.release()
                time.sleep(1)
                self._cap = cv2.VideoCapture(0)
                ret, frame = self._cap.read()

            return ret, frame

    def isOpened(self):
        with self._cap_lock:
            return self._cap is not None and self._cap.isOpened()

    def release(self):
        """Don't actually release — just log. Camera stays open for monitoring."""
        print("📷 CameraManager.release() called (ignored — keeping camera alive)")


# Global singleton instance
camera = CameraManager()
