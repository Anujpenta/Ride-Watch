import requests
import time
import random

BASE_URL = "http://127.0.0.1:8000"

# Real Hyderabad coordinates - Hitec City to Charminar route
ROUTE = [
    {"lat": 17.4435, "lng": 78.3772},  # Hitec City
    {"lat": 17.4401, "lng": 78.3850},  # Madhapur
    {"lat": 17.4350, "lng": 78.3950},  # Jubilee Hills
    {"lat": 17.4200, "lng": 78.4100},  # Banjara Hills
    {"lat": 17.4050, "lng": 78.4200},  # Punjagutta
    {"lat": 17.3950, "lng": 78.4350},  # Begumpet
    {"lat": 17.3850, "lng": 78.4500},  # Secunderabad
    {"lat": 17.3750, "lng": 78.4600},  # Paradise
    {"lat": 17.3650, "lng": 78.4700},  # Musheerabad
    {"lat": 17.3600, "lng": 78.4750},  # Charminar
]

def simulate_driver(driver_id: str):
    print(f"Starting simulation for {driver_id}")
    print(f"Route: Hitec City → Charminar")
    print("-" * 40)

    step = 0
    while True:
        location = ROUTE[step % len(ROUTE)]
        speed = round(random.uniform(20, 60), 1)

        payload = {
            "driver_id": driver_id,
            "latitude": location["lat"] + random.uniform(-0.001, 0.001),
            "longitude": location["lng"] + random.uniform(-0.001, 0.001),
            "speed": speed
        }

        response = requests.post(f"{BASE_URL}/location", json=payload)

        if response.status_code == 200:
            print(f"[{driver_id}] Step {step + 1} → lat={payload['latitude']:.4f}, lng={payload['longitude']:.4f}, speed={speed} km/h ✓")
        else:
            print(f"Error: {response.status_code}")

        step += 1
        time.sleep(2)

if __name__ == "__main__":
    simulate_driver("driver_001")