from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from dependencies import get_db, get_current_user

router = APIRouter(prefix="/sets", tags=["sets"])

@router.post("/", response_model=schemas.SetRead, status_code=status.HTTP_201_CREATED)
def create_set(
    set_in: schemas.SetCreate,
    workout_exercise_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add a set to a workout exercise. Verifies the workout belongs to the user."""
    db_we = db.query(models.WorkoutExercise).join(models.Workout).filter(
        models.WorkoutExercise.id == workout_exercise_id,
        models.Workout.user_id == current_user.id
    ).first()
    if not db_we:
        raise HTTPException(status_code=404, detail="Workout exercise not found or access denied")
    
    db_set = models.Set(
        **set_in.model_dump(),
        workout_exercise_id=workout_exercise_id
    )
    db.add(db_set)
    db.commit()
    db.refresh(db_set)
    return db_set

@router.delete("/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_set(
    set_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a set. Verifies the workout belongs to the user."""
    db_set = db.query(models.Set).join(models.WorkoutExercise).join(models.Workout).filter(
        models.Set.id == set_id,
        models.Workout.user_id == current_user.id
    ).first()
    if not db_set:
        raise HTTPException(status_code=404, detail="Set not found or access denied")
    
    db.delete(db_set)
    db.commit()
    return None
