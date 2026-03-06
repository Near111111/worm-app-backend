import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.mqtt_service import MQTTService

router = APIRouter()


@router.websocket("/ws/sensors")
async def sensor_ws(websocket: WebSocket):
    """
    WebSocket endpoint for real-time sensor data.
    Frontend connects here to get live temperature/humidity updates.
    
    JSON format sent to frontend:
    {
        "temperature": "32.5",
        "humidity": "65.2",
        "timestamp": "2025-01-15T14:30:00.123456"
    }
    
    When ESP32 is disconnected or no data for 10s:
    {
        "temperature": "--",
        "humidity": "--",
        "timestamp": "..."
    }
    """
    await websocket.accept()
    client_host = websocket.client.host if websocket.client else "unknown"
    print(f"📡 Sensor WS client connected from {client_host}")

    # Register this websocket to receive broadcasts
    MQTTService.active_sensor_ws.add(websocket)

    try:
        # Send current data immediately on connect
        from datetime import datetime
        current = MQTTService.get_sensor_data()
        current["timestamp"] = datetime.now().isoformat()
        await websocket.send_text(json.dumps(current))

        # Keep connection alive — listen for client messages (ping/pong)
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        print(f"🔴 Sensor WS client disconnected: {client_host}")
    except Exception as e:
        print(f"❌ Sensor WS error for {client_host}: {e}")
    finally:
        MQTTService.active_sensor_ws.discard(websocket)