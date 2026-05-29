import requests
import time
import random
import threading
import os

BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

WAYPOINTS = {
    "driver_001": [
        {"lat": 17.4435, "lng": 78.3772},  # Hitec City
        {"lat": 17.4200, "lng": 78.4100},  # Banjara Hills
        {"lat": 17.3950, "lng": 78.4350},  # Begumpet
        {"lat": 17.3750, "lng": 78.4600},  # Paradise
        {"lat": 17.3600, "lng": 78.4750},  # Charminar
    ],
    "driver_002": [
        {"lat": 17.3850, "lng": 78.4867},  # Charminar area
        {"lat": 17.4050, "lng": 78.4650},  # Nampally
        {"lat": 17.4250, "lng": 78.4450},  # Khairatabad
        {"lat": 17.4450, "lng": 78.4250},  # SR Nagar
        {"lat": 17.4750, "lng": 78.3950},  # Miyapur
    ],
    "driver_003": [
        {"lat": 17.3616, "lng": 78.4747},  # Old City
        {"lat": 17.3900, "lng": 78.5000},  # Dilsukhnagar
        {"lat": 17.4100, "lng": 78.5200},  # Uppal
        {"lat": 17.4400, "lng": 78.5100},  # Habsiguda
        {"lat": 17.4500, "lng": 78.5000},  # Tarnaka
    ],
}

def get_road_route(waypoints):
    coords = ";".join([f"{p['lng']},{p['lat']}" for p in waypoints])
    url = f"http://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson&steps=false"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data["code"] == "Ok":
            coordinates = data["routes"][0]["geometry"]["coordinates"]
            route = [{"lat": c[1], "lng": c[0]} for c in coordinates]
            print(f"Got {len(route)} road points from OSRM")
            return route
        else:
            print(f"OSRM error: {data['code']}")
            return waypoints
    except Exception as e:
        print(f"OSRM fetch failed: {e}, using straight line")
        return waypoints

def simulate_driver(driver_id: str):
    waypoints = WAYPOINTS[driver_id]
    
    print(f"[{driver_id}] Fetching road route from OSRM...")
    route = get_road_route(waypoints)
    print(f"[{driver_id}] Route ready with {len(route)} points")
    
    step = 0
    direction = 1

    while True:
        location = route[step]
        speed = round(random.uniform(20, 50), 1)

        payload = {
            "driver_id": driver_id,
            "latitude": location["lat"] + random.uniform(-0.0002, 0.0002),
            "longitude": location["lng"] + random.uniform(-0.0002, 0.0002),
            "speed": speed
        }

        try:
            response = requests.post(f"{BASE_URL}/location", json=payload)
            if response.status_code == 200:
                print(f"[{driver_id}] Step {step + 1}/{len(route)} → lat={payload['latitude']:.4f}, lng={payload['longitude']:.4f}, speed={speed} km/h ✓")
            else:
                print(f"[{driver_id}] Error: {response.status_code}")
        except Exception as e:
            print(f"[{driver_id}] Connection error: {e}")
            time.sleep(5)
            continue

        step += direction
        if step >= len(route) - 1:
            direction = -1  # reached end, reverse
        elif step <= 0:
            direction = 1   # reached start, go forward

        time.sleep(0.8)

if __name__ == "__main__":
    threads = []
    for driver_id in WAYPOINTS.keys():
        t = threading.Thread(target=simulate_driver, args=(driver_id,))
        t.daemon = True
        threads.append(t)
        t.start()
        time.sleep(1)

    print("All 3 drivers running on real Hyderabad roads...")
    for t in threads:
        t.join()