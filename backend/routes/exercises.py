"""
Exercises router.
Provides CRUD endpoints for the exercise library.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from dependencies import get_db, get_current_user

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/", response_model=List[schemas.ExerciseRead])
def list_exercises(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List all exercises: default ones + the user's custom ones."""
    return db.query(models.Exercise).filter(
        (models.Exercise.user_id == current_user.id) | (models.Exercise.user_id == None)
    ).all()


@router.post("/", response_model=schemas.ExerciseRead)
def create_exercise(
    exercise: schemas.ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new custom exercise for the current user."""
    db_exercise = models.Exercise(
        **exercise.model_dump(),
        user_id=current_user.id
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}", status_code=204)
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    """Delete a custom exercise. Built-in exercises cannot be deleted."""
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found.")
    if not exercise.is_custom:
        raise HTTPException(status_code=403, detail="Cannot delete built-in exercises.")
    db.delete(exercise)
    db.commit()
