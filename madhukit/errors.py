"""Turn a Python traceback into one plain sentence, plus the line to look at.

A first traceback reads like a wall of noise. This removes the noise and keeps the thinking: it says what kind of
problem it is and where, and never says how to fix it.
"""

from __future__ import annotations

import re

_PLAIN = (
    ("IndentationError", "The spaces at the start of a line are not right. Python uses them to know what belongs together."),
    ("TabError", "This file mixes tabs and spaces at the start of a line."),
    ("SyntaxError", "Python could not read this line. Look for a missing colon, bracket or quote."),
    ("ModuleNotFoundError", "Python could not find a module you tried to import. Check the spelling."),
    ("ImportError", "Python found the file, but not the name you tried to import from it."),
    ("NameError", "You used a name Python does not know yet. Look for a spelling mistake, or a variable that was never set."),
    ("AttributeError", "You asked a value for something it does not have. Check what type that value really is."),
    ("KeyError", "You looked up a key that is not in the dictionary."),
    ("IndexError", "You asked for a position that is past the end of the list."),
    ("TypeError", "A value of the wrong type was used here, or a function got the wrong number of inputs."),
    ("ValueError", "The type is right, but this value cannot be used here."),
    ("FileNotFoundError", "Python could not find that file. Check the name and the folder."),
    ("JSONDecodeError", "A JSON file has a mistake in it, such as a missing comma or quote."),
    ("RecursionError", "A function keeps calling itself and never stops."),
    ("ZeroDivisionError", "Something was divided by zero."),
    ("UnboundLocalError", "A variable was used before it got a value."),
)
_FRAME = re.compile(r'File "(?P<path>[^"]+)", line (?P<line>\d+)')
_INTERNAL = ("madhukit", "site-packages", "<frozen", "lib/python", "lib\\python", "Lib\\")


def _student_frame(text: str) -> tuple[str, int]:
    """The deepest frame in the student's own code: that is the line worth looking at."""
    found = ("", 0)
    for m in _FRAME.finditer(text):
        if not any(mark in m["path"] for mark in _INTERNAL):
            found = (m["path"].replace("\\", "/").rsplit("/", 1)[-1], int(m["line"]))
    return found


def translate(traceback_text: str) -> dict:
    """{title, plain, file, line, detail} for the LAST exception in the text. An unknown error keeps its own message."""
    text = (traceback_text or "").strip()
    last = text.splitlines()[-1].strip() if text else ""
    name = last.split(":", 1)[0].rsplit(".", 1)[-1].strip()
    detail = last.split(":", 1)[1].strip() if ":" in last else ""
    plain = next((p for n, p in _PLAIN if n == name), "Your code stopped with an error.")
    file, line = _student_frame(text)
    return {"title": name or "Error", "plain": plain, "file": file, "line": line, "detail": detail[:200]}


def show_spaces(text: str) -> str:
    """Make invisible differences visible. The bug in a mission is often a space nobody can see."""
    return str(text).replace(" ", "·").replace("\t", "→")
