import asyncio
import json
from datetime import datetime
from app.repositories.previous_notification_dao import PreviousNotificationDAO
from app.repositories.saved_images_dao import SavedImagesDAO
from app.services.image_service import ImageService
import cv2

class NotificationService:
    camera_cap = cv2.VideoCapture(0)  # keep one camera instance

    @staticmethod
    async def send_notification(websocket, title, message):
        notification = {
            "title": title,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

        notification_json = json.dumps(notification)
        print(f"📤 Sending notification: {notification_json}")

        try:
            # Send via WebSocket
            await websocket.send_text(notification_json)

            # Save notification to DB
            PreviousNotificationDAO.save(message)

            # Take snapshot & upload to Supabase Storage
            snapshot_url = ImageService.capture_and_upload_snapshot(NotificationService.camera_cap)
            if snapshot_url:
                # Save snapshot URL to DB
                SavedImagesDAO.save(snapshot_url)

        except Exception as e:
            print(f"❌ Failed to send notification: {e}")

    @staticmethod
    async def start_heartbeat(websocket):
        try:
            while True:
                await asyncio.sleep(30)
                await NotificationService.send_notification(
                    websocket,
                    "Heartbeat",
                    "Too much larvae on 1 area!"
                )
        except Exception as e:
            print(f"🛑 Notification service stopped: {e}")
