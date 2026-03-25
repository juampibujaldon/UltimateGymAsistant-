from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from database import engine, SessionLocal
from routes import exercises, workouts, sets, progress, analysis, auth
from seed import seed_exercises

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
    allow_origins=["*"],  # In production, specify actual frontend URL
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

@app.get("/health")
def health_check():
    return {"status": "online", "version": "1.1.0"}
