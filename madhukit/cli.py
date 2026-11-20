"""`python madhu.py`: start the panel, watch files, keep the loop going.

The terminal always works, even if the panel cannot open, so everything important is printed here too.
"""

from __future__ import annotations

import sys
import textwrap
import threading
import time
from pathlib import Path

from madhukit import gitstate
from madhukit.engine import Engine
from madhukit.panel import Panel
from madhukit.portal import Portal

POLL_S = 0.5
GIT_EVERY = 4        # Git is checked less often than files: it starts a process
SYNC_EVERY = 40      # the portal is checked about every 20 seconds


def _mtimes(root: Path, names: list[str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for n in names:
        try:
            out[n] = (root / n).stat().st_mtime
        except OSError:
            out[n] = 0.0
    return out


WIDTH = 72          # a VS Code terminal beside the code is narrow: a longer line wraps in the middle of a word


def _say(text: str, indent: str = "  ") -> None:
    """Print in short lines. The full detail is in the panel; the terminal stays calm and readable."""
    print(textwrap.fill(" ".join(str(text).split()), width=WIDTH, initial_indent=indent, subsequent_indent=indent))


def _print_cmds(text: str) -> None:
    """One command per line, each indented the same, so two commands never look like one."""
    for c in (text or "").splitlines():
        if c.strip():
            print("      " + c)


def banner(url: str) -> list[str]:
    """What the student sees first: the link on its own line, and the one thing to do with it."""
    rule = "-" * 60
    return [rule, "  Madhu is ready.", "", "  Open this link to see Madhu beside your code", "  (hold Ctrl and click it):",
            "", f"  {url}", "", "  Keep this terminal open while you work. Type your own", "  commands in a second terminal: click + in this panel.", rule]


def _print_view(v: dict) -> None:
    print()
    if v.get("welcome"):
        _say(v["welcome"])
    if v.get("flash"):
        _say(f"Done: {v['flash']}.")
    if v["mode"] == "arrive":
        _say(v["title"])
        _say(v["body"])
        _print_cmds(v["cmd"])
    elif v["mode"] == "finished":
        _say(f"Every step is done. {v['next']}")
        if v.get("next_cmd"):
            _say("Your next mission is ready. Type:")
            _print_cmds(v["next_cmd"])
    else:
        s = v["step"]
        _say(f"Step {v['index']} of {v['total']}: {s['title']}", indent="> ")
        if s.get("cmd"):
            _print_cmds(s["cmd"])
    if v.get("msg"):
        _say(v["msg"])
    line = v.get("line")
    if line:
        _say(f"Happy customers: {line['happy']} of {line['total']}")
        if line.get("error"):
            e = line["error"]
            _say(f"{e['title']}: {e['plain']}" + (f" ({e['file']}, line {e['line']})" if e.get("file") else ""))
        if line["unhappy"]:
            c = line["unhappy"][0]
            _say(f"{c['name']} asked {c['ask']!r} and wanted: {c['wanted']}. Your bot said: {c['said']}")


def _sync(engine: Engine, portal: Portal, reported: dict) -> None:
    """Tell the portal when something changed, and pick up the mentor's comments. Runs in the background: never blocks."""
    v = engine.view()
    code = v.get("code", "")
    pushed = bool(code) and gitstate.is_pushed(engine.root) and gitstate.commits_ahead(engine.root) > 0
    line = v.get("line") or {}
    now = {"ticket": code, "step": v.get("index"), "total": v.get("total"), "title": (v.get("step") or {}).get("title", "Finished"),
           "happy": line.get("happy", 0), "of": line.get("total", 0), "hints": len((v.get("step") or {}).get("hints", [])),
           "shown": v.get("shown", 0), "pushed": pushed}
    if code and now != reported.get("last"):
        reported["last"] = now
        portal.report(now)
    engine.mentor = portal.todo(code)


def should_sync(n: int, step_now: tuple, step_was: tuple | None) -> bool:
    """Tell the portal now? Every 20 seconds, and at once when the step changes or Madhu gets connected, so the portal never
    shows step 1 while the student is on step 4 (found in the first student test)."""
    return n % SYNC_EVERY == 0 or step_now != step_was


def _loop(engine: Engine, root: Path, portal: Portal, lock: threading.Lock) -> None:
    seen = _mtimes(root, (engine.pack or {}).get("watch", []))
    shown, n, reported, step_was = "", 0, {}, None
    while True:
        time.sleep(POLL_S)
        n += 1
        with lock:        # the panel's clicks arrive on another thread
            if n % GIT_EVERY == 0:
                engine.poll_git()
            now = _mtimes(root, (engine.pack or {}).get("watch", []))
            if now != seen:
                seen = now
                engine.on_save()
            v = engine.view()
        step_now = (v.get("code"), v["mode"], v.get("index"), portal.token)
        if should_sync(n, step_now, step_was):
            step_was = step_now
            threading.Thread(target=_sync, args=(engine, portal, reported), daemon=True).start()
        key = f"{v['mode']}{v.get('index')}{v.get('msg')}{(v.get('line') or {}).get('happy')}"
        if key != shown:
            shown = key
            _print_view(v)


def _code_of(root: Path, files: list[str]) -> str:
    """The files this mission watches, as one text. Sent only when the student clicks Ask Madhu."""
    parts = [f"# {f}\n{(root / f).read_text(encoding='utf-8', errors='replace')}" for f in files if (root / f).is_file()]
    return "\n\n".join(parts)


def _asker(engine: Engine, portal: Portal):  # noqa: ANN202
    """Ask Madhu from the panel. The student's code leaves this machine only here, when they click."""
    def ask(question: str, view: dict) -> str:
        files = (engine.pack or {}).get("watch", [])
        code = _code_of(engine.root, files)
        return portal.ask(view.get("code", ""), question, view, code)
    return ask


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(errors="replace")   # a Windows terminal may not have every symbol: never crash over one
    root = Path.cwd()
    args = sys.argv[1:] if argv is None else argv
    portal = Portal(root)
    if args[:1] == ["connect"]:
        return 0 if portal.link() else 1
    engine = Engine(root)
    panel = Panel(engine, ask=_asker(engine, portal), portal_url=portal.url)
    panel.start()
    print("\n".join(banner(panel.url)))
    try:
        _loop(engine, root, portal, panel.lock)
    except KeyboardInterrupt:
        print()
        _say("Madhu stopped. Your work is saved. Press Ctrl+Shift+B to start again.")
    finally:
        panel.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
