"""
Progress calculation service.
Implements the Epley 1RM formula and volume tracking with multi-tenancy.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

import models
import schemas

def epley_1rm(weight: float, reps: int) -> float:
    """
    Estimate one-rep maximum using the Epley formula:
      1RM = weight * (1 + reps / 30)
    This is only accurate for reps <= 10.
    """
    if reps <= 0:
        return 0.0
    if reps == 1:
        return weight
    return round(weight * (1 + reps / 30), 1)

def calculate_volume(sets: List[models.Set]) -> float:
    """Total volume = sum of (weight × reps) across all sets."""
    return sum(s.weight * s.reps for s in sets)

class ProgressService:
    def __init__(self, db: Session):
        self.db = db

    def get_exercise_progress(self, exercise_id: int, user_id: int) -> schemas.ProgressRead:
        """
        Build the full progress history for a given exercise and user.
        Returns 1RM history, volume history, and PR info.
        """
        # Fetch exercise info
        exercise = self.db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()
        exercise_name = exercise.name if exercise else f"Exercise {exercise_id}"

        # Fetch all finished workouts for THIS USER that contain this exercise, ordered by date
        workout_exercises = (
            self.db.query(models.WorkoutExercise)
            .join(models.Workout)
            .filter(
                models.WorkoutExercise.exercise_id == exercise_id,
                models.Workout.user_id == user_id,
                models.Workout.is_finished == True,
            )
            .order_by(models.Workout.date)
            .all()
        )

        one_rm_history = []
        volume_history = []
        pr: Optional[schemas.PRInfo] = None
        best_1rm = 0.0

        for we in workout_exercises:
            if not we.sets:
                continue

            date = we.workout.date
            volume = calculate_volume(we.sets)
            
            # Find the best set in this specific workout
            best_set = max(we.sets, key=lambda s: epley_1rm(s.weight, s.reps))
            est_1rm = epley_1rm(best_set.weight, best_set.reps)

            one_rm_history.append(
                schemas.OneRMPoint(
                    date=date, 
                    estimated_1rm=est_1rm, 
                    weight=best_set.weight, 
                    reps=best_set.reps
                )
            )
            volume_history.append(schemas.VolumePoint(date=date, volume=volume))

            # Track overall Personal Record (PR)
            if est_1rm > best_1rm:
                best_1rm = est_1rm
                pr = schemas.PRInfo(
                    weight=best_set.weight,
                    reps=best_set.reps,
                    estimated_1rm=est_1rm,
                    date=date,
                )

        return schemas.ProgressRead(
            exercise_id=exercise_id,
            exercise_name=exercise_name,
            one_rm_history=one_rm_history,
            volume_history=volume_history,
            personal_record=pr,
        )
