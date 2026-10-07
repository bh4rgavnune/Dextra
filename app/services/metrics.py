from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import SessionRecord


def calculate_success_rate(switch_activations: int, successful_reps: int) -> float:
    if switch_activations == 0:
        return 0.0
    return float(successful_reps / switch_activations)


def calculate_day_streak(db: Session, patient_id: str, today: datetime | None = None) -> int:
    if today is None:
        today = datetime.now(timezone.utc).date()
    else:
        today = today.date() if isinstance(today, datetime) else today

    streak = 0
    cursor = today
    while True:
        exists = (
            db.query(SessionRecord.id)
            .filter(SessionRecord.patient_id == patient_id)
            .filter(SessionRecord.timestamp >= datetime.combine(cursor, datetime.min.time()))
            .filter(SessionRecord.timestamp < datetime.combine(cursor + timedelta(days=1), datetime.min.time()))
            .first()
        )
        if not exists:
            break
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def calculate_weekly_trend(db: Session, patient_id: str, days: int = 7):
    end = datetime.now(timezone.utc).date()
    labels = []
    values = []
    for offset in range(days - 1, -1, -1):
        day = end - timedelta(days=offset)
        labels.append(day.strftime("%a"))
        total = (
            db.query(SessionRecord.successful_reps)
            .filter(SessionRecord.patient_id == patient_id)
            .filter(SessionRecord.timestamp >= datetime.combine(day, datetime.min.time()))
            .filter(SessionRecord.timestamp < datetime.combine(day + timedelta(days=1), datetime.min.time()))
            .all()
        )
        values.append(sum(rep for (rep,) in total))
    return {"labels": labels, "values": values}


def get_dashboard_stats(db: Session, patient_id: str):
    sessions = db.query(SessionRecord).filter(SessionRecord.patient_id == patient_id).all()
    total_reps = sum(session.successful_reps for session in sessions)
    avg_duration = round(sum(session.duration_seconds for session in sessions) / len(sessions), 1) if sessions else 0.0
    streak = calculate_day_streak(db, patient_id)
    weekly = calculate_weekly_trend(db, patient_id)
    success_rates = [calculate_success_rate(s.switch_activations, s.successful_reps) for s in sessions]
    avg_success = round(sum(success_rates) / len(success_rates), 2) if success_rates else 0.0
    return {
        "total_sessions": len(sessions),
        "total_reps": total_reps,
        "avg_duration": avg_duration,
        "day_streak": streak,
        "avg_success_rate": avg_success,
        "weekly_trend": weekly,
    }
