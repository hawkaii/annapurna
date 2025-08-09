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
        return {
            "calories": float(data["calories"]),
            "protein": float(data["protein"]),
            "carbs": float(data["carbs"]),
            "fat": float(data["fat"]),
        }
    except Exception as e:
        print(f"Error parsing Gemini nutrition response: {e}\nRaw response: {text}")
        return None

# --- Dish Suggestion via Gemini ---
def suggest_dishes_from_gemini(ingredients: List[str]) -> Optional[List[str]]:
    prompt = (
        "You are a helpful kitchen assistant. Suggest 3 creative, healthy dish names using ONLY these ingredients: "
        f"{', '.join(ingredients)}. "
        "Return a JSON array of 3 dish names (strings). Do not include any text or explanation, only the JSON array."
    )
    model = genai.GenerativeModel("gemini-2.5-flash")
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
