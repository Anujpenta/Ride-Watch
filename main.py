from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, LocationRecord, init_db
import datetime
from anomaly_detector import detect_anomalies
from fastapi import WebSocket
import asyncio

app = FastAPI()

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

    anomalies = detect_anomalies(locations)

    return {
        "driver_id": driver_id,
        "records_analyzed": len(locations),
        "anomalies_found": len(anomalies),
        "anomalies": anomalies
    }

# Store connected riders
active_connections: list[WebSocket] = []

@app.websocket("/ws/driver/{driver_id}")
async def driver_websocket(websocket: WebSocket, driver_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    active_connections.append(websocket)
    print(f"Driver {driver_id} connected via WebSocket")
    
    try:
        while True:
            # Get latest location from database
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