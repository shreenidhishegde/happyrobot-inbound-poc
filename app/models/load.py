from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class Load(Base):
    __tablename__ = "loads"

    load_id = Column(Integer, primary_key=True, index=True)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    pickup_datetime = Column(DateTime, nullable=False)
    delivery_datetime = Column(DateTime, nullable=False)
    equipment_type = Column(String, nullable=False)
    loadboard_rate = Column(Float, nullable=False)
    notes = Column(String, nullable=True)
    weight = Column(Integer, nullable=False)
    commodity_type = Column(String, nullable=False)
    num_of_pieces = Column(Integer, nullable=True)
    miles = Column(Integer, nullable=True)
    dimensions = Column(String, nullable=True)
    status = Column(String, default="available")


class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    mc_number = Column(String, index=True)
    carrier_name = Column(String, index=True)
    load_id = Column(String, index=True)
    call_outcome = Column(String, index=True)  
    sentiment = Column(String, index=True)     
    call_summary = Column(Text)
    duration = Column(Integer) 
    created_at = Column(DateTime, default=func.now())


