from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Exercise


EXERCISE_LIBRARY = [
    {
        "slug": "wrist_extension",
        "title": "Wrist Extension",
        "what_it_is": "A gentle wrist stretch that helps open the hand after gripping or resting.",
        "how_to_do_it": "Rest your forearm on a table with your hand just beyond the edge.\nSlowly lift the back of your hand, keeping your forearm still.\nLower to neutral and repeat without forcing the movement.",
        "why_it_helps": "This motion supports better hand positioning and helps with daily tasks that need a more open wrist.",
    },
    {
        "slug": "grip_rehab",
        "title": "Grip Rehab",
        "what_it_is": "A simple squeeze exercise that trains the hand to close and release.",
        "how_to_do_it": "Place a soft object in your palm and keep your wrist relaxed.\nGently squeeze, then hold for a comfortable moment.\nRelease slowly and let your fingers open before repeating.",
        "why_it_helps": "It keeps the hand moving and can improve control during everyday gripping tasks.",
    },
    {
        "slug": "finger_release",
        "title": "Finger Release",
        "what_it_is": "A controlled release pattern to help the hand open after closing.",
        "how_to_do_it": "Begin with your hand relaxed and supported.\nOpen your fingers one at a time, moving at a comfortable pace.\nPause with your hand open, then relax before repeating.",
        "why_it_helps": "This encourages smoother hand opening and reduces tightness after repetitive tasks.",
    },
]


def seed_exercises():
    db: Session = SessionLocal()
    try:
        for item in EXERCISE_LIBRARY:
            existing = db.query(Exercise).filter(Exercise.slug == item["slug"]).first()
            if not existing:
                db.add(Exercise(**item))
            else:
                existing.how_to_do_it = item["how_to_do_it"]
        db.commit()
    finally:
        db.close()
