import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
import nutrition.models
from database import engine, SessionLocal
from routes import exercises, workouts, sets, progress, analysis, auth
from nutrition.router import router as nutrition_router
from seed import seed_exercises

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
ALLOWED_ORIGINS_RAW = os.getenv(
    "ALLOWED_ORIGINS",
    "http://127.0.0.1:5173,http://localhost:5173" if ENVIRONMENT != "production" else "",
)
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_RAW.split(",") if origin.strip()]

if ENVIRONMENT == "production" and not ALLOWED_ORIGINS:
    raise RuntimeError("Set ALLOWED_ORIGINS before running in production.")

# ─── Create tables ───────────────────────────────────────────────────────────
# For SQLite, we recreate tables if the schema changed.
# In a production app, we'd use Alembic.
models.Base.metadata.create_all(bind=engine)

# ─── Seed default exercises (system-wide) ──────────────────────────────────
with SessionLocal() as db:
    seed_exercises(db)

# ─── FastAPI app ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Gym AI Coach API",
    description="Backend API for workout logging, progress and AI coaching.",
    version="1.1.0"
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(exercises.router)
app.include_router(workouts.router)
app.include_router(sets.router)
app.include_router(progress.router)
app.include_router(analysis.router)
app.include_router(nutrition_router)

@app.get("/")
def root():
    return {
        "name": "Gym AI Coach API",
        "status": "online",
        "health": "/health",
        "docs": "/docs",
    }

@app.get("/health")
def health_check():
    return {"status": "online", "version": "1.1.0"}
