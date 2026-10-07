from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import api, dashboard
from app.seed_exercises import seed_exercises

Base.metadata.create_all(bind=engine)
seed_exercises()

app = FastAPI(title="Dextra Rehab Dashboard")
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")
app.include_router(dashboard.router)
app.include_router(api.router)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}
