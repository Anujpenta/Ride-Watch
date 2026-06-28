from fastapi import FastAPI, Depends, WebSocket
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, LocationRecord, Driver, Trip, init_db
import datetime
import asyncio
import time
from anomaly_detector import detect_anomalies
from lstm_model import train_model, predict_anomalies
from redis_client import publish_location
from ride_matching import sync_drivers_from_locations, find_nearest_idle_driver


app = FastAPI()

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open("templates/index.html", encoding="utf-8") as f:
        return f.read()

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

from prometheus_client import Counter, Histogram

anomalies_detected = Counter(
    "ridewatch_anomalies_detected_total",
    "Total anomalies detected",
    ["type"]
)

location_updates = Counter(
    "ridewatch_location_updates_total",
    "Total location updates received"
)

model_inference_time = Histogram(
    "ridewatch_model_inference_seconds",
    "Time taken for anomaly detection"
)

init_db()

class LocationUpdate(BaseModel):
    driver_id: str
    latitude: float
    longitude: float
    speed: float

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "RideWatch API is running"}

@app.post("/location")
def update_location(location: LocationUpdate, db: Session = Depends(get_db)):
    record = LocationRecord(
        driver_id=location.driver_id,
        latitude=location.latitude,
        longitude=location.longitude,
        speed=location.speed
    )
    db.add(record)
    db.commit()
    location_updates.inc()
    publish_location(location.driver_id, {
        "driver_id": location.driver_id,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "speed": location.speed
    })
    return {
        "status": "saved",
        "driver_id": location.driver_id,
        "coordinates": {
            "lat": location.latitude,
            "lng": location.longitude
        },
        "speed_kmh": location.speed
    }

@app.get("/locations")
def get_locations(db: Session = Depends(get_db)):
    records = db.query(LocationRecord).all()
    return records

@app.get("/locations/{driver_id}")
def get_driver_locations(driver_id: str, minutes: int = 10, db: Session = Depends(get_db)):
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)
    records = db.query(LocationRecord).filter(
        LocationRecord.driver_id == driver_id,
        LocationRecord.timestamp >= cutoff
    ).all()
    return {
        "driver_id": driver_id,
        "last_minutes": minutes,
        "total_updates": len(records),
        "locations": records
    }

@app.get("/anomalies/{driver_id}")
def get_anomalies(driver_id: str, minutes: int = 10, db: Session = Depends(get_db)):
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)
    records = db.query(LocationRecord).filter(
        LocationRecord.driver_id == driver_id,
        LocationRecord.timestamp >= cutoff
    ).order_by(LocationRecord.timestamp).all()

    locations = [
        {
            "id": r.id,
            "driver_id": r.driver_id,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "speed": r.speed,
            "timestamp": r.timestamp
        }
        for r in records
    ]

    start = time.time()
    anomalies = detect_anomalies(locations)
    model_inference_time.observe(time.time() - start)

    for a in anomalies:
        anomalies_detected.labels(type="rule_based").inc()

    return {
        "driver_id": driver_id,
        "records_analyzed": len(locations),
        "anomalies_found": len(anomalies),
        "anomalies": anomalies
    }

active_connections: list[WebSocket] = []

@app.websocket("/ws/driver/{driver_id}")
async def driver_websocket(websocket: WebSocket, driver_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    active_connections.append(websocket)
    print(f"Driver {driver_id} connected via WebSocket")

    try:
        while True:
            record = db.query(LocationRecord).filter(
                LocationRecord.driver_id == driver_id
            ).order_by(LocationRecord.id.desc()).first()

            if record:
                await websocket.send_json({
                    "driver_id": record.driver_id,
                    "latitude": record.latitude,
                    "longitude": record.longitude,
                    "speed": record.speed,
                    "timestamp": str(record.timestamp)
                })

            await asyncio.sleep(2)

    except Exception as e:
        print(f"Driver {driver_id} disconnected: {e}")
        active_connections.remove(websocket)

@app.post("/train/{driver_id}")
def train_driver_model(driver_id: str, db: Session = Depends(get_db)):
    records = db.query(LocationRecord).filter(
        LocationRecord.driver_id == driver_id
    ).order_by(LocationRecord.timestamp).all()

    locations = [
        {
            "id": r.id,
            "driver_id": r.driver_id,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "speed": r.speed,
            "timestamp": r.timestamp
        }
        for r in records
    ]

    model, scaler, message = train_model(locations)

    return {
        "driver_id": driver_id,
        "records_used": len(locations),
        "status": message
    }

@app.get("/anomalies/lstm/{driver_id}")
def get_lstm_anomalies(driver_id: str, minutes: int = 30, db: Session = Depends(get_db)):
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)
    records = db.query(LocationRecord).filter(
        LocationRecord.driver_id == driver_id,
        LocationRecord.timestamp >= cutoff
    ).order_by(LocationRecord.timestamp).all()

    locations = [
        {
            "id": r.id,
            "driver_id": r.driver_id,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "speed": r.speed,
            "timestamp": r.timestamp
        }
        for r in records
    ]

    anomalies, message = predict_anomalies(locations)

    return {
        "driver_id": driver_id,
        "records_analyzed": len(locations),
        "anomalies_found": len(anomalies),
        "message": message,
        "anomalies": anomalies
    }


class RideRequest(BaseModel):
    rider_id: str
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float

@app.post("/ride/request")
def request_ride(ride: RideRequest, db: Session = Depends(get_db)):
    sync_drivers_from_locations(db)

    result = find_nearest_idle_driver(db, ride.pickup_lat, ride.pickup_lng)

    if result is None or result[0] is None:
        return {"status": "no_drivers_available"}

    driver, distance_km = result

    trip = Trip(
        rider_id=ride.rider_id,
        driver_id=driver.driver_id,
        pickup_lat=ride.pickup_lat,
        pickup_lng=ride.pickup_lng,
        dropoff_lat=ride.dropoff_lat,
        dropoff_lng=ride.dropoff_lng,
        status="matched"
    )
    db.add(trip)

    driver.status = "en_route_to_pickup"

    db.commit()
    db.refresh(trip)

    return {
        "status": "matched",
        "trip_id": trip.id,
        "driver_id": driver.driver_id,
        "driver_distance_km": round(distance_km, 2),
        "driver_location": {
            "lat": driver.latitude,
            "lng": driver.longitude
        }
    }