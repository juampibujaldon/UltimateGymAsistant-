"""
AI coaching service.
Builds a rich prompt from workout data + history and calls an OpenAI-compatible LLM.
"""

import os
from typing import Optional

import json
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()

# ─── System prompt – defines the AI coach persona ───────────────────────────
SYSTEM_PROMPT = """You are an expert strength and hypertrophy coach with 15+ years of experience.
You analyze workout data including sets, reps, weight, and RIR (Reps In Reserve).
You provide precise, constructive, and practical feedback to help the athlete improve performance and progression.

When analyzing a workout session, always structure your response with these sections:
1. **Session Summary** – Overall intensity, training quality, and fatigue estimate
2. **Exercise Analysis** – For each exercise: performance assessment, estimated 1RM, RIR interpretation
3. **Fatigue Analysis** – Signs of fatigue, RIR trends across the session
4. **Progress Estimation** – Compared to previous sessions (if available)
5. **Next Workout Recommendations** – Specific weight/rep targets for each exercise
6. **Weight Progression Suggestions** – Whether to increase, maintain, or reduce load
7. **Technique & Effort Warnings** – Flag any RIR=0 (failure) or very high fatigue sets

Use markdown formatting with headers, bullet points, and bold text.
Be specific with numbers. Act like a knowledgeable coach who knows the athlete well."""


