"""The Try it table: a few example inputs for the function a step is about, what the student's code gives now, and what
it should give. It makes the ask concrete without giving away the code (team lead, 6 Nov: "I did not understand the ask").

A step opts in with {"examples": {"call": "menu:clean_name", "cases": [{"args": ["  MASALA Dosa "], "want": "masala dosa"}]}}.
The student's function runs in a child process with a time limit, the same way the Customer Line does, so no code of
theirs can hang or crash Madhu.
"""

from __future__ import annotations

import json

from madhukit.errors import show_spaces

TIME_LIMIT_S = 5


def _show(value: object) -> str:
    """A value as the student would write it in Python, with invisible spaces shown as dots."""
    if isinstance(value, str):
        return show_spaces(json.dumps(value))
    if isinstance(value, list) and value and all(isinstance(x, list) for x in value):
        return show_spaces("[" + ", ".join("(" + ", ".join(json.dumps(y) for y in x) + ")" for x in value) + "]")
    return show_spaces(json.dumps(value))


def run(root, spec: dict) -> list[dict]:  # noqa: ANN001
    """[{input, got, want, ok}]. If the code cannot even run, every row says so: the Customer Line shows the error itself."""
    from madhukit.customers import run_child

    cases = spec.get("cases", [])
    out = run_child(root, "madhukit.run_examples", {"call": spec["call"], "cases": cases}, TIME_LIMIT_S)
    results = out.get("results") or [{"error": "your code did not run"} for _ in cases]
    rows = []
    for case, got in zip(cases, results):
        shown_in = case.get("show") or ", ".join(_show(a) for a in case["args"])   # "show" names a long input briefly
        if "error" in got:
            rows.append({"input": shown_in, "got": got["error"], "want": _show(case["want"]), "ok": False})
        else:
            rows.append({"input": shown_in, "got": _show(got["got"]), "want": _show(case["want"]), "ok": got["got"] == case["want"]})
    return rows
