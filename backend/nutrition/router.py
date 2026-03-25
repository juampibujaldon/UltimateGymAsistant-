from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

import models
from dependencies import get_current_user, get_db
from nutrition.ai_service import NutritionAIService
from nutrition.models import FoodEntry, MealEntry, NutritionGoal
from nutrition.off_service import OpenFoodFactsService
from nutrition.schemas import (
    FoodEntryCreate,
    FoodEntryRead,
    FoodEntryUpdate,
    MacroTotals,
    MealEntryCreate,
    MealEntryRead,
    MealEntryUpdate,
    NutritionDaySummary,
    NutritionGoalRead,
    NutritionGoalUpdate,
    NutritionHistoryPoint,
    NutritionInsightResponse,
)

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


def _get_or_create_goal(db: Session, user_id: int) -> NutritionGoal:
    goal = db.query(NutritionGoal).filter(NutritionGoal.user_id == user_id).first()
    if goal:
        return goal

    goal = NutritionGoal(user_id=user_id)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def _meal_query(db: Session, user_id: int, target_date: date):
    return (
        db.query(MealEntry)
        .filter(MealEntry.user_id == user_id, MealEntry.entry_date == target_date)
        .options(selectinload(MealEntry.foods))
        .order_by(MealEntry.meal_type.asc(), MealEntry.created_at.asc())
    )


def _sum_meals(meals: list[MealEntry]) -> MacroTotals:
    totals = MacroTotals()
    for meal in meals:
        for food in meal.foods:
            totals.calories += food.calories
            totals.protein += food.protein
            totals.carbs += food.carbs
            totals.fat += food.fat
            totals.fiber += food.fiber or 0
            totals.sugar += food.sugar or 0
    return totals


def _build_summary(db: Session, user_id: int, target_date: date) -> NutritionDaySummary:
    goal = _get_or_create_goal(db, user_id)
    meals = _meal_query(db, user_id, target_date).all()
    totals = _sum_meals(meals)
    remaining = MacroTotals(
        calories=goal.calorie_target - totals.calories,
        protein=goal.protein_target - totals.protein,
        carbs=goal.carbs_target - totals.carbs,
        fat=goal.fat_target - totals.fat,
        fiber=0,
        sugar=0,
    )

    return NutritionDaySummary(
        date=target_date,
        goals=NutritionGoalRead.model_validate(goal),
        totals=totals,
        remaining=remaining,
        meals=[MealEntryRead.model_validate(meal) for meal in meals],
    )


@router.get("/goals", response_model=NutritionGoalRead)
def get_goals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _get_or_create_goal(db, current_user.id)


@router.put("/goals", response_model=NutritionGoalRead)
def update_goals(
    payload: NutritionGoalUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    goal = _get_or_create_goal(db, current_user.id)
    for field, value in payload.model_dump().items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/day", response_model=NutritionDaySummary)
def get_day_summary(
    day: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _build_summary(db, current_user.id, day)


@router.get("/history", response_model=list[NutritionHistoryPoint])
def get_history(
    days: int = Query(default=7, ge=1, le=60),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    points: list[NutritionHistoryPoint] = []

    for offset in range(days):
        target = start_date + timedelta(days=offset)
        summary = _build_summary(db, current_user.id, target)
        points.append(
            NutritionHistoryPoint(
                date=target,
                calories=summary.totals.calories,
                protein=summary.totals.protein,
                carbs=summary.totals.carbs,
                fat=summary.totals.fat,
            )
        )
    return points


@router.post("/meals", response_model=MealEntryRead)
def create_meal(
    payload: MealEntryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    meal = MealEntry(
        user_id=current_user.id,
        meal_type=payload.meal_type,
        entry_date=payload.entry_date,
        title=payload.title,
        notes=payload.notes,
    )
    db.add(meal)
    db.flush()

    for food_payload in payload.foods:
        db.add(FoodEntry(meal_entry_id=meal.id, **food_payload.model_dump()))

    db.commit()
    db.refresh(meal)
    return meal


@router.patch("/meals/{meal_id}", response_model=MealEntryRead)
def update_meal(
    meal_id: int,
    payload: MealEntryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    meal = db.query(MealEntry).filter(MealEntry.id == meal_id, MealEntry.user_id == current_user.id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(meal, field, value)

    db.commit()
    db.refresh(meal)
    return meal


@router.delete("/meals/{meal_id}")
def delete_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    meal = db.query(MealEntry).filter(MealEntry.id == meal_id, MealEntry.user_id == current_user.id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found.")

    db.delete(meal)
    db.commit()
    return {"detail": "Meal deleted"}


@router.post("/meals/{meal_id}/foods", response_model=FoodEntryRead)
def add_food(
    meal_id: int,
    payload: FoodEntryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    meal = db.query(MealEntry).filter(MealEntry.id == meal_id, MealEntry.user_id == current_user.id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found.")

    food = FoodEntry(meal_entry_id=meal.id, **payload.model_dump())
    db.add(food)
    db.commit()
    db.refresh(food)
    return food


@router.patch("/foods/{food_id}", response_model=FoodEntryRead)
def update_food(
    food_id: int,
    payload: FoodEntryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    food = (
        db.query(FoodEntry)
        .join(MealEntry, MealEntry.id == FoodEntry.meal_entry_id)
        .filter(FoodEntry.id == food_id, MealEntry.user_id == current_user.id)
        .first()
    )
    if not food:
        raise HTTPException(status_code=404, detail="Food entry not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(food, field, value)

    db.commit()
    db.refresh(food)
    return food


@router.delete("/foods/{food_id}")
def delete_food(
    food_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    food = (
        db.query(FoodEntry)
        .join(MealEntry, MealEntry.id == FoodEntry.meal_entry_id)
        .filter(FoodEntry.id == food_id, MealEntry.user_id == current_user.id)
        .first()
    )
    if not food:
        raise HTTPException(status_code=404, detail="Food entry not found.")

    db.delete(food)
    db.commit()
    return {"detail": "Food entry deleted"}


@router.get("/barcode/{barcode}")
def lookup_barcode(
    barcode: str,
    current_user: models.User = Depends(get_current_user),
):
    del current_user
    service = OpenFoodFactsService()
    return service.lookup_barcode(barcode)


@router.get("/insights/daily", response_model=NutritionInsightResponse)
def get_daily_insight(
    day: date = Query(default_factory=date.today),
    lang: str = "en",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    summary = _build_summary(db, current_user.id, day)
    service = NutritionAIService()
    return NutritionInsightResponse(period="daily", summary=service.day_insight(summary, lang))


@router.get("/insights/weekly", response_model=NutritionInsightResponse)
def get_weekly_insight(
    days: int = Query(default=7, ge=3, le=30),
    lang: str = "en",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    points = get_history(days=days, db=db, current_user=current_user)
    service = NutritionAIService()
    return NutritionInsightResponse(period="weekly", summary=service.weekly_insight(points, lang))
