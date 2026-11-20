"""Madhu's link to the portal. Optional: Madhu works fully offline, and only Madhu needs this.

Madhu sends step changes and scores. Code goes only when the student clicks Ask Madhu. The token stays in .madhu/token,
which is never committed.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TIMEOUT_S = 15
WAIT_S = 60          # Ask and connect: a hosted portal may be waking up, and Madhu's model can take a while


class Portal:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.url = self._read_url()
        self._token = self._read("token")

    @property
    def token(self) -> str:
        """The sign-in. Read again while it is missing: the student connects in a SECOND terminal, and the Madhu already
        running here must notice, or the portal never hears another step (found in the first student test)."""
        if not self._token:
            self._token = self._read("token")
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        self._token = value

    def _read(self, name: str) -> str:
        try:
            return (self.root / ".madhu" / name).read_text(encoding="utf-8").strip()
        except OSError:
            return ""

    def _read_url(self) -> str:
        try:
            return json.loads((self.root / "madhu.config.json").read_text(encoding="utf-8")).get("portal", "").rstrip("/")
        except (OSError, ValueError):
            return ""

    def _call(self, path: str, data: dict | None = None, form: bool = False, timeout: float = TIMEOUT_S) -> dict | None:
        """The JSON reply, or None if the portal cannot be reached. A sleeping portal must never stop the student."""
        body, headers = None, {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if data is not None:
            body = urllib.parse.urlencode(data).encode() if form else json.dumps(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded" if form else "application/json"
        req = urllib.request.Request(self.url + path, data=body, headers=headers, method="POST" if data is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 - the URL is our own portal
                return json.loads(r.read().decode())
        except (OSError, ValueError, urllib.error.URLError):
            return None

    def link(self, wait_s: int = 180) -> bool:
        """Show a code, wait while the student confirms it in the portal, then keep the token."""
        got = self._call("/kit/link", {}, timeout=WAIT_S)
        if not got:
            print("Could not reach the portal. Check your internet, then try again.")
            return False
        code = got["code"]
        print("Connect Madhu to your portal account. You do this once.")
        print("  1. Hold Ctrl and click this link:")
        print(f"     {self.url}/kit/connect?code={code}")
        print(f"  2. The portal shows the code {code}. Check it matches, then click Confirm.")
        print("Waiting for you to confirm ...")
        end = time.monotonic() + wait_s
        while time.monotonic() < end:
            time.sleep(2)
            token = (self._call("/kit/claim", {"code": code}, form=True) or {}).get("token")
            if token:
                folder = self.root / ".madhu"
                folder.mkdir(exist_ok=True)
                (folder / "token").write_text(token, encoding="utf-8")
                self.token = token
                print("Connected. The portal now follows your steps, and you can ask Madhu questions. You can close this terminal.")
                return True
        print("That took more than 3 minutes. Type python madhu.py connect to try again.")
        return False

    def report(self, data: dict) -> None:
        if self.token and self.url:
            self._call("/kit/report", data)

    def todo(self, ticket: str) -> list[dict]:
        if not (self.token and self.url and ticket):
            return []
        return (self._call(f"/kit/todo?ticket={urllib.parse.quote(ticket)}") or {}).get("items", [])

    def ask(self, ticket: str, question: str, view: dict, code: str) -> str:
        if not self.url or not self.token:
            return "Connect me first: run python madhu.py connect in a terminal."
        line = view.get("line") or {}
        bad = (line.get("unhappy") or [{}])[0]
        reply = self._call("/kit/ask", {
            "ticket": ticket, "question": question, "code": code, "title": view.get("title", ""),
            "step": (view.get("step") or {}).get("title", ""), "score": f"{line.get('happy', 0)} of {line.get('total', 0)}",
            "failing": f"{bad.get('ask', '')}: wanted {bad.get('wanted', '')}, got {bad.get('said', '')}"}, timeout=WAIT_S)
        return (reply or {}).get("reply") or "I cannot reach the portal right now. Try a hint instead."
