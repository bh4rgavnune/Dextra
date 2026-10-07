from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database import Base


class SessionRecord(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, nullable=False)
    patient_id = Column(String, nullable=False, index=True)
    session_type = Column(String, nullable=False)
    duration_seconds = Column(Integer, default=0)
    switch_activations = Column(Integer, default=0)
    successful_reps = Column(Integer, default=0)
    max_force_n = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    what_it_is = Column(String, nullable=False)
    how_to_do_it = Column(String, nullable=False)
    why_it_helps = Column(String, nullable=False)
