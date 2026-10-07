from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import SessionRecord


def get_achievements(db: Session, patient_id: str):
    sessions = db.query(SessionRecord).filter(SessionRecord.patient_id == patient_id).all()
    sessions.sort(key=lambda session: (session.timestamp.replace(tzinfo=timezone.utc) if session.timestamp.tzinfo is None else session.timestamp.astimezone(timezone.utc), session.id))
    total_reps = sum(session.successful_reps or 0 for session in sessions)
    session_days = sorted(
        {
            (session.timestamp.replace(tzinfo=timezone.utc) if session.timestamp.tzinfo is None else session.timestamp.astimezone(timezone.utc)).date()
            for session in sessions
        }
    )
    today = datetime.now(timezone.utc).date()
    cursor = today
    streak = 0
    while cursor in session_days:
        streak += 1
        cursor -= timedelta(days=1)

    streak_unlocked_at = next(
        (day for previous, day in zip(session_days, session_days[1:]) if day - previous == timedelta(days=1)),
        None,
    )
    reps_unlocked_at = None
    reps_so_far = 0
    for session in sessions:
        reps_so_far += session.successful_reps or 0
        if reps_so_far >= 50:
            reps_unlocked_at = session.timestamp
            break

    achievements = [
        {
            "title": "First Rep",
            "description": "Logged your first rehab session.",
            "emoji": "🌱",
            "unlocked": len(sessions) >= 1,
            "unlocked_at": sessions[0].timestamp.date() if sessions else None,
            "progress": min(len(sessions), 1),
            "progress_target": 1,
        },
        {
            "title": "Dedicated",
            "description": "Reached a 2-day streak.",
            "emoji": "📅",
            "unlocked": streak_unlocked_at is not None,
            "unlocked_at": streak_unlocked_at,
            "progress": min(streak, 2),
            "progress_target": 2,
        },
        {
            "title": "Power User",
            "description": "Hit 50 successful reps total.",
            "emoji": "🏆",
            "unlocked": total_reps >= 50,
            "unlocked_at": reps_unlocked_at.date() if reps_unlocked_at else None,
            "progress": min(total_reps, 50),
            "progress_target": 50,
        },
    ]
    return achievements
