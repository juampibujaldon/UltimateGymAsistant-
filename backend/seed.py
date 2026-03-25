"""
Seeds the database with a default list of common exercises.
Called once on app startup if the exercises table is empty.
"""

from sqlalchemy.orm import Session

from models import Exercise

DEFAULT_EXERCISES = [
    {"name": "Bench Press", "muscle_group": "Chest"},
    {"name": "Incline Bench Press", "muscle_group": "Chest"},
    {"name": "Dumbbell Fly", "muscle_group": "Chest"},
    {"name": "Squat", "muscle_group": "Legs"},
    {"name": "Front Squat", "muscle_group": "Legs"},
    {"name": "Leg Press", "muscle_group": "Legs"},
    {"name": "Romanian Deadlift", "muscle_group": "Legs"},
    {"name": "Deadlift", "muscle_group": "Back"},
    {"name": "Pull Ups", "muscle_group": "Back"},
    {"name": "Barbell Rows", "muscle_group": "Back"},
    {"name": "Cable Rows", "muscle_group": "Back"},
    {"name": "Lat Pulldown", "muscle_group": "Back"},
    {"name": "Overhead Press", "muscle_group": "Shoulders"},
    {"name": "Lateral Raises", "muscle_group": "Shoulders"},
    {"name": "Face Pulls", "muscle_group": "Shoulders"},
    {"name": "Barbell Curl", "muscle_group": "Biceps"},
    {"name": "Hammer Curl", "muscle_group": "Biceps"},
    {"name": "Tricep Pushdown", "muscle_group": "Triceps"},
    {"name": "Close Grip Bench Press", "muscle_group": "Triceps"},
    {"name": "Calf Raises", "muscle_group": "Legs"},
    {"name": "Hip Thrust", "muscle_group": "Glutes"},
    {"name": "Plank", "muscle_group": "Core"},
]


def seed_exercises(db: Session) -> None:
    """Insert default exercises if none exist yet."""
    if db.query(Exercise).count() == 0:
        for ex_data in DEFAULT_EXERCISES:
            db.add(Exercise(**ex_data, is_custom=False))
        db.commit()
        print(f"✅  Seeded {len(DEFAULT_EXERCISES)} default exercises.")
