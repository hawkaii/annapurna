# Annapurna Kitchen Assistant (MCP Starter for Puch AI)

Annapurna is a WhatsApp-based kitchen assistant powered by Puch AI and Gemini. It helps users manage their pantry, scan grocery bills, get smart recipe suggestions, and track nutrition—all through simple image and text interactions. This project is a Model Context Protocol (MCP) server starter, ready to connect with Puch AI and extend with your own tools.

---

## Features

- **Grocery Bill OCR**: Scan grocery bills (image upload) and extract purchased items using Azure AI Vision OCR. Inventory is persistent per user in PostgreSQL.
- **Smart Inventory Management**: Automatically update your pantry/inventory from grocery bills (PostgreSQL-backed).
- **AI-Powered Recipe Suggestions**: Get creative, healthy dish ideas based on your available ingredients (Gemini-powered).
- **Nutrition Tracker**: Log foods, extract nutrition facts via Gemini, and view your nutrition scoreboard (calories, protein, carbs, fat) — all data stored in PostgreSQL.
- **WhatsApp Integration**: Designed for seamless use with Puch AI’s WhatsApp bot.
- **Bearer Token Authentication**: Secure, Puch-compatible authentication.
- **PostgreSQL Database**: All user data is stored in a PostgreSQL database for reliability and scalability.

---

## Architecture

```mermaid
graph TB
    %% User Interfaces
    WA[📱 WhatsApp User] 
    WEB[🌐 Web App<br/><i>Coming Soon</i>]
    MOB[📱 Mobile App<br/><i>Future</i>]
    
    %% Middleware Layer
    PUCH[🤖 Puch AI Agent<br/>Message Router]
    
    %% Backend Services
    MCP[🔧 MCP Server<br/>FastMCP + Bearer Auth]
    API[🔌 REST API<br/><i>Future</i>]
    
    %% Core Tools
    subgraph "🛠️ MCP Tools"
        OCR[📄 Grocery Bill OCR<br/>Azure Vision]
        NUT[🥗 Nutrition Tracker<br/>Gemini AI]
        REC[👨‍🍳 Recipe Suggestions<br/>Gemini AI]
        INV[📦 Inventory Manager]
        VAL[✅ Validation Tool]
    end
    
    %% External APIs
    subgraph "🌍 External APIs"
        AZURE[☁️ Azure AI Vision<br/>OCR Service]
        GEMINI[🧠 Google Gemini<br/>LLM for Nutrition & Recipes]
    end
    
    %% Database
    DB[(🗄️ PostgreSQL Database<br/>Users, Nutrition, Inventory)]
    
    %% Connections
    WA --> PUCH
    WEB -.-> API
    MOB -.-> API
    
    PUCH --> MCP
    API -.-> MCP
    
    MCP --> OCR
    MCP --> NUT
    MCP --> REC
    MCP --> INV
    MCP --> VAL
    
    OCR --> AZURE
    NUT --> GEMINI
    REC --> GEMINI
    
    NUT --> DB
    INV --> DB
    VAL --> DB
    
    %% Styling
    classDef future fill:#f9f9f9,stroke:#999,stroke-dasharray: 5 5
    classDef external fill:#e1f5fe,stroke:#0277bd
    classDef core fill:#f3e5f5,stroke:#7b1fa2
    classDef data fill:#e8f5e8,stroke:#388e3c
    
    class WEB,MOB,API future
    class AZURE,GEMINI external
    class MCP,OCR,NUT,REC,INV,VAL core
    class DB data
```

### Current Architecture Overview

- **Frontend**: WhatsApp (via Puch AI) | Future: Web & Mobile Apps
- **Middleware**: Puch AI agent (routes WhatsApp messages to MCP server)
- **Backend**: Python MCP server with 5 core tools
  - OCR (Azure Vision for grocery bills)
  - Nutrition tracking (Gemini AI + PostgreSQL)
  - Recipe suggestions (Gemini AI)
  - Inventory management (PostgreSQL)
  - User validation (required by Puch)
- **External APIs**: Gemini (Google Generative AI), Azure AI Vision
- **Data Storage**: PostgreSQL (users, nutrition_log, nutrition_totals, inventory tables)

---

## Quick Start

### 1. Install Dependencies

