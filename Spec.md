# Dextra Rehab Dashboard: SPEC

## Context
Dextra is a switch-controlled wrist-hand orthosis (ESP32 + servo motors).
After each exercise session the device POSTs one JSON payload to the backend.
The website processes it and shows dashboards, achievements, and exercise education.
Solo project, 24-hour deadline. Prioritise a working demo over completeness.

## Stack (fixed, do not change)
Python 3.11+, FastAPI, SQLAlchemy + SQLite, Jinja2, HTMX, Tailwind (CDN), Chart.js (CDN).
No Docker, no Redis, no login (single hardcoded demo patient).
Use the current Starlette style: TemplateResponse(request, "name.html", context).

## Device payload (POST /api/ingest)
{
  "device_id": "DEXTRA_ESP_01",
  "patient_id": "usr_9876",
  "session_type": "wrist_extension",
  "duration_seconds": 180,
  "switch_activations": 12,
  "successful_reps": 10,
  "max_force_n": 15.2,
  "timestamp": "2026-10-07T17:30:00Z"
}

## Pages
1. Dashboard: stat cards, progress chart, recent sessions
2. History: table of all sessions with filter by exercise type
3. Achievements: unlocked and locked badges
4. Exercise Library: what it is, how to do it, why it helps (simple, non-clinical language)

## Metrics
- success_rate = successful_reps / switch_activations
- total reps, avg duration, weekly trend, day streak

## Folder structure
app/main.py, database.py, models.py, schemas.py, services/metrics.py,
services/achievements.py, routers/, templates/, templates/partials/, static/
simulate_device.py, seed_exercises.py, tests/