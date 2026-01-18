import cv2
import asyncio
import base64

class LiveStreamService:
    @staticmethod
    async def start(websocket):
        cap = cv2.VideoCapture(0)

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame = cv2.resize(frame, (640, 480))

                _, buffer = cv2.imencode(
                    ".jpg",
                    frame,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 60]
                )

                await websocket.send_text(
                    base64.b64encode(buffer).decode("utf-8")
                )

                await asyncio.sleep(0.03)  # ~30 FPS

        except Exception as e:
            print("Stream stopped:", e)

        finally:
            cap.release()
