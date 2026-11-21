"""Ticket s1-4's official tests. They run on your pull request, with no key: AskMate must work without one."""

import ai


def test_the_request_goes_to_the_chat_address_with_the_key():
    req = ai.build_request([{"role": "user", "content": "hi"}], "m", "k", "https://example.org/v1")
    assert req["url"] == "https://example.org/v1/chat/completions"
    assert req["headers"]["Authorization"] == "Bearer k"
    assert req["json"]["model"] == "m" and req["json"]["messages"][0]["content"] == "hi"


def test_the_reply_is_read_and_trimmed():
    assert ai.read_reply({"choices": [{"message": {"content": "  Yes.  "}}]}) == "Yes."


def test_an_empty_reply_is_an_empty_string():
    assert ai.read_reply({"choices": [{"message": {"content": None}}]}) == ""


def test_with_no_key_askmate_still_answers(monkeypatch):
    monkeypatch.setattr(ai, "providers", lambda: [])
    text, model, resting = ai.write("hi", "refuse", [])
    assert text and model == "fake" and not resting
