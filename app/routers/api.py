from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SessionRecord
from app.schemas import SessionIn, SessionOut

router = APIRouter()


@router.post("/api/ingest", response_model=SessionOut)
def ingest_session(payload: SessionIn, db: Session = Depends(get_db)):
    session_data = payload.model_dump()
    session_data["patient_id"] = "usr_9876"
    if isinstance(session_data["timestamp"], str):
        session_data["timestamp"] = datetime.fromisoformat(session_data["timestamp"].replace("Z", "+00:00"))

    session = SessionRecord(**session_data)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
