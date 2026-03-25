"""
SQLAlchemy ORM models for Gym AI Coach.

Tables:
  - Exercise: library of exercises (built-in + custom)
  - Workout: a training session on a given date
  - WorkoutExercise: exercises performed within a session
  - Set: individual set within a workout exercise
"""

from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    """User table for authentication and multi-tenancy."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    weight = Column(Float, nullable=True)     # Current weight in kg
    height = Column(Float, nullable=True)     # Height in cm
    goal = Column(String(100), nullable=True) # Fitness goal (e.g. "Ganar masa muscular")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workouts = relationship("Workout", back_populates="user", cascade="all, delete-orphan")
    exercises = relationship("Exercise", back_populates="user", cascade="all, delete-orphan")


class Exercise(Base):
    """Exercise library entry (e.g., Bench Press, Squat)."""

    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    muscle_group = Column(String(50), nullable=True)  # e.g., "Chest", "Legs"
    is_custom = Column(Boolean, default=False)         # True if added by user
    created_at = Column(DateTime, default=datetime.utcnow)

    # Multi-tenancy
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    user = relationship("User", back_populates="exercises")

    # Reverse relationship
    workout_exercises = relationship("WorkoutExercise", back_populates="exercise")


class Workout(Base):
    """A single training session."""

    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), nullable=True, default="")  # e.g. "Día A – Pecho/Tríceps"
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)    # Optional session notes
    is_finished = Column(Boolean, default=False)  # True once user finishes logging
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="workouts")
    workout_exercises = relationship(
        "WorkoutExercise", back_populates="workout", cascade="all, delete-orphan"
    )


class WorkoutExercise(Base):
    """
    Junction table linking a workout to an exercise.
    Preserves the order in which exercises were performed.
    """

    __tablename__ = "workout_exercises"

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    order = Column(Integer, default=0)  # Display/logging order within the session

    workout = relationship("Workout", back_populates="workout_exercises")
    exercise = relationship("Exercise", back_populates="workout_exercises")
    sets = relationship("Set", back_populates="workout_exercise", cascade="all, delete-orphan")


class Set(Base):
    """
    An individual set within a WorkoutExercise.
    Stores the performance data used for AI analysis and progress tracking.
    """

    __tablename__ = "sets"

    id = Column(Integer, primary_key=True, index=True)
    workout_exercise_id = Column(
        Integer, ForeignKey("workout_exercises.id", ondelete="CASCADE"), nullable=False
    )
    set_number = Column(Integer, nullable=False)  # 1-indexed set order
    weight = Column(Float, nullable=False)         # kg
    reps = Column(Integer, nullable=False)
    rir = Column(Integer, nullable=True)           # Reps In Reserve (0 = failure)
    notes = Column(Text, nullable=True)            # Optional per-set notes
    created_at = Column(DateTime, default=datetime.utcnow)

    workout_exercise = relationship("WorkoutExercise", back_populates="sets")
