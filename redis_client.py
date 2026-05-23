import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def publish_location(driver_id: str, location: dict):
    channel = f"driver:{driver_id}"
    r.publish(channel, json.dumps(location))

def get_redis():
    return r