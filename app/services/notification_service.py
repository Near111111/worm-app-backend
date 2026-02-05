import asyncio
import json
from datetime import datetime, timedelta
from app.repositories.previous_notification_dao import PreviousNotificationDAO
from app.repositories.saved_images_dao import SavedImagesDAO
from app.services.image_service import ImageService
import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path

class NotificationService:
    camera_cap = cv2.VideoCapture(0)
    
    # Load YOLO model
    BASE_DIR = Path(__file__).resolve().parents[1]
    MODEL_PATH = BASE_DIR / "yolo" / "models" / "trained" / "segmentv3.pt"
    model = YOLO(str(MODEL_PATH))
    
    # Constants
    ROI_AREA_CM2 = 413
    AVG_WORM_AREA = 386
    DENSITY_THRESHOLD = 1.25  # larvae per cm²
    
    # Tracking
    last_notification_time = None
    NOTIFICATION_COOLDOWN = timedelta(minutes=30)

    @staticmethod
    def check_larvae_density():
        """Check current larvae density using YOLO"""
        ret, frame = NotificationService.camera_cap.read()
        if not ret:
            return False, 0, 0
        
        # Run YOLO inference
        results = NotificationService.model(frame, imgsz=640, conf=0.4, verbose=False)[0]
        
        mask_count = 0
        total_mask_area = 0
        
        if results.masks is not None:
            masks = results.masks.data.cpu().numpy()
            
            for mask in masks:
                area = np.sum(mask)
                if area > 50:
                    mask_count += 1
                    total_mask_area += area
            
            area_est_count = total_mask_area / NotificationService.AVG_WORM_AREA if NotificationService.AVG_WORM_AREA > 0 else 0
            final_count = int(max(mask_count, area_est_count))
            larvae_per_cm2 = final_count / NotificationService.ROI_AREA_CM2
            
            # Check if HIGH density
            is_high_density = larvae_per_cm2 > NotificationService.DENSITY_THRESHOLD
            
            return is_high_density, larvae_per_cm2, final_count
        
        return False, 0, 0

    @staticmethod
    async def send_notification(websocket, title, message, larvae_count=0, density=0):
        notification = {
            "title": title,
            "message": message,
            "larvae_count": larvae_count,
            "density_per_cm2": round(density, 2),
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
                SavedImagesDAO.save(snapshot_url)
            
            # Update last notification time
            NotificationService.last_notification_time = datetime.now()

        except Exception as e:
            print(f"❌ Failed to send notification: {e}")

    @staticmethod
    def should_send_notification():
        """Check if enough time has passed since last notification"""
        if NotificationService.last_notification_time is None:
            return True
        
        time_since_last = datetime.now() - NotificationService.last_notification_time
        return time_since_last >= NotificationService.NOTIFICATION_COOLDOWN

    @staticmethod
    async def start_monitoring(websocket):
        """Monitor larvae density every 30 seconds, send notification every 30 mins if HIGH"""
        try:
            while True:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Check current density
                is_high_density, density, count = NotificationService.check_larvae_density()
                
                if is_high_density:
                    print(f"⚠️ HIGH DENSITY DETECTED: {density:.2f}/cm² ({count} larvae)")
                    
                    # Only send notification if cooldown period has passed
                    if NotificationService.should_send_notification():
                        await NotificationService.send_notification(
                            websocket,
                            "⚠️ High Larvae Density Alert",
                            f"Overpopulated! Detected {count} larvae ({density:.2f}/cm²)",
                            larvae_count=count,
                            density=density
                        )
                        print(f"✅ Notification sent. Next notification in 30 minutes.")
                    else:
                        time_remaining = NotificationService.NOTIFICATION_COOLDOWN - (
                            datetime.now() - NotificationService.last_notification_time
                        )
                        minutes_left = int(time_remaining.total_seconds() / 60)
                        print(f"🕒 HIGH density detected but cooldown active ({minutes_left} min remaining)")
                else:
                    print(f"✅ Healthy density: {density:.2f}/cm² ({count} larvae)")
                    
        except Exception as e:
            print(f"🛑 Notification monitoring stopped: {e}")