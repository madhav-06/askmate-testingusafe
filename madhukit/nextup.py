"""Where to go next: the one Git command that takes the student to their next mission or task branch.

It looks for new branches on GitHub at most every REFETCH_S seconds, because that is a network call.
"""

from __future__ import annotations

import time

from madhukit import gitstate, packs, state

REFETCH_S = 20


def others(engine) -> list[str]:  # noqa: ANN001
    """Open mission branches other than the one the student is on."""
    if time.monotonic() - engine.others_at > REFETCH_S or not engine.others_at:
        engine.others_at = time.monotonic()
        engine.others = gitstate.ticket_branches(engine.root)
    return [b for b in engine.others if b != engine.branch]


def arrive(engine) -> dict:  # noqa: ANN001
    """Not on a mission branch yet: tell them the one command that gets them there."""
    newest = packs.pick_next(others(engine), "", lambda c: state.finished(engine.root, c))
    if newest:
        return {"mode": "arrive", "title": "Move to your mission's branch", "body": "A branch keeps your work safe until it is ready. Type this in your terminal:",
                "cmd": f"git switch {newest}"}
    return {"mode": "arrive", "title": "No mission started yet", "body": "Go to the portal, open your mission, and click Start. Then come back here.", "cmd": ""}


def after(engine) -> str:  # noqa: ANN001
    """A finished mission is never a dead end: once the next one exists, the command to reach it."""
    nxt = packs.pick_next(others(engine), engine.pack["code"], lambda c: state.finished(engine.root, c))
    return f"git switch {nxt}" if nxt else ""
