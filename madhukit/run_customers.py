"""The child process that talks to the student's code.

It runs apart from Madhu for one reason: student code may loop forever or crash. Madhu stops this process after a time
limit and stays alive. Answers go to a file, because student code may print anything to the screen.

Usage: python -m madhukit.run_customers <request.json> <result.json>
"""

from __future__ import annotations

import contextlib
import importlib
import io
import json
import sys
import traceback


def _load(ref: str):  # noqa: ANN202
    """"bot:answer" gives the function `answer` from the student's module `bot`."""
    module, name = ref.split(":", 1)
    return getattr(importlib.import_module(module), name)


def _result(said: object) -> dict:
    """A reply as text, plus what the bot decided when it replies with a dict (AskMate: answer, action, products)."""
    if isinstance(said, dict):
        meta = {"action": str(said.get("action", "")), "products": [str(p) for p in said.get("products") or []]}
        return {"said": str(said.get("answer", "")), "meta": meta}
    return {"said": "" if said is None else str(said)}


def _serve(req: dict) -> dict:
    setup = req.get("setup")
    world = _load(setup["call"])(*setup.get("args", [])) if setup else None
    answer = _load(req["call"])
    results = []
    for c in req["customers"]:
        try:
            said = answer(c["ask"], world) if setup else answer(c["ask"])
            results.append(_result(said))
        except Exception:  # noqa: BLE001 - one customer crashing the bot is a result to show, not a failure of Madhu
            results.append({"said": "", "crash": traceback.format_exc()})
    return {"results": results}


def main() -> int:
    request_path, result_path = sys.argv[1], sys.argv[2]
    with open(request_path, encoding="utf-8") as f:
        req = json.load(f)
    sys.path.insert(0, ".")
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            out = _serve(req)
    except BaseException:  # noqa: BLE001 - a syntax error in student code lands here; SystemExit too
        out = {"fatal": traceback.format_exc()}
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(out, f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
