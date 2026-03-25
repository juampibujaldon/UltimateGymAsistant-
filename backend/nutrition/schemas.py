from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class NutritionGoalBase(BaseModel):
    calorie_target: float
    protein_target: float
    carbs_target: float
    fat_target: float


class NutritionGoalUpdate(NutritionGoalBase):
    pass


class NutritionGoalRead(NutritionGoalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class FoodEntryBase(BaseModel):
    name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    quantity: float = 1
    unit: str = "g"
    grams: float = 100
    calories: float = 0
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    source: Optional[str] = "manual"


class FoodEntryCreate(FoodEntryBase):
    pass


class FoodEntryUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    barcode: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    grams: Optional[float] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    source: Optional[str] = None


class FoodEntryRead(FoodEntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meal_entry_id: int
    created_at: datetime
    updated_at: datetime


class MealEntryBase(BaseModel):
    meal_type: str
    entry_date: date
    title: Optional[str] = None
    notes: Optional[str] = None


class MealEntryCreate(MealEntryBase):
    foods: List[FoodEntryCreate] = []


class MealEntryUpdate(BaseModel):
    meal_type: Optional[str] = None
    entry_date: Optional[date] = None
    title: Optional[str] = None
    notes: Optional[str] = None


class MealEntryRead(MealEntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    foods: List[FoodEntryRead] = []


class MacroTotals(BaseModel):
    calories: float = 0
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    fiber: float = 0
    sugar: float = 0


class NutritionDaySummary(BaseModel):
    date: date
    goals: NutritionGoalRead
    totals: MacroTotals
    remaining: MacroTotals
    meals: List[MealEntryRead]


class NutritionHistoryPoint(BaseModel):
    date: date
    calories: float
    protein: float
    carbs: float
    fat: float


class FoodLookupResult(BaseModel):
    barcode: str
    name: str
    brand: Optional[str] = None
    image_url: Optional[str] = None
    default_grams: float = 100
    calories_per_100g: float = 0
    protein_per_100g: float = 0
    carbs_per_100g: float = 0
    fat_per_100g: float = 0
    fiber_per_100g: Optional[float] = None
    sugar_per_100g: Optional[float] = None
    source: str = "openfoodfacts"


class NutritionInsightResponse(BaseModel):
    period: str
    summary: str
