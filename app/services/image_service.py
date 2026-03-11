import cv2
import os
from datetime import datetime
from app.core.supabase_client import supabase
from app.core.camera_manager import camera  # ← Shared camera singleton


class ImageService:
    @staticmethod
    def capture_and_upload_snapshot(cap=None) -> str:
        """
        Capture a YOLO-annotated frame and upload to Supabase Storage.
        Uses shared camera singleton — ignores the cap parameter.
        """
        # Always use shared camera (cap param kept for backward compat)
        ret, frame = camera.read()
        if not ret or frame is None:
            print("❌ Failed to capture frame")
            return None

        try:
            from app.services.camera_live_stream import LiveStreamService
            results = LiveStreamService.model(
                frame, imgsz=640, conf=0.4, verbose=False
            )[0]

            annotated = results.plot(
                conf=False,
                labels=False,
                boxes=True,
                line_width=2
            )
        except Exception as e:
            print(f"⚠️ YOLO annotation failed, using raw frame: {e}")
            annotated = frame

        annotated = cv2.resize(annotated, (640, 480))

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"snapshot_{timestamp}.jpg"
        tmp_path  = os.path.join("snapshots_temp", filename)
        os.makedirs("snapshots_temp", exist_ok=True)
        cv2.imwrite(tmp_path, annotated)

        try:
            with open(tmp_path, "rb") as f:
                file_data = f.read()

            bucket = supabase.storage.from_("snapshots")
            bucket.upload(
                path=filename,
                file=file_data,
                file_options={"content-type": "image/jpeg"},
            )

            url = bucket.get_public_url(filename)
            print(f"📸 Snapshot uploaded: {url}")
            return url

        except Exception as e:
            print(f"❌ Failed to upload snapshot: {e}")
            return None

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
