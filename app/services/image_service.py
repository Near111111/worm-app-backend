import cv2
import os
from datetime import datetime
from app.core.supabase_client import supabase

class ImageService:
    @staticmethod
    def capture_and_upload_snapshot(cap) -> str:
        """
        Capture a frame from the live stream and upload to Supabase Storage.
        Returns the public URL of the uploaded image.
        """
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to capture frame")
            return None

        # Resize for standard size
        frame = cv2.resize(frame, (640, 480))

        # Create local temporary file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{timestamp}.jpg"
        tmp_path = os.path.join("snapshots_temp", filename)
        os.makedirs("snapshots_temp", exist_ok=True)
        cv2.imwrite(tmp_path, frame)

        # Upload to Supabase Storage
        try:
            with open(tmp_path, 'rb') as f:
                file_data = f.read()
            
            bucket = supabase.storage.from_("snapshots")
            bucket.upload(
                path=filename,
                file=file_data,
                file_options={"content-type": "image/jpeg"}
            )
            
            url = bucket.get_public_url(filename)
            print(f"📸 Snapshot uploaded to Supabase: {url}")
            return url
            
        except Exception as e:
            print(f"❌ Failed to upload snapshot: {e}")
            return None
            
        finally:
            # Remove local file after upload
            if os.path.exists(tmp_path):
                os.remove(tmp_path)