"""Step packs: a mission's steps as data. Adding a mission means adding a pack, not writing code.

Step kinds:
  say       read one short thing, press Continue
  predict   choose an answer first, then see the real result of `run`
  hunt      find something in the code and name it
  talk      open the Customer Line
  write     change code until `goal` customers are happy, or with "pass": "examples", until its Try it table is all right.
            Three hints climb from a nudge to nearly the answer; after them, `answer` (code and why) can be shown.
  break     remove something on purpose, watch customers leave, put it back
  git       do a real Git action; Madhu sees the result
  setup     install something; passes when Python can really import it
  friend    a real person asks the real bot a few questions
  connect   link Madhu to the portal; passes when Madhu really holds a sign-in
  deploy    put the app online; passes when the address the student pastes really answers as an AskMate
  key       keep an AI key safe; passes when a real key is in .env and Git ignores .env (`vars`: the key names)

Missions are Launchpad (m1-workshop ... m6-ship) and Project tickets (s1-1-hello ... s6-4-...). Both sort by `order_key`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

KINDS = {"say", "predict", "hunt", "talk", "write", "break", "git", "setup", "friend", "connect", "deploy", "key"}
GIT_GOALS = {"committed", "pushed", "merged"}
BRIEF = ("ask", "gets", "gives", "approach", "where", "done")   # a code step's ask, in one fixed shape (owner, 20 Nov)
PACK_DIR = ".madhu/packs"


class PackError(ValueError):
    pass


def _check_step(i: int, s: dict, has_line: bool) -> None:
    where = f"step {i + 1}"
    kind = s.get("kind")
    if kind not in KINDS:
        raise PackError(f"{where}: unknown kind {kind!r}")
    if not s.get("title"):
        raise PackError(f"{where}: needs a title")
    if kind == "predict" and (s.get("answer") not in s.get("options", []) or not s.get("run")):
        raise PackError(f"{where}: predict needs options, an answer among them, and code to run")
    t = s.get("timeout")
    if t is not None and (isinstance(t, bool) or not isinstance(t, int) or not 1 <= t <= 60):
        raise PackError(f"{where}: timeout must be whole seconds from 1 to 60")
    if kind == "hunt" and not s.get("accept"):
        raise PackError(f"{where}: hunt needs accept")
    if kind == "setup" and not s.get("needs"):
        raise PackError(f"{where}: setup needs the modules to check")
    if kind == "key" and not s.get("vars"):
        raise PackError(f"{where}: key needs vars, the names a key may have in .env")
    if kind in ("write", "break", "talk", "friend") and not has_line:
        raise PackError(f"{where}: {kind} needs a customer line")
    by_table = s.get("pass") == "examples"
    if by_table and not s.get("examples"):
        raise PackError(f"{where}: a step that passes by its Try it table needs examples")
    if kind in ("write", "break") and not by_table and not isinstance(s.get("goal"), int):
        raise PackError(f"{where}: {kind} needs a goal")
    if kind == "write" and s.get("ask") is not None and not all(s.get(k) for k in BRIEF):
        raise PackError(f"{where}: a code step with an ask needs all of {BRIEF}: the student must know the ask and how to approach it")
    if kind == "write" and len(s.get("hints", [])) != 3:
        raise PackError(f"{where}: write needs exactly 3 hints: Nudge, Point, Nearly there")
    if kind == "write" and not (isinstance(s.get("answer"), dict) and s["answer"].get("code") and s["answer"].get("why")):
        raise PackError(f"{where}: write needs an answer with code and why, for a student still stuck after every hint")
    if kind == "git" and s.get("git") not in GIT_GOALS:
        raise PackError(f"{where}: git needs one of {sorted(GIT_GOALS)}")
    ex = s.get("examples")
    if ex is not None and not (":" in str(ex.get("call", "")) and ex.get("cases")
                               and all(isinstance(c.get("args"), list) and "want" in c for c in ex["cases"])):
        raise PackError(f"{where}: examples need a call like module:function, and cases with args and want")


def validate(pack: dict) -> dict:
    for key in ("code", "title", "steps"):
        if not pack.get(key):
            raise PackError(f"pack needs {key}")
    line = pack.get("line")
    if line and not (line.get("call") and line.get("customers")):
        raise PackError("line needs call and customers")
    for i, s in enumerate(pack["steps"]):
        _check_step(i, s, bool(line))
    return pack


def load(root: Path, code: str) -> dict | None:
    """The pack for a mission code, or None if this branch has none. A broken pack is a bug in our content, so it raises."""
    path = root / PACK_DIR / f"{code}.json"
    if not path.is_file():
        return None
    pack = json.loads(path.read_text(encoding="utf-8"))
    custom = root / PACK_DIR / f"{code}.customers.json"
    if pack.get("line") and custom.is_file():
        pack["line"]["customers"] = json.loads(custom.read_text(encoding="utf-8"))
    return validate(pack)


def mission_no(code: str) -> int:
    """m3-data is Mission 3. Missions are numbered, so Madhu can tell what comes next."""
    found = re.match(r"m(\d+)", code or "")
    return int(found.group(1)) if found else 0


def order_key(code: str) -> tuple[int, int, int]:
    """Where a mission sits in the programme: (section, sprint or mission, ticket). Launchpad's m3-data is (0, 3, 0);
    the Project's s1-2-clean is (1, 1, 2), so every Project ticket comes after Launchpad and in order inside a sprint.
    Anything else is (0, 0, 0), never a mission to suggest."""
    found = re.match(r"([ms])(\d+)(?:-(\d+)(?=-|$))?", code or "")
    if not found:
        return (0, 0, 0)
    section = 0 if found.group(1) == "m" else 1
    return (section, int(found.group(2)), int(found.group(3) or 0) if section else 0)


def pick_next(branches: list[str], current: str, finished) -> str:  # noqa: ANN001
    """The branch to suggest. After a mission: the next one in order. On no mission: the newest. Never a finished one.
    (Found in testing: Mission 3 suggested Mission 1, because GitHub's merge leaves a branch looking unmerged.)"""
    found = [(order_key(code_for_branch(b)), b) for b in branches
             if code_for_branch(b) and order_key(code_for_branch(b)) > (0, 0, 0) and not finished(code_for_branch(b))]
    if current:
        found = [f for f in found if f[0] > order_key(current)]
        return min(found)[1] if found else ""
    return max(found)[1] if found else ""


BRANCH_PREFIXES = ("feature/", "ticket/")   # feature/ is the industry name; ticket/ is what repos made before 4 Nov use


def code_for_branch(branch: str) -> str:
    """feature/m3-data gives m3-data. Any other branch is not a mission."""
    return next((branch.removeprefix(p) for p in BRANCH_PREFIXES if branch.startswith(p)), "")
