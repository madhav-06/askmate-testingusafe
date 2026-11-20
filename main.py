"""AskMate's web app. Open / for the chat page. Other programs ask POST /api/ask.

Run it on your laptop:  python -m uvicorn main:app --reload --port 8001   then open http://127.0.0.1:8001
On Render the start command is:  uvicorn main:app --host 0.0.0.0 --port $PORT
"""

import os
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import ai
from answer import profile, reply
from catalogue import load_catalogue

HERE = Path(__file__).parent
PER_MINUTE = 10                    # questions one visitor may ask in a minute: your app is public
app = FastAPI(title="AskMate")
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
PRODUCTS = load_catalogue()
_asked = {}                        # visitor -> times of their recent questions


class Question(BaseModel):
    question: str


def _too_fast(visitor):
    now = time.time()
    recent = [t for t in _asked.get(visitor, []) if now - t < 60]
    _asked[visitor] = recent + [now]
    return len(recent) >= PER_MINUTE


@app.get("/")
def chat_page():
    return FileResponse(HERE / "static" / "index.html")


@app.post("/api/ask")
def ask(q: Question, request: Request):
    if _too_fast(request.client.host if request.client else "?"):
        return JSONResponse({"answer": "You are asking very fast. Please wait a minute.", "action": "wait", "products": []}, status_code=429)
    return reply(q.question[:500], PRODUCTS)


@app.get("/healthz")
def health():
    """Is the app up, and which version? The portal and Madhu check this. It never shows a key."""
    return {"ok": True, "app": "askmate", "name": profile()["name"], "products": len(PRODUCTS),
            "version": os.environ.get("RENDER_GIT_COMMIT", "local"), "repo": os.environ.get("RENDER_GIT_REPO_SLUG", ""),
            "ai": ai.status()}
