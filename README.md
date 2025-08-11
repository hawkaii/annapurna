
# Annapurna Kitchen Assistant (MCP Starter for Puch AI)
<div align="center">

<a href="https://tinyurl.com/annapurna-bot" style="text-decoration:none;">
  <img src="https://img.shields.io/badge/Chat%20on%20WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white" alt="Chat on WhatsApp"/>
</a>

</div>

- 🌐 **Website:** to get more info visit [https://annapurna.hawkaii.me](https://annapurna.hawkaii.me)
- 🎬 **Demo:**

  [![Watch the demo video](https://img.youtube.com/vi/uxZUkDU_gno/0.jpg)](https://youtu.be/uxZUkDU_gno?si=cx8ju_32rViGNdMn)

Annapurna is a WhatsApp-based kitchen assistant powered by Puch AI and Gemini. It helps users manage their pantry, scan grocery bills, get smart recipe suggestions, and track nutrition—all through simple image and text interactions. This project is a Model Context Protocol (MCP) server starter, ready to connect with Puch AI and extend with your own tools.

---

## 🚀 How I Deployed This Project on Railway

Deploying this WhatsApp MCP project to the cloud was a breeze, thanks to Railway’s one-click deployment and my custom template. Here’s exactly how I did it, so you can follow the same steps!

### Why Railway?

I chose [Railway](https://railway.app/) because it lets me deploy, manage, and scale my Python backend and PostgreSQL database with zero DevOps hassle. It’s perfect for keeping my WhatsApp AI bot online 24/7, and the dashboard makes everything super easy to monitor and update.

---

### 🛠️ My Deployment Steps

#### 1. Created a Railway Template

I built a custom Railway template for this project, which you can use too:
[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/whatsapp-mcp)

Just click the button above, or visit [https://railway.com/deploy/whatsapp-mcp](https://railway.com/deploy/whatsapp-mcp), and Railway will guide you through the setup.

#### 2. Connected My GitHub Repo

Railway asked me to link my GitHub account and select this project’s repository. It automatically detected the Python backend and set up the build environment for me.

#### 3. Set Up Environment Variables

Following my own `railway.md` and `.env.example`, I added all the required secrets and API keys in the Railway dashboard:

```env
AUTH_TOKEN=your_secret_token
VISION_KEY=your_azure_vision_key
VISION_ENDPOINT=your_azure_vision_endpoint
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql+asyncpg://username:password@host:port/dbname
```

> **Tip:** You’ll get the `DATABASE_URL` after adding the PostgreSQL plugin in the next step.

#### 4. Added a PostgreSQL Database

Railway makes it super simple to add a database:
- I clicked “Add Plugin” and chose **PostgreSQL**.
- Railway generated a secure `DATABASE_URL` for me, which I copied into my environment variables.

#### 5. Deployed with One Click

With everything set, I hit **Deploy** in the dashboard. The logs showed `🚀 Starting MCP server...`—and just like that, my backend was live!

#### 6. Connected to WhatsApp via Puch AI

I made sure my [Puch AI](https://puch.ai/) account was set up and linked to my WhatsApp number. Then, I used the public Railway URL as my webhook/backend endpoint in Puch AI.

#### 7. Monitored and Scaled

Railway’s dashboard let me watch logs, check metrics, and scale the app as needed. If I ever need to redeploy or roll back, it’s just a click away.

---

### 💡 Why This Approach Rocks

- **Personalized:** I built and tested this template myself, so you know it works!
- **Zero DevOps:** No server headaches—Railway handles everything.
- **Fast Iteration:** I can update code, redeploy, and see changes instantly.
- **Secure:** All secrets and API keys are managed in the dashboard.

---

**Want to try it yourself?**  
Just use my template: [https://railway.com/deploy/whatsapp-mcp](https://railway.com/deploy/whatsapp-mcp)

If you get stuck, check out my `railway.md` for more tips, or reach out!

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
... (rest of the file unchanged) ...
