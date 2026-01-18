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
            
            # Send "Heartbeat" for 3 seconds
            for i in range(3):
                await NotificationService.send_notification(
                    websocket, 
                    "Heartbeat", 
                    f"Heartbeat #{i+1}"
                )
                await asyncio.sleep(1)

            # After 3 seconds, send "Hello"
            await NotificationService.send_notification(
                websocket, 
                "Hello", 
                "Hello, world! 👋"
            )
            
            # Keep sending periodic notifications
            counter = 1
            while True:
                await asyncio.sleep(3)
                await NotificationService.send_notification(
                    websocket, 
                    "Test Notification", 
                    f"Test message #{counter} 📨"
                )
                counter += 1

        except Exception as e:
            print(f"🛑 Notification service stopped: {e}")