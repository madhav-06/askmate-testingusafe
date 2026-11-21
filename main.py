"""AskMate's web app. Open / for the chat page. Other programs ask POST /api/ask.

Run it on your laptop:  python -m uvicorn main:app --reload --port 8001   then open http://127.0.0.1:8001
On Render the start command is:  uvicorn main:app --host 0.0.0.0 --port $PORT

The owner's pages (/owner) need the ADMIN_TOKEN you set in .env and on Render: open /owner?token=<your token>.
"""

import os
import secrets
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import ai
import config
from answer import _module, load_products, profile, reply

HERE = Path(__file__).parent
PER_MINUTE = 10                    # questions one visitor may ask in a minute: your app is public
app = FastAPI(title="AskMate")
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
PRODUCTS = load_products()
_asked = {}                        # visitor -> times of their recent questions


class Question(BaseModel):
    question: str
    session: str = ""


def _too_fast(visitor):
    now = time.time()
    recent = [t for t in _asked.get(visitor, []) if now - t < 60]
    _asked[visitor] = recent + [now]
    return len(recent) >= PER_MINUTE


def _owner_ok(request):
    """The owner's pages need the secret ADMIN_TOKEN. With no token set, nobody can open them."""
    token = config.setting("ADMIN_TOKEN")
    given = request.query_params.get("token", "") or request.headers.get("x-admin-token", "")
    return bool(token) and secrets.compare_digest(token, given)


@app.exception_handler(Exception)
def _oops(_request, _exc):
    """A crash never shows your code to a stranger. The details are in your terminal or Render's Logs."""
    return JSONResponse({"answer": "Sorry, something went wrong on our side. Please try again.", "action": "error", "products": []}, status_code=500)


@app.get("/")
def chat_page():
    return FileResponse(HERE / "static" / "index.html")


@app.post("/api/ask")
def ask(q: Question, request: Request):
    visitor = request.client.host if request.client else "?"
    if _too_fast(visitor):
        return JSONResponse({"answer": "You are asking very fast. Please wait a minute.", "action": "wait", "products": []}, status_code=429)
    return reply(q.question[:500], PRODUCTS, (q.session or visitor)[:80])


@app.get("/healthz")
def health():
    """Is the app up, and which version? The portal and Madhu check this. It never shows a key."""
    return {"ok": True, "app": "askmate", "name": profile()["name"], "products": len(PRODUCTS), "suggestions": profile().get("suggestions", [])[:3],
            "version": os.environ.get("RENDER_GIT_COMMIT", "local"), "repo": os.environ.get("RENDER_GIT_REPO_SLUG", ""),
            "ai": ai.status()}


@app.get("/owner")
def owner_page(request: Request):
    if not _owner_ok(request):
        return HTMLResponse("<p>The owner's page needs the right token: /owner?token=...</p>", status_code=403)
    owner, logbook = _module("owner"), _module("logbook")
    asked = owner.inbox() if owner else []
    stats = logbook.summary(logbook.read_all()) if logbook else {}
    rows = "".join(f"<li>{_html(q)}</li>" for q in asked[-50:]) or "<li>No questions for you yet.</li>"
    return HTMLResponse(f"<h1>Owner</h1><h2>Customers asking for you</h2><ul>{rows}</ul><h2>Today</h2><pre>{_html(str(stats))}</pre>")


@app.post("/owner/prices")
async def owner_prices(request: Request):
    """New prices while the app runs: send the CSV text as the body. The newest price wins."""
    global PRODUCTS
    prices = _module("prices")
    if not _owner_ok(request) or not prices:
        return JSONResponse({"ok": False, "error": "not allowed"}, status_code=403)
    PRODUCTS = prices.apply_update(PRODUCTS, prices.read_rows((await request.body()).decode("utf-8")))
    return {"ok": True, "products": len(PRODUCTS)}


def _html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
