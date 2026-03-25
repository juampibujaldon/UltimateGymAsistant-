from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from dependencies import get_db, get_current_user
from services.progress_service import ProgressService

router = APIRouter(prefix="/progress", tags=["progress"])

@router.get("/{exercise_id}", response_model=schemas.ProgressRead)
def get_exercise_progress(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Return historical 1RM and volume for a specific exercise and user."""
    service = ProgressService(db)
    return service.get_exercise_progress(exercise_id, user_id=current_user.id)
