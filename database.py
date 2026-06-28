from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ridewatch:ridewatch123@localhost:5432/ridewatch"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class LocationRecord(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    speed = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(String, unique=True, index=True)
    status = Column(String, default="idle")  # idle, en_route_to_pickup, on_trip
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rider_id = Column(String, index=True)
    driver_id = Column(String, index=True, nullable=True)
    pickup_lat = Column(Float)
    pickup_lng = Column(Float)
    dropoff_lat = Column(Float)
    dropoff_lng = Column(Float)
    distance_km = Column(Float, nullable=True)
    duration_min = Column(Float, nullable=True)
    fare = Column(Float, nullable=True)
    status = Column(String, default="requested")  # requested, matched, in_progress, completed, cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)