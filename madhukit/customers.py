"""The Customer Line: tests shown as people.

Each customer is data: what they ask, what a good answer must contain, and what it must never say. Every unhappy
customer shows what was wanted against what the bot said, because knowing only that something failed teaches little.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from madhukit.errors import show_spaces, translate

TIME_LIMIT_S = 10


def judge(want: dict, said: str, meta: dict | None = None) -> bool:
    """True if the reply is a good one. `must` = all of these, `any` = at least one, `never` = none of these.
    A bot that replies with a dict (AskMate does) is also judged on what it decided: `action` must be that action, and
    every code in `products` must be among the products it named."""
    text = (said or "").casefold()
    if not all(x.casefold() in text for x in want.get("must", [])):
        return False
    options = want.get("any", [])
    if options and not any(x.casefold() in text for x in options):
        return False
    meta = meta or {}
    if "action" in want and meta.get("action") != want["action"]:
        return False
    if not set(want.get("products", [])) <= set(meta.get("products") or []):
        return False
    return not any(x.casefold() in text for x in want.get("never", []))


def _ask_bot(root: Path, line: dict, customers: list[dict], limit: int) -> dict:
    return run_child(root, "madhukit.run_customers", {"setup": line.get("setup"), "call": line["call"], "customers": customers}, limit)


def run_child(root: Path, module: str, payload: dict, limit: int) -> dict:
    """Run a madhukit child module on the student's code, in their folder, with a time limit. Never raises."""
    with tempfile.TemporaryDirectory() as tmp:
        req, res = Path(tmp) / "req.json", Path(tmp) / "res.json"
        req.write_text(json.dumps(payload), encoding="utf-8")
        env_kit = str(Path(__file__).resolve().parent.parent)
        code = ("import sys,runpy;sys.path.insert(0," + repr(env_kit) + ");sys.argv=['r'," + repr(str(req)) + "," + repr(str(res)) + "];"
                "runpy.run_module(" + repr(module) + ",run_name='__main__')")
        # The built-in fake AI, always: a check must give the same answer every time, and must never spend the student's
        # free AI calls or need a key. AskMate reads ASKMATE_LLM before its .env file.
        env = {**os.environ, "ASKMATE_LLM": "fake"}
        try:
            subprocess.run([sys.executable, "-c", code], cwd=root, capture_output=True, text=True, timeout=limit, check=False, env=env)
        except subprocess.TimeoutExpired:
            return {"stuck": True}
        if not res.exists():
            return {"fatal": "RuntimeError: your code stopped Python before Madhu could finish."}
        return json.loads(res.read_text(encoding="utf-8"))


def run_line(root: Path, line: dict, limit: float | None = None) -> dict:
    """Serve every customer. Returns {happy, total, unhappy[], error}. Never raises, whatever the student's code does.
    `limit` defaults to TIME_LIMIT_S read at CALL time (not frozen at import), so a test can give a loaded gate machine room."""
    limit = TIME_LIMIT_S if limit is None else limit
    customers = line["customers"]
    out = _ask_bot(root, line, customers, limit)
    total = len(customers)
    if out.get("stuck"):
        return {"happy": 0, "total": total, "unhappy": [], "error": {
            "title": "Your code did not finish", "plain": f"It was still running after {limit} seconds. A loop may never end.",
            "file": "", "line": 0, "detail": ""}}
    if out.get("fatal"):
        return {"happy": 0, "total": total, "unhappy": [], "error": translate(out["fatal"])}
    unhappy, crash = [], None
    for c, r in zip(customers, out["results"]):
        if r.get("crash") and crash is None:
            crash = translate(r["crash"])
        if r.get("crash") or not judge(c.get("want", {}), r["said"], r.get("meta")):
            unhappy.append({"name": c["name"], "ask": show_spaces(c["ask"]), "wanted": c.get("wanted", ""),
                            "said": "(the bot crashed)" if r.get("crash") else r["said"]})
    return {"happy": total - len(unhappy), "total": total, "unhappy": unhappy, "error": crash}
