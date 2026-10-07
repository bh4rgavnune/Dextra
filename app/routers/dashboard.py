from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from app.database import get_db
from app.models import Exercise, SessionRecord
from app.services.achievements import get_achievements
from app.services.metrics import calculate_success_rate, get_dashboard_stats

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    patient_id = "usr_9876"
    stats = get_dashboard_stats(db, patient_id)
    recent_sessions, latest_session_id = get_recent_sessions(db, patient_id)
    exercise_slugs = [slug for (slug,) in db.query(Exercise.slug).all()]
    trend_total = sum(stats["weekly_trend"]["values"])
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "stats": stats,
            "recent_sessions": recent_sessions,
            "latest_session_id": latest_session_id,
            "exercise_slugs": exercise_slugs,
            "trend_labels": stats["weekly_trend"]["labels"],
            "trend_values": stats["weekly_trend"]["values"],
            "trend_total": trend_total,
        },
    )


@router.get("/partials/stats", response_class=HTMLResponse)
async def stats_partial(request: Request, db: Session = Depends(get_db)):
    stats = get_dashboard_stats(db, "usr_9876")
    return templates.TemplateResponse(request, "partials/_stats.html", {"stats": stats})


@router.get("/partials/recent", response_class=HTMLResponse)
async def recent_partial(request: Request, db: Session = Depends(get_db)):
    recent_sessions, latest_session_id = get_recent_sessions(db, "usr_9876")
    exercise_slugs = [slug for (slug,) in db.query(Exercise.slug).all()]
    return templates.TemplateResponse(
        request,
        "partials/_recent.html",
        {
            "recent_sessions": recent_sessions,
            "latest_session_id": latest_session_id,
            "exercise_slugs": exercise_slugs,
        },
    )


def get_recent_sessions(db: Session, patient_id: str):
    latest_session_id = (
        db.query(SessionRecord.id)
        .filter(SessionRecord.patient_id == patient_id)
        .order_by(SessionRecord.id.desc())
        .limit(1)
        .scalar()
    )
    recent_sessions = (
        db.query(SessionRecord)
        .filter(SessionRecord.patient_id == patient_id)
        .order_by(SessionRecord.id.desc())
        .limit(5)
        .all()
    )
    return recent_sessions, latest_session_id or ""


@router.get("/history", response_class=HTMLResponse)
async def history_page(
    request: Request,
    session_type: str | None = None,
    page: int = 1,
    db: Session = Depends(get_db),
):
    patient_id = "usr_9876"
    query = db.query(SessionRecord).filter(SessionRecord.patient_id == patient_id)
    if session_type:
        query = query.filter(SessionRecord.session_type == session_type)
    total_sessions = query.count()
    total_pages = max(1, (total_sessions + 19) // 20)
    page = min(max(page, 1), total_pages)
    sessions = (
        query.order_by(SessionRecord.timestamp.desc(), SessionRecord.id.desc())
        .offset((page - 1) * 20)
        .limit(20)
        .all()
    )
    exercise_types = [
        row[0]
        for row in (
            db.query(SessionRecord.session_type)
            .filter(SessionRecord.patient_id == patient_id)
            .distinct()
            .order_by(SessionRecord.session_type)
            .all()
        )
    ]
    exercise_slugs = [slug for (slug,) in db.query(Exercise.slug).all()]
    context = {
        "sessions": sessions,
        "exercise_types": exercise_types,
        "selected_type": session_type or "",
        "page": page,
        "total_pages": total_pages,
        "total_sessions": total_sessions,
        "exercise_slugs": exercise_slugs,
    }
    template = "partials/_history_table_body.html" if request.headers.get("HX-Request") == "true" else "history.html"
    return templates.TemplateResponse(request, template, context)


@router.get("/achievements", response_class=HTMLResponse)
async def achievements_page(request: Request, db: Session = Depends(get_db)):
    patient_id = "usr_9876"
    achievements = get_achievements(db, patient_id)
    return templates.TemplateResponse(
        request,
        "achievements.html",
        {
            "achievements": achievements,
            "unlocked_count": sum(achievement["unlocked"] for achievement in achievements),
        },
    )


@router.get("/exercises", response_class=HTMLResponse)
@router.get("/exercise-library", response_class=HTMLResponse)
async def exercise_library_page(request: Request, db: Session = Depends(get_db)):
    exercises = db.query(Exercise).order_by(Exercise.title).all()
    return templates.TemplateResponse(
        request,
        "exercise_library.html",
        {"exercises": exercises},
    )


@router.get("/exercises/{key}", response_class=HTMLResponse)
async def exercise_detail_page(key: str, request: Request, db: Session = Depends(get_db)):
    exercise = db.query(Exercise).filter(Exercise.slug == key).first()
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")

    session_stats = (
        db.query(
            func.count(SessionRecord.id),
            func.coalesce(func.sum(SessionRecord.switch_activations), 0),
            func.coalesce(func.sum(SessionRecord.successful_reps), 0),
        )
        .filter(SessionRecord.patient_id == "usr_9876", SessionRecord.session_type == key)
        .one()
    )
    session_count, total_activations, total_successes = session_stats
    return templates.TemplateResponse(
        request,
        "exercise_detail.html",
        {
            "exercise": exercise,
            "steps": exercise.how_to_do_it.splitlines(),
            "session_count": session_count,
            "success_rate": calculate_success_rate(total_activations, total_successes),
        },
    )
