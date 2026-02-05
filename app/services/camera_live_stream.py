import cv2
import asyncio
import base64
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from ultralytics import YOLO
from pathlib import Path

class LiveStreamService:
    executor = ThreadPoolExecutor(max_workers=1)
    
    # Load YOLO model once
    BASE_DIR = Path(__file__).resolve().parents[2]  # Go up 2 levels from services
    MODEL_PATH = BASE_DIR / "app" / "yolo" / "models" / "trained" / "segmentv3.pt"
    VIDEO_PATH = BASE_DIR / "app" / "yolo" / "videos" / "worm-vid.MOV"  # Video file
    model = YOLO(str(MODEL_PATH))
    
    # Constants
    ROI_AREA_CM2 = 413
    ROI_AREA_M2 = ROI_AREA_CM2 / 10000
    AVG_WORM_AREA = 386
    
    @staticmethod
    def capture_frame(cap):
        """Run in separate thread with YOLO detection"""
        ret, frame = cap.read()
        
        # If video ended, loop back to start
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret:
                return None
        
        # Run YOLO inference
        results = LiveStreamService.model(frame, imgsz=640, conf=0.4, verbose=False)[0]
        
        # Count worms and calculate metrics
        mask_count = 0
        total_mask_area = 0
        alert_status = "Healthy Density"
        
        if results.masks is not None:
            masks = results.masks.data.cpu().numpy()
            
            for mask in masks:
                area = np.sum(mask)
                if area > 50:
                    mask_count += 1
                    total_mask_area += area
            
            area_est_count = total_mask_area / LiveStreamService.AVG_WORM_AREA if LiveStreamService.AVG_WORM_AREA > 0 else 0
            final_count = int(max(mask_count, area_est_count))
            
            larvae_per_cm2 = final_count / LiveStreamService.ROI_AREA_CM2
            larvae_per_m2 = final_count / LiveStreamService.ROI_AREA_M2
            
            if larvae_per_cm2 > 1.25:
                alert_status = f"⚠️ HIGH DENSITY: {larvae_per_cm2:.2f}/cm²"
        else:
            final_count = 0
            larvae_per_cm2 = 0
            larvae_per_m2 = 0
        
        # Get annotated frame with bounding boxes
        annotated_frame = results.plot()
        
        # Add text overlays
        cv2.putText(annotated_frame, f"Larvae Count: {final_count}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.putText(annotated_frame, f"Density: {larvae_per_cm2:.2f}/cm2", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.putText(annotated_frame, f"Per m2: {larvae_per_m2:.1f}", (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Alert status
        color = (0, 0, 255) if "HIGH" in alert_status else (0, 255, 0)
        cv2.putText(annotated_frame, alert_status, (20, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # Resize and encode
        frame = cv2.resize(annotated_frame, (640, 480))
        _, buffer = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        )
        return base64.b64encode(buffer).decode("utf-8")
    
    @staticmethod
    async def start(websocket):
        # Open video file instead of camera
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print(f"❌ Cannot open video file: {LiveStreamService.VIDEO_PATH}")
            return
        
        # Get video FPS to match original speed
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = 1.0 / fps if fps > 0 else 0.033  # Default to 30fps if fps is 0
        
        print(f"🎬 Playing video: {LiveStreamService.VIDEO_PATH.name} at {fps} FPS")
        
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
                await asyncio.sleep(frame_delay)  # Match video FPS

        except Exception as e:
            print("Stream stopped:", e)
        finally: 
            cap.release()