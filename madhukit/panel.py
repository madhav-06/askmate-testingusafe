"""The panel: a small local web page that opens beside the code in VS Code.

SECURITY. Any website the student visits could try to reach this local server, so:
  - it listens on 127.0.0.1 only;
  - every request needs this run's random key;
  - the Host header must be ours, which stops DNS rebinding;
  - every POST needs a custom header, which a plain cross-site form cannot send.
"""

from __future__ import annotations

import json
import secrets
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HEADER = "X-Madhu"
_PAGE = Path(__file__).with_name("panel.html")
_BEE = Path(__file__).with_name("bee.jpg")


class Panel:
    def __init__(self, engine, ask=None, port: int = 0, portal_url: str = "") -> None:  # noqa: ANN001
        self.engine = engine
        self.ask = ask                      # the Madhu seam: (question, view) -> reply text
        self.portal_url = portal_url        # for "Still stuck? Ask your mentor", which opens the portal's help form
        self.key = secrets.token_urlsafe(16)
        self.lock = threading.Lock()
        handler = type("Handler", (_Handler,), {"panel": self})
        self.server = ThreadingHTTPServer(("127.0.0.1", port), handler)
        self.port = self.server.server_address[1]

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/?k={self.key}"

    def start(self) -> None:
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()


def open_in_editor(root: Path, file: str, line: int) -> bool:
    """Jump to the line. `code` is on the PATH inside a VS Code terminal. False means the panel shows the place in words."""
    code = shutil.which("code")
    if not code or not file:
        return False
    try:
        subprocess.Popen([code, "-g", f"{file}:{max(line, 1)}"], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603
    except OSError:
        return False
    return True


class _Handler(BaseHTTPRequestHandler):
    panel: Panel

    def log_message(self, *_args) -> None:  # noqa: ANN002 - keep the student's terminal clean
        return

    def _allowed(self) -> bool:
        host = (self.headers.get("Host") or "").lower()
        ok_host = host in (f"127.0.0.1:{self.panel.port}", f"localhost:{self.panel.port}")
        key = parse_qs(urlparse(self.path).query).get("k", [""])[0]
        return ok_host and secrets.compare_digest(key, self.panel.key)

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data: dict, code: int = 200) -> None:
        self._send(code, json.dumps(data).encode(), "application/json")

    def do_GET(self) -> None:  # noqa: N802
        if not self._allowed():
            self._send(403, b"Forbidden", "text/plain")
            return
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, _PAGE.read_bytes(), "text/html; charset=utf-8")
        elif path == "/bee.jpg" and _BEE.is_file():
            self._send(200, _BEE.read_bytes(), "image/jpeg")
        elif path == "/state":
            with self.panel.lock:
                self._json({**self.panel.engine.view(), "portal": self.panel.portal_url})
        else:
            self._send(404, b"Not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        size = min(int(self.headers.get("Content-Length") or 0), 8192)
        if not self._allowed() or self.headers.get(HEADER) != "1":
            # Read the body we are refusing before answering: closing with unread data makes the client see a
            # connection reset (WinError 10054) instead of the 403.
            self.rfile.read(size)
            self._send(403, b"Forbidden", "text/plain")
            return
        try:
            data = json.loads(self.rfile.read(size) or b"{}")
        except ValueError:
            self._send(400, b"Bad request", "text/plain")
            return
        action = urlparse(self.path).path.strip("/")
        with self.panel.lock:
            self._json(self._act(action, data))

    def _act(self, action: str, data: dict) -> dict:
        e = self.panel.engine
        if action == "continue":
            e.on_continue()
        elif action == "answer":
            e.on_answer(str(data.get("value", ""))[:200])
        elif action == "hint":
            e.on_hint()
        elif action == "restore":
            e.restore()
        elif action == "show":
            e.on_show()
        elif action == "there":
            s = e.step or {}
            opened = open_in_editor(e.root, data.get("file") or s.get("file", ""), int(data.get("line") or s.get("at", 1)))
            return {**e.view(), "opened": opened}
        elif action == "ask":
            q = str(data.get("question", ""))[:600]
            reply = self.panel.ask(q, e.view()) if self.panel.ask else "Madhu needs your portal connection. Run: python madhu.py connect"
            return {**e.view(), "reply": reply}
        return e.view()
