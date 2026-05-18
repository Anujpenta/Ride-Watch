def detect_anomalies(locations: list) -> list:
    anomalies = []

    if len(locations) < 2:
        return anomalies

    for i in range(1, len(locations)):
        current = locations[i]
        previous = locations[i - 1]

        flags = []

        # Rule 1: Speed spike — sudden jump over 80 km/h
        if current["speed"] > 80:
            flags.append({
                "type": "speed_spike",
                "detail": f"Speed {current['speed']} km/h exceeds limit"
            })

        # Rule 2: Sudden speed change — jumped more than 40 km/h instantly
        speed_change = abs(current["speed"] - previous["speed"])
        if speed_change > 40:
            flags.append({
                "type": "erratic_speed",
                "detail": f"Speed changed by {round(speed_change, 1)} km/h instantly"
            })

        # Rule 3: GPS jump — location teleported unrealistically
        lat_jump = abs(current["latitude"] - previous["latitude"])
        lng_jump = abs(current["longitude"] - previous["longitude"])
        if lat_jump > 0.05 or lng_jump > 0.05:
            flags.append({
                "type": "gps_jump",
                "detail": f"Location jumped {round(lat_jump + lng_jump, 4)} degrees instantly"
            })

        if flags:
            anomalies.append({
                "record_id": current["id"],
                "driver_id": current["driver_id"],
                "timestamp": str(current["timestamp"]),
                "latitude": current["latitude"],
                "longitude": current["longitude"],
                "speed": current["speed"],
                "anomalies": flags
            })

    return anomalies