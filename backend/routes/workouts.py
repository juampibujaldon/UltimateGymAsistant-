"""
Workouts router.
Manages workout sessions and their exercises.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

import models
import schemas
from dependencies import get_db, get_current_user
from services.ai_service import AIService

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("/", response_model=List[schemas.WorkoutSummary])
def list_workouts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Retrieve all workouts for the current user with exercise/set counts."""
    workouts = db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id
    ).options(
        selectinload(models.Workout.workout_exercises).selectinload(models.WorkoutExercise.sets)
    ).all()
    
    # Calculate counts manually for the summary
    summaries = []
    for w in workouts:
        ex_count = len(w.workout_exercises)
        set_count = sum(len(we.sets) for we in w.workout_exercises)
        summaries.append(
            schemas.WorkoutSummary(
                **schemas.WorkoutRead.model_validate(w).model_dump(),
                exercise_count=ex_count,
                set_count=set_count
            )
        )
    return summaries


@router.post("/", response_model=schemas.WorkoutRead)
def create_workout(
    workout: schemas.WorkoutCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Start a new workout session for the current user."""
    db_workout = models.Workout(
        **workout.model_dump(),
        user_id=current_user.id
    )
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return db_workout


@router.post("/generate", response_model=schemas.WorkoutRead)
def generate_workout(
    req: schemas.WorkoutGenerateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Generate a new workout session using Gemini AI."""
    from sqlalchemy import desc
    
    all_exercises = db.query(models.Exercise).filter(
        (models.Exercise.user_id == None) | (models.Exercise.user_id == current_user.id)
    ).all()
    
    recent_workouts = db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id,
        models.Workout.is_finished == True
    ).order_by(desc(models.Workout.date)).limit(3).all()
    
    history = []
    for hw in recent_workouts:
        session_data = {"date": hw.date.strftime("%Y-%m-%d"), "workout_exercises": []}
        for we in hw.workout_exercises:
            ex_name = we.exercise.name if we.exercise else "?"
            session_data["workout_exercises"].append({"exercise_name": ex_name})
        history.append(session_data)
    history.reverse()
    
    ai_service = AIService()
    rec_ids = ai_service.generate_routine(all_exercises, history, req.category)
    
    w_name = f"Rutina Generada con IA ✨ ({req.category})" if req.category else "Rutina Generada con IA ✨"
    
    db_workout = models.Workout(
        user_id=current_user.id,
        name=w_name,
    )
    db.add(db_workout)
    db.flush()
    
    for i, ex_id in enumerate(rec_ids):
        if any(e.id == ex_id for e in all_exercises):
            we = models.WorkoutExercise(
                workout_id=db_workout.id,
                exercise_id=ex_id,
                order=i
            )
            db.add(we)
            
    db.commit()
    db.refresh(db_workout)
    return db_workout


@router.get("/{workout_id}", response_model=schemas.WorkoutRead)
def get_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get full details of a specific workout."""
    db_workout = db.query(models.Workout).filter(
        models.Workout.id == workout_id,
        models.Workout.user_id == current_user.id
    ).first()
    if not db_workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return db_workout


@router.patch("/{workout_id}", response_model=schemas.WorkoutRead)
def update_workout(
    workout_id: int,
    workout_update: schemas.WorkoutUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update workout metadata or finish the session."""
    db_workout = db.query(models.Workout).filter(
        models.Workout.id == workout_id,
        models.Workout.user_id == current_user.id
    ).first()
    if not db_workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    for key, value in workout_update.model_dump(exclude_unset=True).items():
        setattr(db_workout, key, value)
    
    db.commit()
    db.refresh(db_workout)
    return db_workout


@router.delete("/{workout_id}")
def delete_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a workout and all its contents."""
    db_workout = db.query(models.Workout).filter(
        models.Workout.id == workout_id,
        models.Workout.user_id == current_user.id
    ).first()
    if not db_workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    db.delete(db_workout)
    db.commit()
    return {"detail": "Workout deleted"}


# ─── Workout Exercise Management ─────────────────────────────────────────────

@router.post("/{workout_id}/exercises", response_model=schemas.WorkoutRead)
def add_exercise_to_workout(
    workout_id: int,
    we_in: schemas.WorkoutExerciseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add an exercise to an active workout."""
    db_workout = db.query(models.Workout).filter(
        models.Workout.id == workout_id,
        models.Workout.user_id == current_user.id
    ).first()
    if not db_workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    # Check if exercise exists
    exercise = db.query(models.Exercise).filter(models.Exercise.id == we_in.exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found.")

    # Prevent duplicate exercises in the same session
    existing = (
        db.query(models.WorkoutExercise)
        .filter(
            models.WorkoutExercise.workout_id == workout_id,
            models.WorkoutExercise.exercise_id == we_in.exercise_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Exercise already in this workout.")

    db_we = models.WorkoutExercise(
        workout_id=workout_id,
        exercise_id=we_in.exercise_id,
        order=we_in.order
    )
    db.add(db_we)
    db.commit()
    db.refresh(db_workout)
    return db_workout

@router.delete("/{workout_id}/exercises/{we_id}", response_model=schemas.WorkoutRead)
def remove_exercise_from_workout(
    workout_id: int,
    we_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Remove an exercise and its sets from the workout."""
    db_workout = db.query(models.Workout).filter(
        models.Workout.id == workout_id,
        models.Workout.user_id == current_user.id
    ).first()
    if not db_workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    db_we = db.query(models.WorkoutExercise).filter(
        models.WorkoutExercise.id == we_id,
        models.WorkoutExercise.workout_id == workout_id
    ).first()
    if not db_we:
        raise HTTPException(status_code=404, detail="Exercise not in this workout")
    
    db.delete(db_we)
    db.commit()
    db.refresh(db_workout)
    return db_workout
