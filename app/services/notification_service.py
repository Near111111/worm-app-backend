import asyncio
import json
from datetime import datetime

class NotificationService:
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
            await websocket.send_text(notification_json)
            print(f"✅ Notification sent successfully")
        except Exception as e:
            print(f"❌ Failed to send notification: {e}")

    @staticmethod
    async def start_heartbeat(websocket):
        try:
            print("🔔 Starting notification heartbeat...")
            while True:
                    await asyncio.sleep(30)
                    await NotificationService.send_notification(
                        websocket,
                        "Heartbeat",
                        "Connection is alive"
                    )
            
        except Exception as e:
            print(f"🛑 Notification service stopped: {e}")