"""How AskMate replies, in four steps: understand the question, find the products, decide what to do, then word it.

Code does the first three, so every answer is right. The AI (or AskMate's own sentences) only does the last one.
"""

import json
from pathlib import Path

import ai
from search import decide, find

HERE = Path(__file__).parent
GREETINGS = ("hi", "hello", "hey", "good morning", "good evening", "namaste", "vanakkam")


def profile():
    """Your AskMate's name and greeting, from askmate.json."""
    return json.loads((HERE / "askmate.json").read_text(encoding="utf-8"))


def is_greeting(question):
    q = " ".join(question.lower().replace("?", " ").replace("!", " ").split())
    return q in GREETINGS or q.startswith(("hi ", "hello ", "hey ")) or "who are you" in q


def money(rupees):
    """11500 becomes '₹11,500', the way people read prices."""
    return f"₹{rupees:,}"


def facts_of(codes, products):
    """The facts about the products found: the only things a reply may say."""
    by_code = {p["code"]: p for p in products}
    return [{"code": c, "name": by_code[c]["name"], "category": by_code[c]["category"], "size": by_code[c]["size"],
             "features": by_code[c]["features"], "price": money(by_code[c]["price"])} for c in codes if c in by_code]


def reply(question, products):
    """{answer, action, products, model, resting}: what AskMate says, and what it decided."""
    if is_greeting(question):
        return {"answer": profile()["greeting"], "action": "greet", "products": [], "model": "none", "resting": False}
    codes = find(question, products)
    action = decide(codes)
    text, model, resting = ai.write(question, action, facts_of(codes, products))
    return {"answer": text, "action": action, "products": codes[:10], "model": model, "resting": resting}
