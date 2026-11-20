"""Ticket s1-1's official tests. They run on your pull request."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_the_greeting_says_homeshine():
    assert "homeshine" in client.post("/api/ask", json={"question": "hi"}).json()["answer"].lower()


def test_askmate_has_its_own_name():
    profile = json.loads(Path("askmate.json").read_text(encoding="utf-8"))
    assert "starter" not in profile["name"].lower() and "starter" not in profile["greeting"].lower()


def test_health_shows_the_new_name():
    assert "starter" not in client.get("/healthz").json()["name"].lower()
