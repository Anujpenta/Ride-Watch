import redis
import json
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

r = redis.from_url(REDIS_URL, decode_responses=True)

def publish_location(driver_id: str, location: dict):
    channel = f"driver:{driver_id}"
    r.publish(channel, json.dumps(location))

def get_redis():
    return r