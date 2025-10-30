# 🧠 Language Simplifier — Telegram WebApp + OpenAI

AI-powered Telegram WebApp that adapts any English text to your chosen CEFR level (B1/B2/C1) in real time.

## 🚀 Features
- Telegram WebApp with real-time streaming via WebSocket
- Text adaptation powered by OpenAI (`gpt-4o-mini`)
- Clean FastAPI backend
- aiogram v3 bot with WebApp integration

## 🛠️ Setup

```bash
git clone https://github.com/YOUR_USERNAME/language-simplifier.git
cd language-simplifier
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.server:app --reload
```
Then start the Telegram bot:
```bash
python bot/bot.py
```
Open the WebApp from the bot message.
