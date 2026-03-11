import asyncio
import json
from datetime import datetime, timedelta
from app.repositories.previous_notification_dao import PreviousNotificationDAO
from app.repositories.saved_images_dao import SavedImagesDAO
from app.services.image_service import ImageService
from app.services.mqtt_service import MQTTService
import numpy as np
from ultralytics import YOLO
from pathlib import Path
from app.core.camera_manager import camera  # ← Shared camera singleton


class NotificationService:

    # Load YOLO model
    BASE_DIR = Path(__file__).resolve().parents[1]
    MODEL_PATH = BASE_DIR / "yolo" / "models" / "trained" / "worms-seg.pt"
    model = YOLO(str(MODEL_PATH))

    # Constants
    ROI_AREA_CM2 = 413
    AVG_WORM_AREA = 386
    DENSITY_THRESHOLD = 1.25

    # Cooldowns
    last_notification_time = None
    NOTIFICATION_COOLDOWN = timedelta(minutes=30)

    last_hourly_report_time = None
    HOURLY_REPORT_INTERVAL = timedelta(hours=1)

    # ── Singleton monitoring task ──────────────────────────────────────────
    _monitoring_task: asyncio.Task | None = None

    # All connected notification WebSocket clients
    active_clients: set = set()

    # ──────────────────────────────────────────────────────────────────────

    @classmethod
    def register_client(cls, websocket):
        cls.active_clients.add(websocket)
        print(f"🔔 Notification client registered. Total: {len(cls.active_clients)}")

    @classmethod
    def unregister_client(cls, websocket):
        cls.active_clients.discard(websocket)
        print(f"🔴 Notification client removed. Total: {len(cls.active_clients)}")

    @classmethod
    async def broadcast(cls, notification: dict):
        message = json.dumps(notification)
        print(f"📤 Broadcasting notification: {message}")

        dead = set()
        for ws in list(cls.active_clients):
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)

        for ws in dead:
            cls.active_clients.discard(ws)

    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def check_larvae_density():
        # Use shared camera singleton — never dies
        ret, frame = camera.read()
        if not ret:
            print("⚠️ Could not read frame from camera")
            return False, 0, 0

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

            area_est_count = (
                total_mask_area / NotificationService.AVG_WORM_AREA
                if NotificationService.AVG_WORM_AREA > 0 else 0
            )
            final_count = int(max(mask_count, area_est_count))
            larvae_per_cm2 = final_count / NotificationService.ROI_AREA_CM2
            return larvae_per_cm2 > NotificationService.DENSITY_THRESHOLD, larvae_per_cm2, final_count

        return False, 0, 0

    @classmethod
    async def _send_and_persist(cls, title, message, larvae_count=0, density=0,
                                include_sensor=False, report_type="density_alert"):
        sensor = MQTTService.get_sensor_data()

        notification = {
            "type": report_type,
            "title": title,
            "message": message,
            "larvae_count": larvae_count,
            "density_per_cm2": round(density, 2),
            "timestamp": datetime.now().isoformat(),
        }

        if include_sensor:
            notification["temperature"] = sensor["temperature"]
            notification["humidity"] = sensor["humidity"]

        await cls.broadcast(notification)

        try:
            PreviousNotificationDAO.save(notification)
        except Exception as e:
            print(f"❌ Failed to save notification: {e}")

        try:
            # Pass shared camera to image service
            snapshot_url = ImageService.capture_and_upload_snapshot(camera)
            if snapshot_url:
                SavedImagesDAO.save(snapshot_url)
        except Exception as e:
            print(f"❌ Failed to save snapshot: {e}")

        if report_type == "density_alert":
            cls.last_notification_time = datetime.now()
        elif report_type == "hourly_report":
            cls.last_hourly_report_time = datetime.now()

    # ──────────────────────────────────────────────────────────────────────

    @classmethod
    def should_send_density_alert(cls):
        if cls.last_notification_time is None:
            return True
        return datetime.now() - cls.last_notification_time >= cls.NOTIFICATION_COOLDOWN

    @classmethod
    def should_send_hourly_report(cls):
        if cls.last_hourly_report_time is None:
            return True
        return datetime.now() - cls.last_hourly_report_time >= cls.HOURLY_REPORT_INTERVAL

    # ──────────────────────────────────────────────────────────────────────

    @classmethod
    async def _monitoring_loop(cls):
        print("🔁 Monitoring loop started (singleton)")
        try:
            while True:
                await asyncio.sleep(30)

                is_high, density, count = cls.check_larvae_density()

                # --- HOURLY REPORT ---
                if cls.should_send_hourly_report():
                    sensor = MQTTService.get_sensor_data()
                    status = "HIGH" if is_high else "Normal"

                    await cls._send_and_persist(
                        "📊 Hourly Monitoring Report",
                        (
                            f"Hourly Report — Status: {status} | "
                            f"Larvae: {count} ({density:.2f}/cm²) | "
                            f"Temp: {sensor['temperature']}°C | "
                            f"Humidity: {sensor['humidity']}%"
                        ),
                        larvae_count=count,
                        density=density,
                        include_sensor=True,
                        report_type="hourly_report",
                    )
                    print("📊 Hourly report sent. Next in 1 hour.")

                # --- DENSITY ALERT ---
                if is_high:
                    print(f"⚠️ HIGH DENSITY: {density:.2f}/cm² ({count} larvae)")
                    if cls.should_send_density_alert():
                        await cls._send_and_persist(
                            "⚠️ High Larvae Density Alert",
                            f"Overpopulated! Detected {count} larvae ({density:.2f}/cm²)",
                            larvae_count=count,
                            density=density,
                            include_sensor=False,
                            report_type="density_alert",
                        )
                        print("✅ Density alert sent. Next in 30 minutes.")
                    else:
                        remaining = cls.NOTIFICATION_COOLDOWN - (
                            datetime.now() - cls.last_notification_time
                        )
                        print(f"🕒 Cooldown active ({int(remaining.total_seconds()/60)} min left)")
                else:
                    print(f"✅ Healthy density: {density:.2f}/cm² ({count} larvae)")

        except asyncio.CancelledError:
            print("🛑 Monitoring loop cancelled")
        except Exception as e:
            print(f"🛑 Monitoring loop crashed: {e}")

    @classmethod
    def ensure_monitoring_started(cls):
        if cls._monitoring_task is None or cls._monitoring_task.done():
            cls._monitoring_task = asyncio.ensure_future(cls._monitoring_loop())
            print("✅ Monitoring task created")

    @classmethod
    def stop_monitoring(cls):
        if cls._monitoring_task and not cls._monitoring_task.done():
            cls._monitoring_task.cancel()
            cls._monitoring_task = None
