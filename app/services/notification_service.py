import asyncio
import json

class NotificationService:
    @staticmethod
    async def send_notification(websocket, title, message):
        notification = {
            "title": title,
            "message": message
        }

        # Sending notification to the client
        await websocket.send_text(json.dumps(notification))

    @staticmethod
    async def start_heartbeat(websocket):
        try:
            # Send "Heartbeat" for 3 seconds
            for _ in range(3):
                await NotificationService.send_notification(websocket, "Heartbeat", "First")
                await asyncio.sleep(1)  # Wait for 1 second

            # After 3 seconds, send "Hello"
            await NotificationService.send_notification(websocket, "Hello", "Hello, world!")
            
            while True:
                await asyncio.sleep(3)  # Wait for 3 seconds before sending another notification
                await NotificationService.send_notification(websocket, "Test", "Test Test")

        except Exception as e:
            print("Notification stopped:", e)
