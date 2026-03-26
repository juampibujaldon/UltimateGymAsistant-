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


def parse_allowed_origins() -> list[str]:
    origins: list[str] = []

    raw_allowed_origins = os.getenv("ALLOWED_ORIGINS", "")
    frontend_url = os.getenv("FRONTEND_URL", "")
    railway_public_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")

    for raw_value in (raw_allowed_origins, frontend_url):
        origins.extend(origin.strip() for origin in raw_value.split(",") if origin.strip())

    if railway_public_domain:
        origins.append(f"https://{railway_public_domain}")

    if ENVIRONMENT != "production":
        origins.extend(
            [
                "http://127.0.0.1:5173",
                "http://localhost:5173",
                "http://127.0.0.1:8080",
                "http://localhost:8080",
            ]
        )

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(origins))


ALLOWED_ORIGINS = parse_allowed_origins()

if ENVIRONMENT == "production" and not ALLOWED_ORIGINS:
    raise RuntimeError("Set ALLOWED_ORIGINS or FRONTEND_URL before running in production.")

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
