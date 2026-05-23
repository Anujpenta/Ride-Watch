from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime

DATABASE_URL = "postgresql://ridewatch:ridewatch123@localhost:5432/ridewatch"

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

def init_db():
    Base.metadata.create_all(bind=engine)