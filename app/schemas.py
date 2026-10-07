from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessionIn(BaseModel):
    device_id: str
    patient_id: str = "usr_9876"
    session_type: str
    duration_seconds: int
    switch_activations: int = Field(default=0)
    successful_reps: int = Field(default=0)
    max_force_n: float = Field(default=0.0)
    timestamp: datetime


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    device_id: str
    patient_id: str
    session_type: str
    duration_seconds: int
    switch_activations: int
    successful_reps: int
    max_force_n: float
    timestamp: datetime
