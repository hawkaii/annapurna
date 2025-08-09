from typing import Dict, List
from datetime import datetime, date
from .models import get_db_connection

def log_food(user_id: str, food: str, amount: float, nutrition: Dict[str, float]):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO food_log (user_id, food, amount, calories, protein, carbs, fat, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        food,
        amount,
        nutrition["calories"],
        nutrition["protein"],
        nutrition["carbs"],
        nutrition["fat"],
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

def get_daily_summary(user_id: str, for_date: date) -> Dict[str, float]:
    conn = get_db_connection()
    cur = conn.cursor()
    start = datetime.combine(for_date, datetime.min.time()).isoformat()
    end = datetime.combine(for_date, datetime.max.time()).isoformat()
    cur.execute('''
        SELECT SUM(calories) as calories, SUM(protein) as protein, SUM(carbs) as carbs, SUM(fat) as fat
        FROM food_log
        WHERE user_id = ? AND timestamp BETWEEN ? AND ?
    ''', (user_id, start, end))
    row = cur.fetchone()
    conn.close()
    return {
        "calories": row["calories"] or 0,
        "protein": row["protein"] or 0,
        "carbs": row["carbs"] or 0,
        "fat": row["fat"] or 0,
    }
