import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Exercise, SessionRecord
from app.services.achievements import get_achievements
from app.services import metrics


def test_metrics_handles_zero_switch_activations():
    assert metrics.calculate_success_rate(0, 10) == 0.0


def test_achievements_include_unlock_dates_and_locked_progress():
    patient_id = f"achievement_test_{uuid4().hex}"
    historical_patient_id = f"achievement_history_test_{uuid4().hex}"
    timestamp = datetime.now(timezone.utc)
    db = SessionLocal()
    db.add_all(
        [
            SessionRecord(
                device_id="achievement_test_device",
                patient_id=patient_id,
                session_type="wrist_extension",
                duration_seconds=60,
                switch_activations=4,
                successful_reps=12,
                max_force_n=1.0,
                timestamp=timestamp,
            ),
            *[
                SessionRecord(
                    device_id="achievement_test_device",
                    patient_id=historical_patient_id,
                    session_type="wrist_extension",
                    duration_seconds=60,
                    switch_activations=4,
                    successful_reps=4,
                    max_force_n=1.0,
                    timestamp=timestamp - timedelta(days=days_ago),
                )
                for days_ago in (4, 3)
            ],
        ]
    )
    db.commit()
    try:
        achievements = get_achievements(db, patient_id)
        assert achievements[0]["unlocked"]
        assert achievements[0]["unlocked_at"] == timestamp.date()
        assert achievements[1]["progress"] == 1
        assert achievements[2]["progress"] == 12
        assert achievements[2]["progress_target"] == 50
        historical_achievements = get_achievements(db, historical_patient_id)
        assert historical_achievements[1]["unlocked"]
        assert historical_achievements[1]["unlocked_at"] == (timestamp - timedelta(days=3)).date()
    finally:
        db.query(SessionRecord).filter(
            SessionRecord.patient_id.in_([patient_id, historical_patient_id])
        ).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_dashboard_route_returns_200():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_exercise_pages_show_patient_stats_and_link_sessions():
    slug = f"exercise_route_test_{uuid4().hex}"
    db = SessionLocal()
    db.add(
        Exercise(
            slug=slug,
            title="Exercise Route Test",
            what_it_is="A test movement.",
            how_to_do_it="First step.\nSecond step.",
            why_it_helps="It helps verify this page.",
        )
    )
    db.add_all(
        [
            SessionRecord(
                device_id="exercise_route_test_device",
                patient_id="usr_9876",
                session_type=slug,
                duration_seconds=60,
                switch_activations=4,
                successful_reps=3,
                max_force_n=1.0,
                timestamp=datetime.now(timezone.utc),
            ),
            SessionRecord(
                device_id="exercise_route_test_device",
                patient_id="usr_9876",
                session_type=slug,
                duration_seconds=60,
                switch_activations=2,
                successful_reps=1,
                max_force_n=1.0,
                timestamp=datetime.now(timezone.utc),
            ),
            SessionRecord(
                device_id="exercise_route_test_device",
                patient_id="another_patient",
                session_type=slug,
                duration_seconds=60,
                switch_activations=1,
                successful_reps=0,
                max_force_n=1.0,
                timestamp=datetime.now(timezone.utc),
            ),
        ]
    )
    db.commit()
    db.close()

    try:
        client = TestClient(app)
        library = client.get("/exercises")
        detail = client.get(f"/exercises/{slug}")
        dashboard = client.get("/")
        history = client.get("/history", params={"session_type": slug})

        assert library.status_code == 200
        assert f"/exercises/{slug}" in library.text
        assert detail.status_code == 200
        assert "Your stats for this exercise" in detail.text
        assert ">2</strong>" in detail.text
        assert ">67%</strong>" in detail.text
        assert "First step." in detail.text and "Second step." in detail.text
        assert "Stop if you feel pain and consult your therapist." in detail.text
        assert f"/exercises/{slug}" in dashboard.text
        assert f"/exercises/{slug}" in history.text
    finally:
        db = SessionLocal()
        db.query(SessionRecord).filter(SessionRecord.session_type == slug).delete(synchronize_session=False)
        db.query(Exercise).filter(Exercise.slug == slug).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_ingest_route_accepts_payload_and_forces_demo_patient():
    client = TestClient(app)
    payload = {
        "device_id": "DEXTRA_ESP_01",
        "patient_id": "other_user",
        "session_type": "wrist_extension",
        "duration_seconds": 180,
        "switch_activations": 12,
        "successful_reps": 10,
        "max_force_n": 15.2,
        "timestamp": "2026-10-07T17:30:00Z",
    }
    response = client.post("/api/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "usr_9876"
    assert data["session_type"] == "wrist_extension"


def test_dashboard_partials_reflect_new_ingested_session():
    client = TestClient(app)
    before_stats = client.get("/partials/stats").text
    before_recent = client.get("/partials/recent").text
    before_count = int(re.search(r'data-total-sessions="(\d+)"', before_stats).group(1))
    before_latest_id = re.search(r'data-latest-session-id="(\d*)"', before_recent).group(1)

    response = client.post(
        "/api/ingest",
        json={
            "device_id": "DEXTRA_ESP_01",
            "patient_id": "usr_9876",
            "session_type": "live_refresh_test",
            "duration_seconds": 75,
            "switch_activations": 8,
            "successful_reps": 6,
            "max_force_n": 9.1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert response.status_code == 200

    after_stats = client.get("/partials/stats").text
    after_recent = client.get("/partials/recent").text
    after_count = int(re.search(r'data-total-sessions="(\d+)"', after_stats).group(1))
    after_latest_id = re.search(r'data-latest-session-id="(\d*)"', after_recent).group(1)

    assert after_count == before_count + 1
    assert after_latest_id != before_latest_id
    assert "Live Refresh Test" in after_recent


def test_history_paginates_and_returns_only_the_table_body_for_htmx():
    session_type = f"history_test_{uuid4().hex}"
    db = SessionLocal()
    db.add_all(
        [
            SessionRecord(
                device_id="history_test_device",
                patient_id="usr_9876",
                session_type=session_type,
                duration_seconds=60,
                switch_activations=4,
                successful_reps=index % 5,
                max_force_n=1.0,
                timestamp=datetime(2026, 1, 1) + timedelta(minutes=index),
            )
            for index in range(21)
        ]
    )
    db.commit()
    try:
        client = TestClient(app)
        first_page = client.get("/history", params={"session_type": session_type})
        second_page = client.get("/history", params={"session_type": session_type, "page": 2})
        fragment = client.get(
            "/history",
            params={"session_type": session_type},
            headers={"HX-Request": "true"},
        )

        assert first_page.status_code == 200
        assert first_page.text.count('class="history-session"') == 20
        assert "Jan 01, 2026 00:20" in first_page.text
        assert second_page.text.count('class="history-session"') == 1
        assert "Jan 01, 2026 00:00" in second_page.text
        assert fragment.text.startswith('<tbody id="history-body">')
        assert "<html" not in fragment.text
        assert fragment.text.count('class="history-session"') == 20
    finally:
        db.query(SessionRecord).filter(SessionRecord.session_type == session_type).delete()
        db.commit()
        db.close()
