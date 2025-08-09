# RannaBondhu WhatsApp Bot – Plan (Updated for Gemini Nutrition Extraction)

## Overview

RannaBondhu is a WhatsApp-based kitchen assistant powered by Puch AI and Gemini. It helps users manage their pantry, scan grocery bills, get smart recipe suggestions, and now track nutrition—all through simple image and text interactions.

---

## Core Features

### 1. Smart Inventory Scan
- Fridge & Pantry Scan (Image → Ingredient List)
- Grocery Bill Scan (Image → Inventory Update)

### 2. AI-Powered Recipe Suggestion
- "Cook Now" Menu (Text → Recipe Suggestion)
- Recipe Card (Static Image)

### 3. Nutrition Tracker (NEW, via Gemini)
- Log food via WhatsApp command (e.g., `log apple 2`)
- Use Gemini (Google Generative AI) to extract nutrition data
- Store logs per user in SQLite database
- View daily nutrition summary via WhatsApp (e.g., `summary`)

---

## System Architecture

- **Frontend:** WhatsApp (user sends images/text)
- **Middleware:** Puch AI agent receives and routes messages
- **Backend:** Python agent (FastAPI/MCP server) with:
  - Image analysis (fridge/pantry scan)
  - OCR (grocery bill scan)
  - Inventory management
  - Nutrition tracker (Gemini + SQLite)
  - Recipe suggestion (via Gemini)
- **External APIs:**
  - Gemini Vision/LLM (nutrition, recipes)
  - Microsoft Azure AI Vision (OCR)
- **Data Storage:**
  - SQLite for nutrition logs
  - In-memory or SQLite for inventory
- **Static Assets:** Recipe images stored locally or in cloud storage

---

## Nutrition Tracker API Design

- `log_food(user_id: str, food: str, amount: float) -> dict`  
  Prompts Gemini for nutrition facts, stores in DB, returns nutrition info.
- `get_nutrition_summary(user_id: str, date: str) -> dict`  
  Returns total nutrition for the user for a given day.

---

## WhatsApp UX (Nutrition)

- **Log Food:**
  - User: `log apple 2`
  - Bot: "Logged 2 apples. Calories: 190, Protein: 0.6g, ..."
- **View Summary:**
  - User: `summary`
  - Bot: "Today: Calories: 1200, Protein: 30g, Carbs: 150g, Fat: 40g"

---

## Implementation Steps

1. **Gemini Integration**
    - Use `google-generativeai` Python package
    - Write a prompt template for nutrition extraction
    - Add Gemini API key to `.env`/`.env.example` if not present
2. **Core Nutrition Logic**
    - In `nutrition_tracker/tracker.py`, implement a function to call Gemini and parse nutrition info
3. **Database**
    - Store logs in SQLite as before
4. **REST API Layer**
    - Create `api_server.py` (FastAPI app)
    - Expose endpoints for logging food and getting summaries
5. **WhatsApp Bot Integration**
    - Update `whatsapp_bot.py` to parse `log` and `summary` commands
    - Call REST API endpoints from bot
6. **Testing & Documentation**
    - Test end-to-end: WhatsApp → API → DB → WhatsApp
    - Update README and `.env.example` with new config

---

## Example Directory Structure

```
/ (project root)
|-- nutrition_tracker/
|     |-- __init__.py
|     |-- tracker.py
|     |-- db.py
|     |-- models.py
|-- api_server.py
|-- whatsapp_bot.py
|-- plan.md
|-- .env / .env.example
|-- ...
```

---

## Summary Table (Nutrition)

| User Action         | WhatsApp Command | API Endpoint         | DB         | Bot Reply Type         |
|---------------------|------------------|---------------------|------------|------------------------|
| Log food            | log apple 2      | /log_food           | SQLite     | Nutrition info         |
| View summary        | summary          | /nutrition_summary  | SQLite     | Daily totals           |

---

## Notes
- Nutrition logic is reusable for web/mobile apps via REST API
- SQLite can be swapped for Postgres/MySQL in production
- Gemini is used for nutrition extraction (no external food API needed)
- All credentials/secrets in `.env`/`.env.example`

---
