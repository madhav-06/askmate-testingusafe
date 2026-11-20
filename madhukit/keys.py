"""Is the student's AI key kept safely? It must be in .env, and .env must never reach GitHub.

A key on GitHub is copied by bots within minutes, so this step checks the real state of the repo, not what the student says.
"""

from __future__ import annotations

from pathlib import Path

from madhukit import gitstate

_PLACEHOLDERS = ("paste", "your", "xxx", "<", "here")


def read_env(path: Path) -> dict[str, str]:
    """KEY=value lines. Blank lines and # comments are skipped. A missing file is an empty dict."""
    out: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            name, value = line.split("=", 1)
            out[name.strip()] = value.strip().strip('"').strip("'")
    return out


def _real(value: str) -> bool:
    return len(value) >= 20 and not any(p in value.lower() for p in _PLACEHOLDERS)


def problem(root: Path, names: list[str]) -> str:
    """'' when a real key is in .env and Git ignores .env. Otherwise the one thing to fix, in plain words."""
    env = root / ".env"
    if not env.is_file():
        return "Make a file called .env next to main.py: copy .env.example, rename the copy to .env, and paste your key in it."
    values = read_env(env)
    if not any(_real(values.get(n, "")) for n in names):
        return f"Your .env has no key yet. Paste it right after {names[0]}= with no spaces, then save."
    if gitstate._git(root, "ls-files", "--error-unmatch", ".env") is not None:
        return "Your .env is in Git, so your key would reach GitHub. Type: git rm --cached .env  and then commit."
    if gitstate._git(root, "check-ignore", "-q", ".env") is None:
        return "Git is not told to ignore .env yet. Add a line with just .env to your .gitignore file, then save."
    return ""
