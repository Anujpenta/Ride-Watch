import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def watch_driver(driver_id: str):
    channel = f"driver:{driver_id}"
    pubsub = r.pubsub()
    pubsub.subscribe(channel)

    print(f"Subscribed to channel: {channel}")
    print(f"Watching {driver_id} via Redis pub/sub...\n")

    for message in pubsub.listen():
        if message["type"] == "message":
            location = json.loads(message["data"])
            print(f"REDIS → driver={location['driver_id']} | "
                  f"lat={location['latitude']:.4f}, "
                  f"lng={location['longitude']:.4f}, "
                  f"speed={location['speed']} km/h")

if __name__ == "__main__":
    watch_driver("driver_001")