import asyncio
import websockets
import json

async def watch_driver():
    url = "ws://127.0.0.1:8000/ws/driver/driver_001"
    print("Connecting to RideWatch WebSocket...")
    print("Watching driver_001 in real time...\n")
    
    async with websockets.connect(url) as ws:
        while True:
            data = await ws.recv()
            location = json.loads(data)
            print(f"LIVE → lat={location['latitude']:.4f}, "
                  f"lng={location['longitude']:.4f}, "
                  f"speed={location['speed']} km/h | "
                  f"{location['timestamp']}")

asyncio.run(watch_driver())