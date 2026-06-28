import requests

def get_route_info(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
    """
    Fetch real driving distance (km) and duration (min) 
    between pickup and dropoff using OSRM, adjusted for realistic traffic.
    """
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{pickup_lng},{pickup_lat};{dropoff_lng},{dropoff_lat}"
        f"?overview=false"
    )

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data["code"] == "Ok":
            route = data["routes"][0]
            distance_km = route["distance"] / 1000

            # OSRM gives best-case duration with zero traffic.
            # Apply a realistic Hyderabad traffic multiplier.
            raw_duration_min = route["duration"] / 60
            TRAFFIC_MULTIPLIER = 1.8  # accounts for signals, congestion, traffic
            duration_min = raw_duration_min * TRAFFIC_MULTIPLIER

            return round(distance_km, 2), round(duration_min, 2)
        else:
            print(f"OSRM error: {data['code']}")
            return None, None
    except Exception as e:
        print(f"OSRM fetch failed: {e}")
        return None, None


def calculate_fare(distance_km, duration_min, surge_multiplier=1.0):
    BASE_FARE = 40
    PER_KM_RATE = 12
    PER_MIN_RATE = 1.5

    fare = BASE_FARE + (distance_km * PER_KM_RATE) + (duration_min * PER_MIN_RATE)
    fare = fare * surge_multiplier

    return round(fare, 2)