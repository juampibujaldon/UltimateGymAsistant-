from datetime import date, timedelta
from typing import Iterable

from google import genai

from nutrition.schemas import NutritionHistoryPoint, NutritionDaySummary
from services.ai_service import AIService


def _fallback_day_insight(summary: NutritionDaySummary) -> str:
    remaining = summary.remaining
    return (
        f"Calories remaining: {remaining.calories:.0f}. "
        f"Protein remaining: {remaining.protein:.0f}g. "
        f"Carbs remaining: {remaining.carbs:.0f}g. "
        f"Fat remaining: {remaining.fat:.0f}g."
    )


class NutritionAIService:
    def __init__(self) -> None:
        self.base_ai = AIService()
        self.api_key = self.base_ai.api_key

    def build_day_prompt(self, summary: NutritionDaySummary, lang: str) -> str:
        meal_lines = []
        for meal in summary.meals:
            foods = ", ".join(f"{food.name} ({food.calories:.0f} kcal)" for food in meal.foods) or "No foods"
            meal_lines.append(f"- {meal.meal_type}: {foods}")

        return f"""
You are an evidence-based sports nutrition coach.
Analyze the user's day and provide practical feedback in {lang}.

Goals:
- Calories: {summary.goals.calorie_target}
- Protein: {summary.goals.protein_target}g
- Carbs: {summary.goals.carbs_target}g
- Fat: {summary.goals.fat_target}g

Consumed:
- Calories: {summary.totals.calories:.1f}
- Protein: {summary.totals.protein:.1f}g
- Carbs: {summary.totals.carbs:.1f}g
- Fat: {summary.totals.fat:.1f}g

Meals:
{chr(10).join(meal_lines)}

Respond with:
1. Daily assessment
2. What is missing or excessive
3. 2 concrete food suggestions
Keep it short and actionable.
"""

    def day_insight(self, summary: NutritionDaySummary, lang: str = "en") -> str:
        if not self.api_key:
            return _fallback_day_insight(summary)

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=self.build_day_prompt(summary, lang),
        )
        return response.text

    def weekly_insight(self, points: Iterable[NutritionHistoryPoint], lang: str = "en") -> str:
        points = list(points)
        if not points:
            return "No nutrition history yet."

        if not self.api_key:
            avg_calories = sum(point.calories for point in points) / len(points)
            avg_protein = sum(point.protein for point in points) / len(points)
            return (
                f"Last {len(points)} days average: {avg_calories:.0f} kcal and {avg_protein:.0f}g protein. "
                "Aim for consistency and close protein gaps early in the day."
            )

        today = date.today()
        since = today - timedelta(days=len(points) - 1)
        lines = "\n".join(
            f"- {point.date.isoformat()}: {point.calories:.0f} kcal, {point.protein:.0f}p, {point.carbs:.0f}c, {point.fat:.0f}f"
            for point in points
        )

        prompt = f"""
You are a sports nutrition coach. Review the weekly nutrition trend from {since.isoformat()} to {today.isoformat()}.
Write the analysis in {lang}.

Daily data:
{lines}

Respond with:
1. Weekly pattern
2. Main nutritional gap
3. One simple adjustment for next week
"""

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
