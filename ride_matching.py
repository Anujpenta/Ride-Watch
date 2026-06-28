import math
from sqlalchemy.orm import Session
from database import Driver, Trip, LocationRecord

def haversine_distance(lat1, lng1, lat2, lng2):
    """Calculate distance in km between two GPS points"""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def sync_drivers_from_locations(db: Session):
    """
    Update the drivers table using the latest location 
    from each driver in the locations table.
    This keeps driver positions fresh for matching.
    """
    driver_ids = db.query(LocationRecord.driver_id).distinct().all()
    
    for (driver_id,) in driver_ids:
        latest = db.query(LocationRecord).filter(
            LocationRecord.driver_id == driver_id
        ).order_by(LocationRecord.id.desc()).first()
        
        if not latest:
            continue
        
        driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
        
        if driver:
            driver.latitude = latest.latitude
            driver.longitude = latest.longitude
        else:
            driver = Driver(
                driver_id=driver_id,
                status="idle",
                latitude=latest.latitude,
                longitude=latest.longitude
            )
            db.add(driver)
    
    db.commit()

def find_nearest_idle_driver(db: Session, pickup_lat: float, pickup_lng: float):
    """Find the closest driver with status='idle'"""
    idle_drivers = db.query(Driver).filter(Driver.status == "idle").all()
    
    if not idle_drivers:
        return None
    
    nearest = None
    min_distance = float("inf")
    
    for driver in idle_drivers:
        if driver.latitude is None or driver.longitude is None:
            continue
        dist = haversine_distance(pickup_lat, pickup_lng, driver.latitude, driver.longitude)
        if dist < min_distance:
            min_distance = dist
            nearest = driver
    
    return nearest, min_distance if nearest else (None, None)