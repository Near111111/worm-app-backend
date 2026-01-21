import cv2
import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor

class LiveStreamService:
    executor = ThreadPoolExecutor(max_workers=1)
    
    @staticmethod
    def capture_frame(cap):
        """Run in separate thread"""
        ret, frame = cap.read()
        if not ret:
            return None
        
        frame = cv2.resize(frame, (640, 480))
        _, buffer = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 60]
        )
        return base64.b64encode(buffer).decode("utf-8")
    
    @staticmethod
    async def start(websocket):
        cap = cv2.VideoCapture(0)
        loop = asyncio.get_event_loop()

        try:
            while True:
                frame_data = await loop.run_in_executor(
                    LiveStreamService.executor,
                    LiveStreamService.capture_frame,
                    cap
                )
                
                if frame_data is None:
                    break

                await websocket.send_text(frame_data)
                await asyncio.sleep(0.03)  # ~30 FPS

        except Exception as e:
            print("Stream stopped:", e)
        finally: 
            cap.release()