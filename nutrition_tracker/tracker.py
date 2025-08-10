import os
import json
from typing import Optional, Dict, List, Any
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment.")

genai.configure(api_key=GEMINI_API_KEY)

PROMPT_TEMPLATE = (
    "Give me the nutrition facts for {amount} {food}. "
    "Return calories, protein (g), carbs (g), and fat (g) as numbers in JSON format. "
    "If you cannot determine a value for any field, return 0 for that field (do not use null, empty, or omit the field). "
    "Only return the JSON object."
)

import re

def get_nutrition_from_gemini(food: str, amount: float) -> Optional[Dict[str, float]]:
    prompt = PROMPT_TEMPLATE.format(food=food, amount=amount)
    model = genai.GenerativeModel("gemini-2.5-flash")
    text = None
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Remove code block markers and leading 'json'
        text = text.lstrip("` \n")
        if text.lower().startswith("json"):
            text = text[4:].lstrip(" \n")
        # Extract the first JSON object from the response
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in Gemini response")
        json_str = match.group(0)
        data = json.loads(json_str)
        # Normalize keys
        key_map = {
            "protein (g)": "protein",
            "carbs (g)": "carbs",
            "fat (g)": "fat",
            "protein_g": "protein",
            "carbs_g": "carbs",
            "fat_g": "fat",
        }
        for old, new in key_map.items():
            if old in data:
                data[new] = data.pop(old)
        # Ensure all required keys are present
        for key in ("calories", "protein", "carbs", "fat"):
            if key not in data:
                raise ValueError(f"Missing key: {key}")
        # Coerce any None or missing values to 0 as a fallback
        return {
            "calories": float(data["calories"]), 
            "protein": float(data["protein"]), 
            "carbs": float(data["carbs"]) ,
            "fat": float(data["fat"]), 
        }
    except Exception as e:
        print(f"Error parsing Gemini nutrition response: {e}\nRaw response: {text}")
        return None

# --- Nutrition Totals from DB ---
from nutrition_tracker.db import AsyncSessionLocal
from nutrition_tracker.models import User, NutritionLog
from sqlalchemy import select, func
from datetime import datetime

async def get_nutrition_totals_from_db(
    user_id: str, start_date: str = None, end_date: str = None
) -> list[dict]:
    """
    Returns a list of daily nutrition totals for the user from the database.
    Each item: { "date": "YYYY-MM-DD", "calories": float, "protein": float, "carbs": float, "fat": float }
    """
    async with AsyncSessionLocal() as session:
        # Get user row
        user = (await session.execute(select(User).where(User.user_id == user_id))).scalar_one_or_none()
        if not user:
            return []

        # Build query
        query = (
            select(
                func.date(NutritionLog.timestamp).label("date"),
                func.sum(NutritionLog.calories).label("calories"),
                func.sum(NutritionLog.protein).label("protein"),
                func.sum(NutritionLog.carbs).label("carbs"),
                func.sum(NutritionLog.fat).label("fat"),
            )
            .where(NutritionLog.user_id == user.id)
        )

        # Date filtering
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.where(NutritionLog.timestamp >= start)
            except Exception:
                pass
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d")
                # Add 1 day to include the end date fully
                end = end.replace(hour=23, minute=59, second=59)
                query = query.where(NutritionLog.timestamp <= end)
            except Exception:
                pass

        query = query.group_by(func.date(NutritionLog.timestamp)).order_by(func.date(NutritionLog.timestamp))

        result = await session.execute(query)
        rows = result.fetchall()
        return [
            {
                "date": str(row.date),
                "calories": float(row.calories or 0),
                "protein": float(row.protein or 0),
                "carbs": float(row.carbs or 0),
                "fat": float(row.fat or 0),
            }
            for row in rows
        ]

# --- Dish Suggestion via Gemini ---
def suggest_dishes_from_gemini(ingredients: List[str]) -> Optional[List[str]]:
    prompt = (
        "You are a helpful kitchen assistant. Suggest 3 creative, healthy dish names using ONLY these ingredients: "
        f"{', '.join(ingredients)}. "
        "Return a JSON array of 3 dish names (strings). Do not include any text or explanation, only the JSON array."
    )
    model = genai.GenerativeModel("gemini-2.0-flash")
    text = None
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = text.lstrip("` \n")
        if text.lower().startswith("json"):
            text = text[4:].lstrip(" \n")
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if not match:
            raise ValueError("No JSON array found in Gemini response")
        json_str = match.group(0)
        data = json.loads(json_str)
        if not isinstance(data, list) or not all(isinstance(d, str) for d in data):
            raise ValueError("Response is not a list of strings")
        return data
    except Exception as e:
        print(f"Error parsing Gemini dish suggestion response: {e}\nRaw response: {text}")
        return None
