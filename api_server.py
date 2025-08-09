from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date
from nutrition_tracker.tracker import get_nutrition_from_gemini
from nutrition_tracker.db import log_food, get_daily_summary

app = FastAPI()

class LogFoodRequest(BaseModel):
    user_id: str
    food: str
    amount: float

class LogFoodResponse(BaseModel):
    food: str
    amount: float
    calories: float
    protein: float
    carbs: float
    fat: float

class SummaryRequest(BaseModel):
    user_id: str
    date: date

class SummaryResponse(BaseModel):
    calories: float
    protein: float
    carbs: float
    fat: float

@app.post("/log_food", response_model=LogFoodResponse)
def log_food_endpoint(req: LogFoodRequest):
    nutrition = get_nutrition_from_gemini(req.food, req.amount)
    if not nutrition:
        raise HTTPException(status_code=400, detail="Could not get nutrition info from Gemini.")
    log_food(req.user_id, req.food, req.amount, nutrition)
    return LogFoodResponse(food=req.food, amount=req.amount, **nutrition)

@app.post("/nutrition_summary", response_model=SummaryResponse)
def nutrition_summary_endpoint(req: SummaryRequest):
    summary = get_daily_summary(req.user_id, req.date)
    return SummaryResponse(**summary)
