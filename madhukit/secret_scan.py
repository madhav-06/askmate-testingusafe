"""The secret check, run by GitHub Actions on every pull request: no AI key or database password in the repo.

A key on GitHub is found and used by strangers within minutes, so a pull request with one in it never passes. The fix
is always the same: delete the key in its website, make a new one, and keep it only in .env (and on Render).

Usage: python -m madhukit.secret_scan        (exit 1 if a secret is found)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PATTERNS = {
    "a Groq key": re.compile(r"gsk_[A-Za-z0-9]{20,}"),
    "a Google (Gemini) key": re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    "an OpenRouter key": re.compile(r"sk-or-[A-Za-z0-9\-]{20,}"),
    "a database password": re.compile(r"postgres(?:ql)?://[^:\s/]+:[^@\s]{6,}@"),
}
_SKIP = (".madhu/", "madhukit/")      # Madhu's own files hold the patterns, not secrets


def tracked(root: Path) -> list[str]:
    """The files Git would send to GitHub. Outside a Git repo, every file under root."""
    try:
        out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, timeout=20, check=True).stdout
        return [f for f in out.splitlines() if f]
    except (OSError, subprocess.SubprocessError):
        return [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]


def scan(root: Path) -> list[str]:
    """Plain sentences, one per secret found: the file, the line and what it looks like. Never the secret itself."""
    found = []
    for name in tracked(root):
        if name.startswith(_SKIP):
            continue
        try:
            text = (root / name).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for n, line in enumerate(text.splitlines(), start=1):
            for what, pattern in PATTERNS.items():
                if pattern.search(line):
                    found.append(f"{name}, line {n}: this looks like {what}.")
    return found


def main() -> int:
    found = scan(Path.cwd())
    for f in found:
        print(f"::error title=MADHU_SECRET::{f} Delete it from the file, delete the key on its website and make a new one, "
              "and keep the new one only in .env and on Render.")
    print("No secrets found." if not found else f"{len(found)} secret(s) found.")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
