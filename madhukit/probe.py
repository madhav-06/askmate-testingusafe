"""Small checks that run Python apart from Madhu: a predict step's snippet, and whether an install worked."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SNIPPET_TIMEOUT = 10      # seconds: enough for plain Python; a step that imports a framework sets its own "timeout" (packs.py: 1 to 60)


def run_snippet(root: Path, code: str, timeout: float = SNIPPET_TIMEOUT) -> str:
    """What Python really prints for a predict step. A snippet that never ends is stopped, never waited on."""
    try:
        r = subprocess.run([sys.executable, "-c", code], cwd=root, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return "(it did not finish)"
    return (r.stdout + r.stderr).strip()


def can_import(needs: list[str]) -> bool:
    """An install step finishes when Python can really import what was installed."""
    probe = f"import importlib.util as u,sys;sys.exit(any(u.find_spec(n) is None for n in {needs!r}))"
    return subprocess.run([sys.executable, "-c", probe], capture_output=True, check=False).returncode == 0


LIVE_TIMEOUT = 90         # a free Render app asleep takes about a minute to wake


def _address_problem(url: str) -> str:
    from urllib.parse import urlsplit

    u = urlsplit(url)
    local = u.scheme == "http" and u.hostname in ("127.0.0.1", "localhost")      # trying it on your own laptop first is fine
    if not (u.scheme == "https" or local) or not u.hostname:
        return "Paste the full address Render gave you. It starts with https://"
    return ""


def check_live(url: str, timeout: float = LIVE_TIMEOUT) -> tuple[bool, str]:
    """(True, message) when an AskMate answers at this address. Madhu asks from the student's own laptop, never the portal."""
    import json
    import urllib.request

    url = url.strip().rstrip("/")
    problem = _address_problem(url)
    if problem:
        return False, problem
    try:
        with urllib.request.urlopen(url + "/healthz", timeout=timeout) as r:      # noqa: S310 - the student's own app
            data = json.loads(r.read(65536).decode("utf-8", "replace"))
    except (OSError, ValueError):
        return False, ("Your app did not answer. On Render, open your service and look at the Logs: the last red line says why. "
                       "If it says Deploy live, wait a minute and try again.")
    if not isinstance(data, dict) or data.get("app") != "askmate":
        return False, "Something answered, but it is not your AskMate. Check that you pasted your own app's address."
    return True, f"Your AskMate is online at {url}. Anyone with this address can use it now."
