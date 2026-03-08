import asyncio
import json
import time
from paho.mqtt import client as mqtt_client
from datetime import datetime

# MQTT Broker Configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_TEMP = "superworms-2025/device1/temp"
TOPIC_HUM  = "superworms-2025/device1/humidity"
CLIENT_ID  = "fastapi_larvae_monitor_98765"


class MQTTService:
    """Manages MQTT connection and sensor data from ESP32/DHT22"""

    sensor_data = {
        "temperature": "--",
        "humidity":    "--",
        "last_update": 0
    }

    active_sensor_ws = set()

    _mqtt_client  = None
    _loop         = None
    _timeout_task = None

    @classmethod
    def get_sensor_data(cls):
        return {
            "temperature": cls.sensor_data["temperature"],
            "humidity":    cls.sensor_data["humidity"],
        }

    @classmethod
    def _on_connect(cls, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to MQTT Broker ({BROKER})")
            client.subscribe(TOPIC_TEMP)
            client.subscribe(TOPIC_HUM)
            print(f"📡 Subscribed to {TOPIC_TEMP} and {TOPIC_HUM}")
        else:
            print(f"❌ MQTT connection failed, return code {rc}")

    @classmethod
    def _on_message(cls, client, userdata, msg):
        topic   = msg.topic
        payload = msg.payload.decode("utf-8")

        print(f"📩 MQTT received [{topic}]: {payload}")  # ← debug log

        # Always update, always broadcast — same as working code
        if topic == TOPIC_TEMP:
            cls.sensor_data["temperature"] = payload
        elif topic == TOPIC_HUM:
            cls.sensor_data["humidity"] = payload
        else:
            return  # unknown topic, skip

        cls.sensor_data["last_update"] = time.time()

        # Broadcast to all WS clients (thread-safe)
        if cls._loop is not None:
            asyncio.run_coroutine_threadsafe(
                cls.broadcast_sensor_data(), cls._loop
            )

    @classmethod
    async def broadcast_sensor_data(cls):
        message = json.dumps({
            "temperature": cls.sensor_data["temperature"],
            "humidity":    cls.sensor_data["humidity"],
            "timestamp":   datetime.now().isoformat()
        })

        dead = set()
        for ws in list(cls.active_sensor_ws):
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)

        for ws in dead:
            cls.active_sensor_ws.discard(ws)

    @classmethod
    async def _check_sensor_timeout(cls):
        """Reset to '--' if no MQTT data for 10 seconds"""
        while True:
            await asyncio.sleep(2)
            if time.time() - cls.sensor_data["last_update"] > 60.0:
                if cls.sensor_data["temperature"] != "--" or cls.sensor_data["humidity"] != "--":
                    cls.sensor_data["temperature"] = "--"
                    cls.sensor_data["humidity"]    = "--"
                    await cls.broadcast_sensor_data()

    @classmethod
    def start(cls, loop: asyncio.AbstractEventLoop):
        cls._loop = loop

        # Start timeout checker as asyncio task
        cls._timeout_task = asyncio.ensure_future(
            cls._check_sensor_timeout(), loop=loop
        )

        # Connect MQTT
        client = mqtt_client.Client(
            mqtt_client.CallbackAPIVersion.VERSION1, CLIENT_ID
        )
        client.on_connect = cls._on_connect
        client.on_message = cls._on_message
        client.connect(BROKER, PORT)
        client.loop_start()
        cls._mqtt_client = client

        print("🚀 MQTT Service started")

    @classmethod
    def stop(cls):
        if cls._timeout_task:
            cls._timeout_task.cancel()
        if cls._mqtt_client:
            cls._mqtt_client.loop_stop()
            cls._mqtt_client.disconnect()
        print("🛑 MQTT Service stopped")