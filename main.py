from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, LocationRecord, init_db
import datetime

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