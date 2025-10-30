from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket

from .security import verify_init_data, parse_init_data_for_app
from .settings import settings
from .ws_adapt import ws_adapt_handler

app = FastAPI(title="AdaptArticleApp")

@app.get("/", response_class=PlainTextResponse)
async def root():
    return "ok"

@app.get("/webapp", response_class=HTMLResponse)
async def webapp():
    with open("app/webapp.html", "r", encoding="utf-8") as f:
        return f.read()


class VerifyRequest(BaseModel):
    init_data: str

@app.post("/api/verify")
async def api_verify(req: VerifyRequest):
    try:
        ok = verify_init_data(req.init_data, bot_token=settings.bot_token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"bad init_data: {e}")
    if not ok:
        raise HTTPException(status_code=401, detail="invalid signature")

    data = parse_init_data_for_app(req.init_data)
    return {"ok": True, "user": data.get("user"), "query_id": data.get("query_id"), "auth_date": data.get("auth_date")}

@app.websocket("/ws/adapt")
async def ws_adapt(ws: WebSocket):
    await ws_adapt_handler(ws)


app.mount("/webapp", StaticFiles(directory="webapp/dist", html=True), name="webapp")

@app.get("/webapp", response_class=HTMLResponse)
async def webapp_index():
    with open("webapp/dist/index.html", "r", encoding="utf-8") as f:
        return f.read()
