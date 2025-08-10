# Annapurna WhatsApp Bot – Plan (PostgreSQL Edition)

## Overview

Annapurna is a WhatsApp-based kitchen assistant powered by Puch AI and Gemini. It helps users manage their pantry, scan grocery bills, get smart recipe suggestions, and track nutrition—all through simple image and text interactions. All persistent data is now stored in PostgreSQL for reliability and scalability.

---

## Core Features (Current)

### 1. Smart Inventory Scan
- [x] Grocery Bill Scan (Image → Inventory Update, via Azure Vision OCR, persistent in PostgreSQL)
- [ ] Fridge & Pantry Scan (Image → Ingredient List) *(Planned)*

### 2. AI-Powered Recipe Suggestion
- [x] "Cook Now" Menu (Text → Recipe Suggestion, via Gemini)
- [x] Dish Suggestion (Ingredient List → Dish Names, via Gemini)
- [ ] Recipe Card (Static Image) *(Planned)*

### 3. Nutrition Tracker (via Gemini)
- [x] Log food via command (logs to PostgreSQL)
- [x] Use Gemini (Google Generative AI) to extract nutrition data
- [x] Store logs per user in PostgreSQL
- [x] View nutrition scoreboard (nutrition_totals table)
- [x] View daily nutrition summary

---

## System Architecture (Current)

- **Frontend:** WhatsApp (user sends images/text)
- **Middleware:** Puch AI agent receives and routes messages
- **Backend:** Python agent (MCP server) with:
  - OCR (grocery bill scan, Azure Vision)
  - Inventory management (PostgreSQL)
  - Nutrition tracker (Gemini, PostgreSQL)
  - Recipe/dish suggestion (Gemini)
- **External APIs:**
  - Gemini LLM (nutrition, recipes)
  - Microsoft Azure AI Vision (OCR)
- **Data Storage:**
  - PostgreSQL: tables for users, inventory, nutrition_log, nutrition_totals, etc.
- **Static Assets:** *(Planned: recipe images)*

---

## Nutrition Tracker API Design (Current)

- `get_nutrition(user_id: str, food: str, amount: float) -> dict`  
  Prompts Gemini for nutrition facts, logs to PostgreSQL, returns nutrition info.
- `nutrition_board(user_id: str) -> dict`  
  Returns running nutrition totals for the user from PostgreSQL.
- `lock_dish(user_id: str, dish: str, nutrition: dict) -> dict`  
  Logs a custom/suggested dish and updates scoreboard in PostgreSQL.
- `scan_grocery_bill(user_id: str, puch_image_data: str) -> list`  
  OCRs grocery bill and updates inventory in PostgreSQL.

---

## WhatsApp UX (Nutrition)

- **Log Food:**
  - User: `log apple 2`
  - Bot: "Logged 2 apples. Calories: 190, Protein: 0.6g, ..."
- **View Summary:**
  - User: `summary`
  - Bot: "Today: Calories: 1200, Protein: 30g, Carbs: 150g, Fat: 40g"

---

## Implementation Steps (Current)

1. **Gemini Integration**
    - [x] Use `google-generativeai` Python package
    - [x] Prompt template for nutrition extraction
    - [x] Gemini API key in `.env`
2. **Core Nutrition Logic**
    - [x] Implemented in `nutrition_tracker/tracker.py` (PostgreSQL-backed)
3. **Database**
    - [x] PostgreSQL with async SQLAlchemy ORM
    - [x] Alembic for migrations
    - [x] Tables: users, nutrition_log, nutrition_totals, inventory
    - [x] All tool logic uses ORM queries
    - [x] `.env` includes `DATABASE_URL`
    - [x] Documentation and `.env.example` updated
4. **REST API Layer**
    - [ ] *(Planned: not yet implemented, MCP tools only)*
5. **WhatsApp Bot Integration**
    - [ ] *(Planned: not yet integrated, MCP tools ready)*
6. **Testing & Documentation**
    - [x] Manual and tool-based testing
    - [x] Updated README and `.env.example` with new config

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
| Log food            | log apple 2      | /log_food           | PostgreSQL | Nutrition info         |
| View summary        | summary          | /nutrition_summary  | PostgreSQL | Daily totals           |

---

## Notes
- Nutrition logic is reusable for web/mobile apps via REST API
- PostgreSQL is the default and recommended database
- Gemini is used for nutrition extraction (no external food API needed)
- All credentials/secrets in `.env`/`.env.example`

---
