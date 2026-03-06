import cv2
import os
from datetime import datetime
from app.core.supabase_client import supabase


class ImageService:
    @staticmethod
    def capture_and_upload_snapshot(cap) -> str:
        """
        Capture a YOLO-annotated frame and upload to Supabase Storage.
        Reuses LiveStreamService.model so no second model is loaded.
        """
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to capture frame")
            return None

        # ── Run YOLO on the frame (reuse existing model) ──────────────────
        try:
            from app.services.camera_live_stream import LiveStreamService
            results = LiveStreamService.model(
                frame, imgsz=640, conf=0.4, verbose=False
            )[0]

            # Annotated frame with bounding boxes, no labels/confidence
            annotated = results.plot(
                conf=False,
                labels=False,
                boxes=True,
                line_width=2
            )
        except Exception as e:
            print(f"⚠️ YOLO annotation failed, using raw frame: {e}")
            annotated = frame  # fallback to raw if YOLO fails

        # ── Resize & save to temp file ────────────────────────────────────
        annotated = cv2.resize(annotated, (640, 480))

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"snapshot_{timestamp}.jpg"
        tmp_path  = os.path.join("snapshots_temp", filename)
        os.makedirs("snapshots_temp", exist_ok=True)
        cv2.imwrite(tmp_path, annotated)

        # ── Upload to Supabase Storage ────────────────────────────────────
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
            print(f"📸 Snapshot uploaded to Supabase: {url}")
            return url

        except Exception as e:
            print(f"❌ Failed to upload snapshot: {e}")
            return None

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)