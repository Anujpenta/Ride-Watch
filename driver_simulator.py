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
        {"lat": 17.3800, "lng": 78.4900},  # Dilsukhnagar
        {"lat": 17.4000, "lng": 78.5100},  # Uppal
        {"lat": 17.4300, "lng": 78.4800},  # Tarnaka
        {"lat": 17.4500, "lng": 78.4300},  # Secunderabad
        {"lat": 17.4435, "lng": 78.3772},  # Back to Hitec City
    ],
    "driver_002": [
        {"lat": 17.3850, "lng": 78.4867},  # Charminar
        {"lat": 17.4050, "lng": 78.4650},  # Nampally
        {"lat": 17.4250, "lng": 78.4450},  # Khairatabad
        {"lat": 17.4450, "lng": 78.4250},  # SR Nagar
        {"lat": 17.4750, "lng": 78.3950},  # Miyapur
        {"lat": 17.4600, "lng": 78.3800},  # BHEL
        {"lat": 17.4400, "lng": 78.3700},  # Gachibowli
        {"lat": 17.4200, "lng": 78.3900},  # Financial District
        {"lat": 17.4000, "lng": 78.4200},  # Tolichowki
        {"lat": 17.3850, "lng": 78.4867},  # Back to Charminar
    ],
    "driver_003": [
        {"lat": 17.3616, "lng": 78.4747},  # Old City
        {"lat": 17.3900, "lng": 78.5000},  # Dilsukhnagar
        {"lat": 17.4100, "lng": 78.5200},  # Uppal
        {"lat": 17.4400, "lng": 78.5100},  # Habsiguda
        {"lat": 17.4600, "lng": 78.4900},  # Tarnaka
        {"lat": 17.4700, "lng": 78.4600},  # Malkajgiri
        {"lat": 17.4500, "lng": 78.4300},  # Secunderabad
        {"lat": 17.4200, "lng": 78.4500},  # Somajiguda
        {"lat": 17.3900, "lng": 78.4600},  # Abids
        {"lat": 17.3616, "lng": 78.4747},  # Back to Old City
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


def find_nearest_step(loop_route, current_lat, current_lng):
    """Find the closest point in the loop to resume from."""
    min_dist = float("inf")
    nearest_step = 0
    for i, point in enumerate(loop_route):
        dist = ((point["lat"] - current_lat) ** 2 + (point["lng"] - current_lng) ** 2) ** 0.5
        if dist < min_dist:
            min_dist = dist
            nearest_step = i
    return nearest_step


def check_destination(driver_id):
    try:
        response = requests.get(f"{BASE_URL}/driver/destination/{driver_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"[{driver_id}] Destination check failed: {e}")
    return {"has_destination": False}


def notify_arrival(driver_id, trip_id):
    try:
        response = requests.post(f"{BASE_URL}/trip/arrive/{trip_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[{driver_id}] Arrival notified → {data['status']}")
            return data
    except Exception as e:
        print(f"[{driver_id}] Arrival notification failed: {e}")
    return None


def simulate_driver(driver_id: str):
    waypoints = WAYPOINTS[driver_id]

    print(f"[{driver_id}] Fetching road route from OSRM...")
    loop_route = get_road_route(waypoints)
    print(f"[{driver_id}] Route ready with {len(loop_route)} points")

    step = 0
    current_lat = loop_route[0]["lat"]
    current_lng = loop_route[0]["lng"]

    diversion_route = None
    diversion_step = 0
    active_dest = None
    active_trip_id = None
    check_counter = 0
    returning_to_loop = False  # True when routing back to loop after trip

    while True:
        check_counter += 1
        use_loop = False
        location = None

        # --- RETURNING TO LOOP MODE ---
        # After trip completes, driver routes back to loop via real roads
        if returning_to_loop:
            if diversion_route and diversion_step < len(diversion_route):
                location = diversion_route[diversion_step]
                diversion_step += 1
            else:
                # Reached loop re-entry point — resume normal loop
                print(f"[{driver_id}] Back on normal loop route!")
                returning_to_loop = False
                diversion_route = None
                diversion_step = 0
                use_loop = True

        # --- NORMAL / TRIP MODE ---
        else:
            # Poll API every 3rd cycle, reuse known state otherwise
            if check_counter % 3 == 0:
                dest_info = check_destination(driver_id)
            else:
                has_dest = active_dest is not None
                dest_info = {"has_destination": has_dest}
                if has_dest:
                    dest_info["dest_lat"] = active_dest[0]
                    dest_info["dest_lng"] = active_dest[1]
                    dest_info["trip_id"] = active_trip_id

            if dest_info.get("has_destination"):
                dest_lat = dest_info["dest_lat"]
                dest_lng = dest_info["dest_lng"]
                trip_id = dest_info.get("trip_id")

                # New destination detected — compute fresh OSRM route
                if active_dest != (dest_lat, dest_lng):
                    active_dest = (dest_lat, dest_lng)
                    active_trip_id = trip_id
                    print(f"[{driver_id}] New destination (trip {trip_id}), routing there...")
                    diversion_route = get_road_route([
                        {"lat": current_lat, "lng": current_lng},
                        {"lat": dest_lat, "lng": dest_lng}
                    ])
                    diversion_step = 0

                if diversion_route and diversion_step < len(diversion_route):
                    # Still on the way to destination
                    location = diversion_route[diversion_step]
                    diversion_step += 1

                else:
                    # Reached destination — notify API
                    if active_trip_id is not None:
                        result = notify_arrival(driver_id, active_trip_id)

                        if result and result.get("status") == "in_progress":
                            # Arrived at PICKUP → API has now set dest to dropoff
                            # Reset so next check picks up dropoff destination smoothly
                            print(f"[{driver_id}] Pickup reached! Now routing to dropoff...")
                            active_dest = None
                            active_trip_id = None
                            diversion_route = None
                            diversion_step = 0
                            check_counter = 2  # next cycle: 3 % 3 == 0 → immediate fresh check
                            location = {"lat": current_lat, "lng": current_lng}

                        elif result and result.get("status") == "completed":
                            # Arrived at DROPOFF → route back to loop via real roads
                            print(f"[{driver_id}] Trip completed! Routing back to loop via roads...")
                            nearest = find_nearest_step(loop_route, current_lat, current_lng)
                            nearest_point = loop_route[nearest]
                            diversion_route = get_road_route([
                                {"lat": current_lat, "lng": current_lng},
                                {"lat": nearest_point["lat"], "lng": nearest_point["lng"]}
                            ])
                            diversion_step = 0
                            step = nearest
                            active_dest = None
                            active_trip_id = None
                            returning_to_loop = True
                            location = {"lat": current_lat, "lng": current_lng}

                        else:
                            # Unexpected — just resume loop
                            active_dest = None
                            active_trip_id = None
                            diversion_route = None
                            diversion_step = 0
                            check_counter = 0
                            use_loop = True

                    else:
                        # No trip ID — resume loop
                        active_dest = None
                        diversion_route = None
                        diversion_step = 0
                        use_loop = True

            else:
                # No destination — normal loop
                if active_dest is not None:
                    # Was on a trip but destination cleared unexpectedly
                    print(f"[{driver_id}] Destination cleared, routing back to loop...")
                    nearest = find_nearest_step(loop_route, current_lat, current_lng)
                    nearest_point = loop_route[nearest]
                    diversion_route = get_road_route([
                        {"lat": current_lat, "lng": current_lng},
                        {"lat": nearest_point["lat"], "lng": nearest_point["lng"]}
                    ])
                    diversion_step = 0
                    step = nearest
                    active_dest = None
                    active_trip_id = None
                    returning_to_loop = True
                    location = {"lat": current_lat, "lng": current_lng}
                else:
                    active_dest = None
                    active_trip_id = None
                    diversion_route = None
                    diversion_step = 0
                    use_loop = True

        if use_loop:
            location = loop_route[step % len(loop_route)]
            step += 1

        if location is None:
            location = loop_route[step % len(loop_route)]
            step += 1

        current_lat = location["lat"]
        current_lng = location["lng"]
        speed = round(random.uniform(20, 50), 1)

        payload = {
            "driver_id": driver_id,
            "latitude": current_lat + random.uniform(-0.0002, 0.0002),
            "longitude": current_lng + random.uniform(-0.0002, 0.0002),
            "speed": speed
        }

        try:
            response = requests.post(f"{BASE_URL}/location", json=payload, timeout=5)
            if response.status_code != 200:
                print(f"[{driver_id}] Error: {response.status_code}")
        except Exception as e:
            print(f"[{driver_id}] Connection error: {e}")
            time.sleep(5)
            continue

        time.sleep(0.8)


if __name__ == "__main__":
    threads = []
    for driver_id in WAYPOINTS.keys():
        t = threading.Thread(target=simulate_driver, args=(driver_id,))
        t.daemon = True
        threads.append(t)
        t.start()
        time.sleep(1)

    print("All 3 drivers running with automatic trip lifecycle...")
    for t in threads:
        t.join()