"""The child process for the Try it table: call one of the student's functions on each example input.

It runs apart from Madhu for the same reason as run_customers: student code may loop forever or crash. Results go to a
file, because student code may print anything.

Usage: python -m madhukit.run_examples <request.json> <result.json>
"""

from __future__ import annotations

import contextlib
import importlib
import io
import json
import sys
import traceback


def _plain(value: object) -> object:
    """A JSON-safe copy, so a dict, a tuple or a number compares the same way on both sides."""
    return json.loads(json.dumps(value, default=repr))


def _serve(req: dict) -> dict:
    module, name = req["call"].split(":", 1)
    fn = getattr(importlib.import_module(module), name)
    out = []
    for case in req["cases"]:
        try:
            out.append({"got": _plain(fn(*case["args"]))})
        except Exception as exc:  # noqa: BLE001 - one bad input is a row to show, not a failure of Madhu
            out.append({"error": f"{type(exc).__name__}: {exc}"[:200]})
    return {"results": out}


def main() -> int:
    request_path, result_path = sys.argv[1], sys.argv[2]
    with open(request_path, encoding="utf-8") as f:
        req = json.load(f)
    sys.path.insert(0, ".")
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            out = _serve(req)
    except BaseException:  # noqa: BLE001 - a syntax error in student code lands here
        out = {"fatal": traceback.format_exc()}
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(out, f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
