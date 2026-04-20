from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, LocationRecord, init_db

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