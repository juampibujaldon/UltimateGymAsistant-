import os
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models
import schemas
import auth
from dependencies import get_db, get_current_user
from services.ai_service import AIService

router = APIRouter(prefix="/auth", tags=["auth"])

DEMO_EMAIL = "demo@gym.local"
DEMO_PASSWORD = "demo123456"
DEMO_NAME = "Demo User"
ALLOW_DEMO_LOGIN = os.getenv("ENABLE_DEMO_AUTH", "false").lower() == "true"


def ensure_demo_user(db: Session) -> models.User:
    """Create or reset the local demo user so frontend demo access always works."""
    user = db.query(models.User).filter(models.User.email == DEMO_EMAIL).first()
    hashed_password = auth.get_password_hash(DEMO_PASSWORD)

    if user:
        user.hashed_password = hashed_password
        if not user.full_name:
            user.full_name = DEMO_NAME
    else:
        user = models.User(
            email=DEMO_EMAIL,
            hashed_password=hashed_password,
            full_name=DEMO_NAME,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return user

@router.post("/register", response_model=schemas.UserRead)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)) -> Any:
    """Create a new user."""
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists."
        )
    
    hashed_password = auth.get_password_hash(user_in.password)
    new_user = models.User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """Validate credentials and return a access token."""
    if ALLOW_DEMO_LOGIN and form_data.username == DEMO_EMAIL and form_data.password == DEMO_PASSWORD:
        user = ensure_demo_user(db)
    else:
        user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/demo-login", response_model=schemas.Token)
def demo_login(db: Session = Depends(get_db)) -> Any:
    """Issue a token for the local demo user."""
    if not ALLOW_DEMO_LOGIN:
        raise HTTPException(status_code=404, detail="Demo auth is disabled.")
    user = ensure_demo_user(db)
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserRead)
def read_current_user(
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """Return the authenticated user's profile."""
    return current_user

@router.patch("/me", response_model=schemas.UserRead)
def update_profile(
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """Update current user profile (weight, height, goal, etc)."""
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/me/insights")
def get_profile_insights(
    lang: str = "en",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Any:
    """Get AI personalized insights based on the user's physical profile and history."""
    try:
        insights = AIService.analyze_profile(db, current_user.id, lang)
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
