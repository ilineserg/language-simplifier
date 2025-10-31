# 🧠 Language Simplifier — Telegram WebApp + OpenAI

AI-powered Telegram WebApp that adapts **English texts** to a chosen **CEFR level** (B1/B2/C1) in real time.
Backend: **FastAPI** + **WebSocket** streaming • Bot: **aiogram v3** • Frontend: **Vite + TypeScript**.

---

## ✨ Features

* Telegram **WebApp** with token-by-token **real-time streaming** over WebSocket
* Text adaptation via **OpenAI** (default model: `gpt-4o-mini`)
* **FastAPI** backend with Telegram WebApp **initData verification**
* **aiogram v3** bot that opens the WebApp inside Telegram
* Production-ready details: structured logging, graceful shutdown, simple anti-flood

---

## 🧩 Requirements

* **Python** 3.11+
* **Node.js** 18+ and **npm**
* A **Telegram Bot Token** (from **@BotFather**)
* An **OpenAI API Key** (or plug any other provider you add)

---

## 🔐 Environment

Create `.env` from the example and fill in your values:

```bash
cp .env.example .env
```

`.env` (example):

```
BOT_TOKEN=123456:ABC-DEF...              # from @BotFather
PUBLIC_BASE_URL=https://your-domain.tld  # public HTTPS (for Telegram WebApp)
HOST=0.0.0.0
PORT=8000

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

> **Do not commit** your real `.env`. Keep secrets out of git.

---

## 📦 Installation

```bash
git clone https://github.com/YOUR_USERNAME/language-simplifier.git
cd language-simplifier

# Python deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend (Vite + TypeScript)

**Development** (Vite dev server on :5173, proxy to FastAPI on :8000):

```bash
cd webapp
npm i
npm run dev
```

**Production build** (served by FastAPI):

```bash
cd webapp
npm i
npm run build   # creates webapp/dist
```

> FastAPI mounts `/webapp` to serve the built frontend from `webapp/dist`.

---

## ▶️ Run (Backend + Bot)

Start **FastAPI** (serves API, WS, and `/webapp` if built):

```bash
uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
```

Start **Telegram bot**:

```bash
python bot/bot.py
```

Open Telegram → your bot → **/start** → press **Open Language Simplifier**.

> For local testing via Telegram, you’ll need a **public HTTPS** URL (e.g., **ngrok**) set in `PUBLIC_BASE_URL`.

---

## 🧪 Quick Check

* WebApp header shows **verified** (initData check passed).
* Paste any English text, choose **B1/B2/C1**, click **Start stream** → tokens appear live.
* If you only see `— done —` with no tokens:

  * confirm `OPENAI_API_KEY` and model,
  * check outbound network access,
  * see backend logs for `provider error`.

---

## 🗂 Project Structure (key parts)

```
app/
  server.py            # FastAPI app, static mount (/webapp), API routes
  ws_adapt.py          # WebSocket handler (initData verify, token stream)
  providers.py         # OpenAI streaming provider
  prompting.py         # CEFR-aware prompts
  security.py          # Telegram WebApp initData verification
  settings.py          # Pydantic (pydantic-settings v2)
bot/
  bot.py               # aiogram v3 bot (logging, rate-limit, commands)
webapp/
  index.html           # Vite entry (dev) → built to /dist for prod
  vite.config.ts       # dev proxy for /api and /ws
  tsconfig.json
  package.json
  src/                 # TypeScript (main.ts, ws.ts, theme.ts, ui.ts, telegram.d.ts)
  styles/              # CSS
  dist/                # (build output; not tracked in git)
```

---

## 🧹 .gitignore (important)

Ensure artifacts and secrets are ignored:

```
# Python
__pycache__/
*.py[cod]
.venv/
.env
.env.*

# Node/Vite
node_modules/
dist/
*.log

# IDE
.vscode/
.idea/
*.iml

# OS
.DS_Store
Thumbs.db
```

If you changed `.gitignore` after some files were already committed:

```bash
git rm -r --cached .
git add .
git commit -m "Apply .gitignore and retrack"
```

---

## 🚀 Deploy Notes

* **Build frontend** on server/CI **before** starting FastAPI:

  ```bash
  cd webapp && npm ci && npm run build
  ```
* Start backend (serving `/webapp` from `webapp/dist`):

  ```bash
  uvicorn app.server:app --host 0.0.0.0 --port 8000
  ```
* Ensure `PUBLIC_BASE_URL` is a valid **HTTPS** domain reachable by Telegram.

> With Docker/Render/Fly.io, add a **frontend build step** in the image or CI pipeline.

---

## ❓ Troubleshooting

* **“invalid init_data”** in WebApp: open via the **bot button**, not by direct URL.
* **No streaming tokens**:

  * verify `OPENAI_API_KEY` / model and account quota,
  * check FastAPI logs for `provider error`,
  * confirm reverse proxy forwards **WebSocket** (`Upgrade`/`Connection` headers).
* **WS over HTTPS fails**: verify TLS and WS pass-through on your proxy.

---

## 📄 License

MIT
