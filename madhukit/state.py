"""Madhu's memory and safety net, kept in .madhu/ and never committed.

Work happens in short sittings, and starting again is where students drift away. So Madhu remembers the step, and it
keeps the last version that worked so a student can try things without fear of losing it.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Progress:
    pack: str = ""
    step: int = 0
    attempts: int = 0            # real tries on this step: the first hint needs one
    hints: int = 0               # hints shown on this step
    phase: str = ""              # steps with two stages use this, such as break then repair
    answered: str = ""           # the student's guess on a predict step, kept so the reveal survives a restart
    best: int = 0                # highest number of happy customers so far
    chat: list = field(default_factory=list)   # the Friend Test's questions and the bot's replies
    last_seen: str = ""
    done: list = field(default_factory=list)
    finished: bool = False       # every step done: a finished mission stays finished when the student comes back to it
    shown: list = field(default_factory=list)  # steps whose answer Madhu showed after every hint: the mentor sees how many


def _dir(root: Path) -> Path:
    d = root / ".madhu"
    d.mkdir(exist_ok=True)
    return d


def _all(root: Path) -> dict[str, dict]:
    """Every mission's progress, by mission code. One file for all of them, so switching branches never wipes another
    mission's progress (found in testing: going back to Mission 3 restarted it at step 1). The old one-mission file is
    still read."""
    try:
        raw = json.loads((_dir(root) / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    if isinstance(raw.get("packs"), dict):
        return raw["packs"]
    return {raw["pack"]: raw} if raw.get("pack") else {}


def load(root: Path, pack: str) -> Progress:
    """A damaged or missing file means starting the pack again, never a crash. A new pack starts fresh."""
    raw = _all(root).get(pack)
    try:
        return Progress(**{k: v for k, v in raw.items() if k in Progress.__dataclass_fields__}) if isinstance(raw, dict) else Progress(pack=pack)
    except TypeError:
        return Progress(pack=pack)


def finished(root: Path, pack: str) -> bool:
    return bool(_all(root).get(pack, {}).get("finished"))


def save(root: Path, p: Progress) -> None:
    p.last_seen = datetime.now(timezone.utc).isoformat()
    packs = _all(root)
    packs[p.pack] = asdict(p)
    tmp = _dir(root) / "state.json.tmp"
    tmp.write_text(json.dumps({"packs": packs}), encoding="utf-8")
    tmp.replace(_dir(root) / "state.json")


def snapshot(root: Path, files: list[str]) -> None:
    """Keep these files as the last version that worked."""
    snap = _dir(root) / "snap"
    snap.mkdir(exist_ok=True)
    for name in files:
        src = root / name
        if src.is_file():
            target = snap / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)


def restore(root: Path, files: list[str]) -> list[str]:
    """Put the last working version back. Returns the files restored."""
    snap = _dir(root) / "snap"
    done = []
    for name in files:
        if (snap / name).is_file():
            shutil.copy2(snap / name, root / name)
            done.append(name)
    return done