class AIService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY", "")

    def build_workout_prompt(self, current_workout: dict, lang: str = "es", history: Optional[list] = None) -> str:
        """
        Build the user-facing prompt containing the workout data.
        """
        def _get_val(obj, key, default=None):
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        lines = ["## Current Workout Session\n"]
        lines.append(f"Date: {_get_val(current_workout, 'date', 'Unknown')}")
        notes = _get_val(current_workout, "notes")
        if notes:
            lines.append(f"Session Notes: {notes}")
        lines.append("")

        # Format exercises and sets
        # Note: In the route, we pass the model object, not a dict. 
        # But let's keep it flexible or adjust to what the route passes.
        # Looking at routes/analysis.py: workout = db.query(models.Workout)...
        # So current_workout is a models.Workout object.
        
        workout_exercises = getattr(current_workout, "workout_exercises", [])
        for we in workout_exercises:
            exercise_name = we.exercise.name if hasattr(we, "exercise") else "Unknown Exercise"
            lines.append(f"### {exercise_name}")
            
            for s in sorted(we.sets, key=lambda x: x.set_number):
                rir_str = f" | RIR {s.rir}" if s.rir is not None else ""
                notes_str = f" | Note: {s.notes}" if s.notes else ""
                lines.append(
                    f"  Set {s.set_number}: {s.weight}kg × {s.reps} reps{rir_str}{notes_str}"
                )
            lines.append("")

        # Add historical context if available
        if history:
            lines.append("---\n## Recent History (same exercises)\n")
            for past_session in history[-4:]:  # Last 4 sessions
                lines.append(f"**{past_session.get('date', 'Unknown date')}**")
                for we in past_session.get("workout_exercises", []):
                    lines.append(f"- {we.get('exercise_name', '?')}: ", )
                    set_summaries = []
                    for s in we.get("sets", []):
                        rir_str = f"/RIR{s['rir']}" if s.get("rir") is not None else ""
                        set_summaries.append(f"{s['weight']}kg×{s['reps']}{rir_str}")
                    lines[-1] = lines[-1] + ", ".join(set_summaries)
                lines.append("")

        lines.append(
            "\nPlease analyze this workout session and provide detailed coaching feedback."
        )
        
        # Add strong instruction for language translation
        lines.append(f"\nCRITICAL INSTRUCTION: You MUST write your ENTIRE analysis and response strictly in the '{lang}' language. Do not use English unless the user's language is English.")
        
        return "\n".join(lines)

    def call_ai(self, prompt: str) -> str:
        """
        Send the prompt to Google Gemini and return the response text.
        """
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            # Return a mock response when no API key is configured
            return self._mock_analysis(prompt)

        client = genai.Client(api_key=self.api_key)
        
        # Combine system prompt + user prompt since Gemini uses the config for system instructions
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,
                    max_output_tokens=2000,
                )
            )
            return response.text
        except Exception as e:
            return f"❌ Error llamando a la IA: {e}"

    def _mock_analysis(self, prompt: str) -> str:
        """
        Returns a realistic mock analysis when no API key is configured.
        """
        return """## 🏋️ Session Summary

**Overall Intensity:** Moderate-High  
**Training Quality:** Good  
**Fatigue Level:** Moderate

Your session shows solid effort with proper RIR management. The progression in load is appropriate.

---

## 📊 Exercise Analysis

### Bench Press
- **Performance:** Strong performance with controlled fatigue
- **Estimated 1RM:** ~93 kg (based on 80 kg × 6 @ RIR 1)
- **RIR Trend:** RIR decreased from 1 → 0 → 1, indicating good fatigue management
- **Assessment:** The drop in weight for Set 3 was smart — prioritizing quality over grinding

### Squat / Other Exercises
- Adequate stimulus achieved across all sets
- RIR values indicate you left some capacity in the tank — ideal for hypertrophy

---

## 😮‍💨 Fatigue Analysis

- RIR trend is healthy — you approached failure without exceeding it
- No signs of excessive central fatigue
- Session length appears appropriate

---

## 📈 Progress Estimation

⚠️ *No historical data available for comparison yet. Log more sessions to see progress trends.*

---

## 🎯 Next Workout Recommendations

| Exercise | Current | Next Session |
|----------|---------|-------------|
| Bench Press | 80 kg × 6 | Try **82.5 kg × 5** or **80 kg × 7** |
| Supporting exercises | Maintain | Same weight, aim for +1 rep |

---

## ⬆️ Weight Progression Suggestions

- **Bench Press:** You're ready for a small weight increase (+2.5 kg) or extra rep
- **Other exercises:** Maintain current loads and focus on rep quality

---

## ⚠️ Technique & Effort Warnings

- Set 2 reached **RIR 0** (technical failure) — monitor fatigue accumulation
- Ensure adequate rest between sessions (48-72 hours for compound movements)
- Great job not grinding excessively past failure!

---

*💡 Note: This is a demo analysis. Connect your GEMINI API key in `backend/.env` for real AI coaching.*
"""

    def analyze_workout(self, current_workout: dict, lang: str = "es", history: Optional[list] = None) -> str:
        """Main entry point: build prompt and call AI, return analysis text."""
        prompt = self.build_workout_prompt(current_workout, lang, history)
        return self.call_ai(prompt)

    def generate_routine(self, all_exercises: list, history: Optional[list] = None, category: str = None) -> list[int]:
        """
        AI recommends 4-6 exercises based on history and an optional category target.
        Returns a list of exercise IDs.
        """
        lines = ["You are an expert fitness coach. Your task is to generate a new workout routine consisting of 4 to 6 exercises."]
        lines.append("Here is the list of available exercises:")
        for ex in all_exercises:
            lines.append(f"- ID {getattr(ex, 'id', '?')}: {getattr(ex, 'name', '?')} (Muscle: {getattr(ex, 'muscle_group', 'None')})")
        
        if history:
            lines.append("\nHere is what the user trained recently (do not overwork the same muscles trained in the last 48 hours):")
            for past in history[-3:]:
                lines.append(f"Date: {past.get('date', 'Unknown')}")
                for we in past.get("workout_exercises", []):
                    lines.append(f" - {we.get('exercise_name', '?')}")
        
        if category:
            lines.append(f"\nCRITICAL TARGET: The user explicitly requested a routine focused on: '{category}'.")
            lines.append("You MUST aggressively prioritize exercises from the list that fit this target. Exclude exercises that are completely irrelevant to this goal.")
        
        lines.append("\nRespond ONLY with a valid JSON array of integer IDs. Example: [1, 5, 8, 12]. Do not include any markdown formatting like ```json, just the raw array.")
        prompt = "\n".join(lines)
        
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return [getattr(ex, 'id') for ex in all_exercises[:5]]
            
        client = genai.Client(api_key=self.api_key)
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction="You are an AI that outputs pure JSON lists of integers. No text.",
                    temperature=0.7,
                )
            )
            text = response.text
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return [int(i) for i in json.loads(match.group(0))]
            return [int(i) for i in json.loads(text)]
        except Exception as e:
            print(f"AI Generate Error: {e}")
            return [getattr(ex, 'id') for ex in all_exercises[:5]]

    @classmethod
    def analyze_profile(cls, db, user_id: int, lang: str = "en") -> str:
        """Analyze a user's physical profile (weight, height, goal) and recent workout volume."""
        import models
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return "User not found."

        workouts = db.query(models.Workout).filter(models.Workout.user_id == user_id, models.Workout.is_finished == True).order_by(models.Workout.date.desc()).limit(10).all()
        
        prompt = f"""
        Act as an elite fitness and nutrition coach.
        You are analyzing the profile of a user:
        - Weight: {user.weight if user.weight else 'Unknown'} kg
        - Height: {user.height if user.height else 'Unknown'} cm
        - Goal: {user.goal if user.goal else 'General Fitness'}
        - Recent Workouts Logged: {len(workouts)} in recent history.
        
        Based on this data, provide a highly personalized, actionable summary emphasizing:
        1. A brief analysis of their current metrics (e.g. BMI approximation if both weight and height exist).
        2. Specific nutritional and training advice to reach their goal ("{user.goal}").
        3. A motivational closing statement.
        
        CRITICAL INSTRUCTION: You MUST write your ENTIRE analysis and response strictly in the '{lang}' language. Use markdown formatting with bolding and bullet points. Do NOT include any JSON syntax, just the raw markdown string.
        """
        
        service = cls()
        if not service.api_key or service.api_key == "your_gemini_api_key_here":
            return f"*(Modo Demo)* Tu perfil: Peso: {user.weight}kg, Altura: {user.height}cm, Objetivo: {user.goal}. Conecta Gemini para obtener análisis detallados."
            
        client = genai.Client(api_key=service.api_key)
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text
        except Exception as e:
            return f"Hubo un error al generar análisis del perfil: {e}"
