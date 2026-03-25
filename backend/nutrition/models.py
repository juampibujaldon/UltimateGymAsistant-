from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class NutritionGoal(Base):
    __tablename__ = "nutrition_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    calorie_target = Column(Float, nullable=False, default=2200)
    protein_target = Column(Float, nullable=False, default=160)
    carbs_target = Column(Float, nullable=False, default=220)
    fat_target = Column(Float, nullable=False, default=70)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MealEntry(Base):
    __tablename__ = "meal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    meal_type = Column(String(30), nullable=False, index=True)
    entry_date = Column(Date, nullable=False, default=date.today, index=True)
    title = Column(String(120), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    foods = relationship("FoodEntry", back_populates="meal_entry", cascade="all, delete-orphan")


class FoodEntry(Base):
    __tablename__ = "food_entries"

    id = Column(Integer, primary_key=True, index=True)
    meal_entry_id = Column(Integer, ForeignKey("meal_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(160), nullable=False)
    brand = Column(String(160), nullable=True)
    barcode = Column(String(64), nullable=True, index=True)
    quantity = Column(Float, nullable=False, default=1)
    unit = Column(String(20), nullable=False, default="g")
    grams = Column(Float, nullable=False, default=100)
    calories = Column(Float, nullable=False, default=0)
    protein = Column(Float, nullable=False, default=0)
    carbs = Column(Float, nullable=False, default=0)
    fat = Column(Float, nullable=False, default=0)
    fiber = Column(Float, nullable=True)
    sugar = Column(Float, nullable=True)
    source = Column(String(40), nullable=True, default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meal_entry = relationship("MealEntry", back_populates="foods")
