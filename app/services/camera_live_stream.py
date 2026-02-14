import cv2
import asyncio
import base64
import json
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from ultralytics import YOLO
from pathlib import Path

class LiveStreamService:
    executor = ThreadPoolExecutor(max_workers=1)
    
    # Shared state for stats
    current_stats = {
        "larvae_count": 0,
        "density_cm2": 0,
        "density_m2": 0,
        "is_high_density": False,
        "timestamp": ""
    }
    stats_lock = asyncio.Lock()
    
    # Load YOLO model once
    BASE_DIR = Path(__file__).resolve().parents[2]
    MODEL_PATH = BASE_DIR / "app" / "yolo" / "models" / "trained" / "wormv11-seg-final.pt"
    VIDEO_PATH = BASE_DIR / "app" / "yolo" / "videos" / "worm-vid.MOV"
    model = YOLO(str(MODEL_PATH))
    
    # Constants
    ROI_AREA_CM2 = 413
    ROI_AREA_M2 = ROI_AREA_CM2 / 10000
    AVG_WORM_AREA = 386
    DENSITY_THRESHOLD = 1.25
    
    @staticmethod
    def capture_frame(cap):
        """Run YOLO once, return clean video frame + update stats"""
        ret, frame = cap.read()
        
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret:
                return None
        
        # Run YOLO inference ONCE
        results = LiveStreamService.model(frame, imgsz=640, conf=0.4, verbose=False)[0]
        
        # Calculate stats
        mask_count = 0
        total_mask_area = 0
        
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
            is_high = larvae_per_cm2 > LiveStreamService.DENSITY_THRESHOLD
        else:
            final_count = 0
            larvae_per_cm2 = 0
            larvae_per_m2 = 0
            is_high = False
        
        # Update shared stats (thread-safe)
        from datetime import datetime
        LiveStreamService.current_stats = {
            "larvae_count": final_count,
            "density_cm2": round(larvae_per_cm2, 2),
            "density_m2": round(larvae_per_m2, 1),
            "is_high_density": is_high,
            "timestamp": datetime.now().isoformat()
        }
        
        # Get CLEAN annotated frame (bounding boxes only, NO labels/confidence)
        annotated_frame = results.plot(
            conf=False,        # ← Hide confidence scores
            labels=False,      # ← Hide class labels
            boxes=True,        # ✓ Show bounding boxes only
            line_width=2
        )
        
        # Resize and encode
        frame = cv2.resize(annotated_frame, (640, 480))
        _, buffer = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        )
        return base64.b64encode(buffer).decode("utf-8")
    
    @staticmethod
    async def start_video_stream(websocket):
        """Send clean video frames"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print(f"❌ Cannot open video file")
            return
        
        print(f"🎬 Playing video at 30 FPS (clean UI)")
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
                await asyncio.sleep(0.033)  # 30 FPS

        except Exception as e:
            print("Video stream stopped:", e)
        finally: 
            cap.release()
    
    @staticmethod
    async def start_stats_stream(websocket):
        """Send stats updates (lighter, ~10 updates per second)"""
        try:
            while True:
                # Send current stats as JSON
                stats_json = json.dumps(LiveStreamService.current_stats)
                await websocket.send_text(stats_json)
                await asyncio.sleep(0.1)  # 10 updates/sec (lighter than video)
                
        except Exception as e:
            print("Stats stream stopped:", e)