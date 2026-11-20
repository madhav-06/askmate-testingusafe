"""The app starts, and every page answers. These pass from day one: each ticket brings its own official tests."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_the_chat_page_opens():
    assert client.get("/").status_code == 200


def test_health_says_this_is_askmate():
    assert client.get("/healthz").json()["app"] == "askmate"


def test_every_reply_says_what_it_decided():
    data = client.post("/api/ask", json={"question": "Do you sell tiles?"}).json()
    assert {"answer", "action", "products"} <= set(data)