Requires Python 3.11+ and [uv](https://github.com/astral-sh/uv):

```bash
uv venv && uv sync && source .venv/bin/activate
```

### 2. Set Up PostgreSQL

- Install PostgreSQL and create a database (e.g., `annapurna`):
  ```bash
  createdb annapurna
  ```
- (Optional) Create a dedicated user and set a password.

### 3. Configure Environment

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` and set:

```
AUTH_TOKEN=your_secret_token_here
MY_NUMBER=919876543210
VISION_KEY=your_azure_vision_key_here
VISION_ENDPOINT=your_azure_vision_endpoint_here
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/annapurna
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

### 5. Run the MCP Server

```bash
cd mcp-bearer-token
python mcp_starter.py
```

You should see:
```
🚀 Starting MCP server on http://0.0.0.0:8086
```

### 6. Expose Your Server (for Puch AI)

- **Recommended:** Use [ngrok](https://ngrok.com/) to tunnel your local server:
  ```bash
  ngrok http 8086
  ```
- Or deploy to Railway, Render, Heroku, etc.

---

## Usage with Puch AI (WhatsApp)

1. [Open Puch AI on WhatsApp](https://wa.me/+919998881729)
2. Start a conversation
3. Connect your MCP server:
   ```
   /mcp connect https://your-ngrok-url.ngrok.app/mcp your_secret_token_here
   ```
4. Use commands like `log apple 2`, send a grocery bill photo, or ask for a recipe suggestion.

---

## Example API Endpoints

- `POST /log_food` – Log a food and amount (calls Gemini for nutrition, stores in PostgreSQL)
- `POST /nutrition_summary` – Get your daily nutrition summary (from PostgreSQL)

---

## Development & Testing

- No test framework included by default. To add tests, use `pytest`.
- Linting: Use `ruff` or `flake8` for PEP8 compliance.
- All secrets/config in `.env` (see `.env.example`).
- Code style: PEP8, type hints, one import per line, see [AGENTS.md](AGENTS.md) for guidelines.
- **Database migrations:** Use Alembic for schema changes (`alembic revision --autogenerate -m "message"` and `alembic upgrade head`).

---

## Technical Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastMCP (Model Context Protocol)
- **Database**: PostgreSQL with async SQLAlchemy ORM
- **Migrations**: Alembic
- **Authentication**: Bearer token with RSA keys
- **AI Services**: Google Gemini, Azure AI Vision

### Key Dependencies
- `fastmcp` - MCP server framework
- `sqlalchemy[asyncio]` - Async ORM
- `asyncpg` - PostgreSQL async driver
- `alembic` - Database migrations
- `google-generativeai` - Gemini AI client
- `azure-cognitiveservices-vision-computervision` - Azure OCR
- `pydantic` - Data validation
- `python-dotenv` - Environment management

### Deployment Options
- **Development**: Local with ngrok tunneling
- **Production**: Railway, Render, Heroku, DigitalOcean
- **Enterprise**: Kubernetes, Docker Swarm
- **Database**: Managed PostgreSQL (AWS RDS, Google Cloud SQL, etc.)

---

## Roadmap

### ✅ Completed
- [x] PostgreSQL migration (async SQLAlchemy, Alembic)
- [x] Core MCP tools (OCR, nutrition, recipes, inventory)
- [x] WhatsApp integration via Puch AI
- [x] Bearer token authentication
- [x] Gemini AI integration for nutrition & recipes

### 🚧 In Progress
- [ ] Enhanced error handling and logging
- [ ] Performance optimizations
- [ ] Comprehensive test suite

### 🔮 Future Plans

#### Phase 1: API & Documentation (Q1 2025)
- [ ] **REST API**: Complete REST endpoints for all MCP tools
- [ ] **API Documentation**: OpenAPI/Swagger docs
- [ ] **Rate limiting**: Implement proper API rate limiting
- [ ] **Monitoring**: Health checks and metrics endpoints

#### Phase 2: Web Platform (Q2 2025)
- [ ] **Web Application**: React/Vue.js frontend
  - User dashboard for nutrition tracking
  - Recipe discovery and meal planning
  - Inventory management interface
  - Grocery bill upload via web
- [ ] **User Authentication**: OAuth2, JWT tokens
- [ ] **Multi-user Support**: User roles and permissions

#### Phase 3: Mobile Apps (Q3 2025)
- [ ] **iOS App**: Native Swift app
- [ ] **Android App**: Native Kotlin app
- [ ] **Features**:
  - Camera integration for grocery bills
  - Barcode scanning for products
  - Offline nutrition logging
  - Push notifications for meal reminders

#### Phase 4: Advanced Features (Q4 2025)
- [ ] **AI Meal Planning**: Weekly meal plans based on inventory
- [ ] **Smart Shopping Lists**: Auto-generated based on recipes
- [ ] **Nutrition Goals**: Personalized targets and progress tracking
- [ ] **Recipe Sharing**: Community features
- [ ] **Integration APIs**: Connect with fitness apps, smart scales
- [ ] **Voice Assistant**: Alexa/Google Home integration

#### Phase 5: Enterprise & Scale (2026+)
- [ ] **Multi-tenant SaaS**: White-label solutions
- [ ] **Advanced Analytics**: Nutrition insights and trends
- [ ] **Dietitian Portal**: Professional nutrition counseling tools
- [ ] **Enterprise Cafeteria**: Bulk meal planning for organizations

---

## Resources

- [Puch AI MCP Docs](https://puch.ai/mcp)
- [Puch AI Discord](https://discord.gg/VMCnMvYx)
- [JSON-RPC 2.0 Spec](https://www.jsonrpc.org/specification)

---

## License

MIT License. See [LICENSE](LICENSE).

---

**Happy coding! 🚀 Use #BuildWithPuch to share your MCP!**
