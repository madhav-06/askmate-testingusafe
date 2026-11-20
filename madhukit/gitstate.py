"""Read the repo's Git state. Madhu only looks: the student types every Git command themselves."""

from __future__ import annotations

import subprocess
from pathlib import Path

_GIT_TIMEOUT = 8


def _git(root: Path, *args: str, timeout: int = _GIT_TIMEOUT) -> str | None:
    """The command's output, or None if it failed. A broken or missing Git must never crash Madhu."""
    try:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.rstrip() if r.returncode == 0 else None   # keep leading spaces: `git status` uses them as columns


def branch(root: Path) -> str:
    return _git(root, "rev-parse", "--abbrev-ref", "HEAD") or ""


def changed_files(root: Path) -> list[str]:
    """Files with work not yet committed. Madhu's own folder never counts."""
    out = _git(root, "status", "--porcelain")
    files = [line[3:].strip().strip('"') for line in (out or "").splitlines() if len(line) > 3]
    return [f for f in files if not f.startswith(".madhu/")]


def commits_ahead(root: Path, base: str = "main") -> int:
    """Commits on this branch that the base does not have. Works if only origin/<base> exists locally."""
    for ref in (f"origin/{base}", base):
        out = _git(root, "rev-list", "--count", f"{ref}..HEAD")
        if out is not None:
            return int(out.strip() or 0)
    return 0


def is_pushed(root: Path) -> bool:
    """True if GitHub already has this exact commit. Needs an upstream, which `git push -u` or a fetched branch gives."""
    head = _git(root, "rev-parse", "HEAD")
    upstream = _git(root, "rev-parse", "@{u}")
    return bool(head) and head == upstream


def has_identity(root: Path) -> bool:
    """A first commit fails with a confusing message if Git does not know who you are."""
    return bool(_git(root, "config", "--get", "user.name")) and bool(_git(root, "config", "--get", "user.email"))


def in_conflict(root: Path) -> list[str]:
    """Files still waiting for a merge conflict to be solved."""
    out = _git(root, "diff", "--name-only", "--diff-filter=U")
    return [f for f in (out or "").splitlines() if f]


def merged_main(root: Path) -> bool:
    """True once this branch contains everything on origin/main, so the pull request can merge cleanly."""
    _git(root, "fetch", "--quiet", timeout=15)
    if _git(root, "rev-parse", "--verify", "origin/main") is None:
        return False
    return _git(root, "merge-base", "--is-ancestor", "origin/main", "HEAD") is not None and not in_conflict(root)


def rescue(root: Path, wanted: str, changed: list[str]) -> str:
    """Name the Git problem in plain words, so confusion about Git never stops the real work. `wanted` is the step's goal."""
    if not has_identity(root):
        return 'Git does not know who you are yet. Type: git config --global user.name "Your Name", then the same with user.email.'
    conflicts = in_conflict(root)
    if conflicts:
        return "Git needs your decision in: " + ", ".join(conflicts) + ". Open it, choose, delete the marker lines, then git add and git commit."
    if wanted == "pushed" and changed:
        return "You still have changes that are not committed: " + ", ".join(changed[:3]) + "."
    if wanted == "committed" and not changed and commits_ahead(root) == 0:
        return "There is nothing to commit yet. Check that your file is saved."
    return ""


def ticket_branches(root: Path) -> list[str]:
    """Mission branches on GitHub this clone knows about that are not merged yet. Fetches quietly so a new one shows up.
    New branches are feature/<mission>; ticket/<mission> is the older name, still read so older repos keep working."""
    _git(root, "fetch", "--quiet", timeout=15)
    out = _git(root, "branch", "-r", "--list", "origin/feature/*", "origin/ticket/*", "--no-merged", "origin/main") or ""
    return [b.strip().removeprefix("origin/") for b in out.splitlines() if b.strip()]
