from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# ─────────────────── User ───────────────────

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    goal: Optional[str] = None


class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    goal: Optional[str] = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
    created_at: datetime


# ─────────────────── Token ───────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# ─────────────────── Exercise ───────────────────

class ExerciseCreate(BaseModel):
    name: str
    muscle_group: Optional[str] = None
    is_custom: bool = False


class ExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    muscle_group: Optional[str]
    is_custom: bool
    created_at: datetime
    user_id: Optional[int] = None


# ─────────────────── Set ───────────────────

class SetCreate(BaseModel):
    set_number: int
    weight: float    # kg
    reps: int
    rir: Optional[int] = None
    notes: Optional[str] = None


class SetUpdate(BaseModel):
    weight: Optional[float] = None
    reps: Optional[int] = None
    rir: Optional[int] = None
    notes: Optional[str] = None


class SetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workout_exercise_id: int
    set_number: int
    weight: float
    reps: int
    rir: Optional[int]
    notes: Optional[str]
    created_at: datetime


# ─────────────────── WorkoutExercise ───────────────────

class WorkoutExerciseCreate(BaseModel):
    exercise_id: int
    order: int = 0


class WorkoutExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workout_id: int
    exercise_id: int
    order: int
    exercise: ExerciseRead
    sets: List[SetRead] = []


# ─────────────────── Workout ───────────────────

class WorkoutCreate(BaseModel):
    name: Optional[str] = ""
    date: Optional[datetime] = None
    notes: Optional[str] = None


class WorkoutGenerateRequest(BaseModel):
    category: Optional[str] = None


class WorkoutUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    is_finished: Optional[bool] = None


class WorkoutRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str]
    date: datetime
    notes: Optional[str]
    is_finished: bool
    created_at: datetime
    user_id: int
    workout_exercises: List[WorkoutExerciseRead] = []


class WorkoutSummary(BaseModel):
    """Lightweight summary used in list views."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str]
    date: datetime
    notes: Optional[str]
    is_finished: bool
    exercise_count: int = 0
    set_count: int = 0


# ─────────────────── Progress ───────────────────

class OneRMPoint(BaseModel):
    date: datetime
    estimated_1rm: float
    weight: float
    reps: int


class VolumePoint(BaseModel):
    date: datetime
    volume: float          # sum of weight * reps for that session


class PRInfo(BaseModel):
    weight: float
    reps: int
    estimated_1rm: float
    date: datetime


class ProgressRead(BaseModel):
    exercise_id: int
    exercise_name: str
    one_rm_history: List[OneRMPoint]
    volume_history: List[VolumePoint]
    personal_record: Optional[PRInfo]


# ─────────────────── Analysis ───────────────────

class AnalysisResponse(BaseModel):
    workout_id: int
    analysis: str          # Markdown-formatted AI response
