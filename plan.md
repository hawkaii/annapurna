# RannaBondhu WhatsApp Bot – Plan (Updated for Gemini Nutrition Extraction)

## Overview

RannaBondhu is a WhatsApp-based kitchen assistant powered by Puch AI and Gemini. It helps users manage their pantry, scan grocery bills, get smart recipe suggestions, and now track nutrition—all through simple image and text interactions.

---

## Core Features (Current Progress)

### 1. Smart Inventory Scan
- [x] Grocery Bill Scan (Image → Inventory Update, via Azure Vision OCR, persistent in inventory.txt)
- [ ] Fridge & Pantry Scan (Image → Ingredient List) *(Planned)*

### 2. AI-Powered Recipe Suggestion
- [x] "Cook Now" Menu (Text → Recipe Suggestion, via Gemini)
- [x] Dish Suggestion (Ingredient List → Dish Names, via Gemini)
- [ ] Recipe Card (Static Image) *(Planned)*

### 3. Nutrition Tracker (via Gemini)
- [x] Log food via command (logs to nutrition_log.txt, not SQLite)
- [x] Use Gemini (Google Generative AI) to extract nutrition data
- [x] Store logs per user in nutrition_log.txt
- [x] View nutrition scoreboard (nutrition_totals.txt)
- [ ] View daily nutrition summary *(Planned: currently scoreboard is running total)*

---

## System Architecture (Current)

- **Frontend:** WhatsApp (user sends images/text)
- **Middleware:** Puch AI agent receives and routes messages
- **Backend:** Python agent (MCP server) with:
  - OCR (grocery bill scan, Azure Vision)
  - Inventory management (file-based: inventory.txt)
  - Nutrition tracker (Gemini, file-based: nutrition_log.txt, nutrition_totals.txt)
  - Recipe/dish suggestion (Gemini)
- **External APIs:**
  - Gemini LLM (nutrition, recipes)
  - Microsoft Azure AI Vision (OCR)
- **Data Storage:**
  - Text files: nutrition_log.txt, nutrition_totals.txt, inventory.txt
- **Static Assets:** *(Planned: recipe images)*

---

## Nutrition Tracker API Design (Current)

- `get_nutrition(user_id: str, food: str, amount: float) -> dict`  
  Prompts Gemini for nutrition facts, logs to nutrition_log.txt, returns nutrition info.
- `nutrition_board(user_id: str) -> dict`  
  Returns running nutrition totals for the user from nutrition_totals.txt.
- `lock_dish(user_id: str, dish: str, nutrition: dict) -> dict`  
  Logs a custom/suggested dish and updates scoreboard.
- `scan_grocery_bill(user_id: str, puch_image_data: str) -> list`  
  OCRs grocery bill and updates inventory.txt.

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
    - [x] Implemented in `nutrition_tracker/tracker.py` (file-based logging)
3. **Database**
    - [x] Replaced with text files: nutrition_log.txt, nutrition_totals.txt, inventory.txt
    - [ ] **Planned: PostgreSQL Migration**
        - Use SQLAlchemy (async) for all data models
        - Define tables: users, nutrition_log, nutrition_totals, inventory
        - Add PostgreSQL connection to `.env`
        - Refactor all tool logic to use ORM queries
        - Use Alembic for migrations
        - (Optional) Write migration script to import from text files
        - Test all tools with PostgreSQL
        - Update documentation and .env.example
4. **REST API Layer**
    - [ ] *(Planned: not yet implemented, MCP tools only)*
5. **WhatsApp Bot Integration**
    - [ ] *(Planned: not yet integrated, MCP tools ready)*
6. **Testing & Documentation**
    - [x] Manual and tool-based testing
    - [x] Updated README and `.env.example` with new config

---

## PostgreSQL Migration Plan

1. **Choose an ORM or Database Library**
    - Use SQLAlchemy (async) for robust, scalable DB access
2. **Define Your Database Models**
    - users, nutrition_log, nutrition_totals, inventory
3. **Set Up Database Connection**
    - Add DATABASE_URL to .env
    - Install: `uv pip install sqlalchemy[asyncio] asyncpg alembic`
    - Initialize SQLAlchemy engine/session
4. **Migrate Data (Optional)**
    - Write a script to import from text files to DB
5. **Refactor Tool Logic**
    - Replace file I/O with ORM queries for all tools
6. **Add Migrations**
    - Use Alembic for schema changes
7. **Update README and .env.example**
8. **Test End-to-End**
    - Ensure all tools work with PostgreSQL

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
