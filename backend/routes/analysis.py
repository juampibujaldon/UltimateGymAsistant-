from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from dependencies import get_db, get_current_user
from services.ai_service import AIService

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.get("/{workout_id}", response_model=schemas.AnalysisResponse)
def analyze_workout_session(
    workout_id: int,
    lang: str = "es",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Generate AI coaching feedback for a specific workout session."""
    workout = db.query(models.Workout).filter(
        models.Workout.id == workout_id,
        models.Workout.user_id == current_user.id
    ).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found or access denied")
    
    ai_service = AIService()
    analysis = ai_service.analyze_workout(workout, lang=lang)
    
    return schemas.AnalysisResponse(workout_id=workout_id, analysis=analysis)
