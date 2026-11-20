"""How AskMate words its reply.

Code has already decided what to say: which products, and whether to answer, ask which one, or say no. The AI only
makes the sentence sound natural. With no key, or when the AI is busy, AskMate uses its own sentences, and the answer is
just as right. Then the chat page says the AI helper is resting.
"""

import datetime
import time

import httpx

import config

_resting_until = {}               # provider -> the time it may be tried again after it failed
_today = {"day": "", "calls": 0}  # real AI calls today, so a stranger cannot use up your free key


def _names(facts):
    names = [f"{f['name']} ({f['price']})" for f in facts[:3]]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


def fake_reply(action, facts):
    """AskMate's own sentence for each decision. Always right, never fancy."""
    if action == "answer":
        f = facts[0]
        size = f" Size: {f['size']}." if f["size"] else ""
        return f"Yes, we have the {f['name']} {f['category'].lower()} ({f['code']}) for {f['price']}.{size} {f['features']}."
    if action == "ask" and len(facts) <= 3:
        return f"Did you mean {_names(facts)}?"
    if action == "ask":
        return (f"We have {len(facts)} that match, like {_names(facts)}. "
                "Tell me a little more, like the size or your budget.")
    return f"Sorry, {config.COMPANY} does not sell that. I can help with toilets, wash basins, kitchen sinks, bathtubs and taps."


def build_request(messages, model, key, base_url):
    """The request to send to the AI: where, who you are, and what to write. You build this in Sprint 1."""
    return {}


def read_reply(data):
    """The AI's sentence, taken out of the answer it sends back. You write this in Sprint 1."""
    return ""


def instructions(action, facts):
    todo = {"answer": "Tell the customer we have it, with its price.", "ask": "Ask which one they mean, naming each.",
            "refuse": f"Say kindly that {config.COMPANY} does not sell it."}[action]
    return (f"You are the shop assistant of {config.COMPANY}, a shop for toilets, basins, sinks and taps. Write one short, "
            f"friendly reply. {todo} Use ONLY these facts, and copy every name, code and price exactly. Never add a "
            f"product, price, size or promise that is not in the facts. Facts: {facts}")


def keeps_facts(text, facts):
    """Code checks the AI: every product it was given must be named in its reply."""
    return all(f["name"].lower() in text.lower() for f in facts[:3])


def providers():
    """The AIs you have a key for, in the order to try them."""
    found = [("groq", config.GROQ_URL, config.GROQ_KEY, config.GROQ_MODEL), ("gemini", config.GEMINI_URL, config.GEMINI_KEY, config.GEMINI_MODEL)]
    return [p for p in found if p[2]] if config.AI_MODE != "fake" else []


def _budget_left():
    day = datetime.date.today().isoformat()
    if _today["day"] != day:
        _today.update(day=day, calls=0)
    return _today["calls"] < config.DAILY_AI_CALLS


def real_reply(question, action, facts):
    """(the AI's sentence, the model) or (None, '') if no AI could write a good one right now."""
    messages = [{"role": "system", "content": instructions(action, facts)}, {"role": "user", "content": question}]
    for name, url, key, model in providers():
        req = build_request(messages, model, key, url)
        if not req or time.time() < _resting_until.get(name, 0) or not _budget_left():
            continue
        _today["calls"] += 1
        try:
            if "gpt-oss" in model:
                req["json"]["reasoning_effort"] = "low"  # think briefly, so the words fit in the reply
            r = httpx.post(req["url"], headers=req["headers"], json=req["json"], timeout=10)
            r.raise_for_status()
            text = read_reply(r.json())
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, AttributeError):
            _resting_until[name] = time.time() + 60      # rest for a minute, then try again
            continue
        if text and keeps_facts(text, facts):
            return text, model
    return None, ""


def write(question, action, facts):
    """(the reply, which model wrote it, whether the AI helper is resting)."""
    template = fake_reply(action, facts)
    if not providers():
        return template, "fake", False
    text, model = real_reply(question, action, facts)
    return (text, model, False) if text else (template, "fake", True)


def status():
    return {"mode": "fake" if not providers() else "real", "groq": bool(config.GROQ_KEY), "gemini": bool(config.GEMINI_KEY),
            "resting": any(t > time.time() for t in _resting_until.values())}
