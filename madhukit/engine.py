"""The step machine. One rule above all: only what the student's real code does can move a step forward.

The panel and the terminal are two faces on this one engine. `view()` is everything either of them needs to show.
"""

from __future__ import annotations

from pathlib import Path

from madhukit import customers, examples, gitstate, keys, nextup, packs, probe, state


def _norm(text: str) -> str:
    return " ".join((text or "").strip().casefold().replace("()", "").split())


class Engine:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.pack: dict | None = None
        self.p = state.Progress()
        self.msg = ""            # one line of feedback for the student
        self.tone = ""           # good | bad | ""
        self.flash = ""          # the title of the step just finished, so its "well done" is never read as this step's
        self.line: dict | None = None   # the latest Customer Line result
        self.reveal = ""         # the real output shown after a prediction
        self.branch = ""
        self.others: list[str] = []
        self.others_at = 0.0     # Madhu looks for new mission branches at most this often: it means a network call
        self.rescue_msg = ""
        self.welcome = ""
        self.mentor: list[dict] = []   # review comments from the portal: each one is a step to do
        self.examples: list[dict] = []      # the Try it table for the current step
        self._ex_key: tuple | None = None   # what the table was computed for: (mission, step, saves)
        self._saves = 0
        self.refresh()

    # ---- where am I? ----
    def refresh(self) -> None:
        """Read the branch and load its pack. Called at start and after any Git change."""
        self.branch = gitstate.branch(self.root)
        code = packs.code_for_branch(self.branch)
        pack = packs.load(self.root, code) if code else None
        if pack and (not self.pack or self.pack["code"] != pack["code"]):
            self.pack = pack
            self.p = state.load(self.root, pack["code"])
            self.line = None
            self.welcome = ""
            self._say("")        # the last mission's words do not belong on this one
            if self.p.step or self.p.done:
                self.welcome = f"Welcome back. You were on step {min(self.p.step + 1, self.total)}."
        elif not pack:
            self.pack = None

    @property
    def total(self) -> int:
        return len(self.pack["steps"]) if self.pack else 0

    @property
    def finished(self) -> bool:
        return bool(self.pack) and self.p.step >= self.total

    @property
    def step(self) -> dict | None:
        return None if not self.pack or self.finished else self.pack["steps"][self.p.step]

    def _say(self, msg: str, tone: str = "") -> None:
        self.msg, self.tone, self.flash = msg, tone, ""

    # ---- moving on ----
    def _advance(self, msg: str = "") -> None:
        s = self.step or {}
        self.p.done.append(s.get("id", self.p.step))
        self.p.step += 1
        self.p.finished = self.p.step >= self.total
        self.p.attempts = self.p.hints = 0
        self.p.phase = self.p.answered = ""
        self.p.chat = []
        self.reveal = ""
        if s.get("kind") in ("write", "break") and self.pack.get("watch"):
            state.snapshot(self.root, self.pack["watch"])
        state.save(self.root, self.p)
        self._say(msg or s.get("well_done", "Well done."), "good")
        self.flash = s.get("title", "")

    def _line_for_now(self) -> dict:
        """A Boss Customer stays hidden until their step, and Stretch customers until every step is done."""
        steps = self.pack["steps"][: self.p.step + 1]
        boss_here = any(s.get("boss") for s in steps)
        line = dict(self.pack["line"])
        line["customers"] = [c for c in line["customers"] if (boss_here or not c.get("boss")) and (self.finished or not c.get("stretch"))]
        return line

    def run_customers(self) -> dict:
        self.line = customers.run_line(self.root, self._line_for_now())
        self.p.best = max(self.p.best, self.line["happy"])
        return self.line

    # ---- events ----
    def on_continue(self) -> None:
        s = self.step
        if not s:
            return
        if s["kind"] == "say":
            self._advance()
        elif s["kind"] == "predict" and self.p.answered:
            self._advance()
        elif s["kind"] == "talk":
            self.run_customers()
            self._advance(f"{self.line['happy']} of {self.line['total']} customers are happy. Look at who is not.")

    def on_answer(self, value: str) -> None:
        s = self.step
        if not s:
            return
        if s["kind"] == "predict" and not self.p.answered:
            self.p.answered = value
            state.save(self.root, self.p)
            self.reveal = probe.run_snippet(self.root, s["run"], s.get("timeout", probe.SNIPPET_TIMEOUT))
            right = value == s["answer"]
            self._say(s.get("explain", "") if right else f"You guessed {value}. {s.get('explain', '')}".strip(), "good" if right else "")
        elif s["kind"] == "friend":
            self._friend_asks(s, value)
        elif s["kind"] == "deploy":
            ok, msg = probe.check_live(value)
            if ok:
                self._advance(msg)
            else:
                self._say(msg, "bad")
        elif s["kind"] == "hunt":
            self.p.attempts += 1
            if _norm(value) in {_norm(x) for x in s["accept"]}:
                self._advance()
            else:
                self._say(s.get("retry", "Not that one. Look again."), "bad")
            state.save(self.root, self.p)

    def _friend_asks(self, s: dict, question: str) -> None:
        """A real person talks to the real bot. Real people ask what nobody planned for."""
        one = {**self.pack["line"], "customers": [{"name": "Friend", "ask": question, "wanted": "", "want": {"must": ["\0"]}}]}
        res = customers.run_line(self.root, one)
        said = res["unhappy"][0]["said"] if res["unhappy"] else "(the bot crashed)"
        self.p.chat.append({"q": question, "a": said})
        if len(self.p.chat) >= s.get("count", 3):
            self._advance(s.get("well_done", "Real people ask things you never thought of."))
        state.save(self.root, self.p)

    def on_save(self) -> None:
        """A watched file changed. This is the heart of the loop."""
        self._saves += 1
        s = self.step
        if self.finished and any(c.get("stretch") for c in self.pack["line"]["customers"]):
            self.run_customers()
            return
        if not s or s["kind"] not in ("write", "break"):
            return
        before = self.line["happy"] if self.line else None
        line = self.run_customers()
        if s["kind"] == "write":
            self._after_write(s, line, before)
        else:
            self._after_break(s, line)
        state.save(self.root, self.p)

    def _after_write(self, s: dict, line: dict, before: int | None) -> None:
        self.p.attempts += 1
        if s.get("pass") == "examples":
            self._after_examples(s)
        elif line["error"]:
            self._say("Your code has an error. See below.", "bad")
        elif line["happy"] >= s["goal"]:
            self._advance(s.get("well_done") or f"{line['happy']} of {line['total']}. Nice work.")
        elif before is not None and line["happy"] > before:
            self._say(f"Up from {before} to {line['happy']}. Keep going. Look at who is still unhappy.", "good")
        elif before is not None and line["happy"] < before:
            self._say(f"Down from {before} to {line['happy']}. Something that worked has stopped working.", "bad")
        else:
            self._say("Nothing changed for customers yet. Look at what they wanted and what your bot said.", "")

    def _after_examples(self, s: dict) -> None:
        """A step about one function passes when its Try it table is all right: the customers come once the bot uses it."""
        rows = self._try_table(s)
        right = sum(r["ok"] for r in rows)
        if rows and right == len(rows):
            self._advance()
        else:
            self._say(f"{right} of {len(rows)} rows in the table are right. Look at the rows with a cross.", "good" if right else "")

    def _after_break(self, s: dict, line: dict) -> None:
        happy, goal = line["happy"], s["goal"]
        if self.p.phase == "" and happy < goal and not line["error"]:
            self.p.phase = "broken"
            self._say(s.get("broken", f"Customers just left: {happy} of {goal}. Now put it back and save."), "bad")
        elif self.p.phase == "broken" and happy >= goal:
            self._advance(s.get("well_done", "All back. Now you know why that line matters."))
        elif self.p.phase == "":
            self._say("Nothing broke yet. Make the change, then save.")

    def on_hint(self) -> str:
        """Try first: the first hint opens after one real attempt. Hints climb from a nudge to nearly the answer."""
        s = self.step
        hints = (s or {}).get("hints", [])
        if s and s.get("no_hint_until", 0) > self.p.attempts:
            self._say("Have a go first. Save one attempt, even a wrong one. Then I can help.")
        elif s and s["kind"] == "write" and self.p.attempts < 1:
            self._say("Have a go first. Save one attempt, even a wrong one. Then I can help.")
        elif self.p.hints < len(hints):
            self.p.hints += 1
            state.save(self.root, self.p)
            self._say("")
        return self.msg

    def on_show(self) -> None:
        """Still stuck after every hint: show the answer and why. The student still types it in and saves, and the mentor
        sees how many answers were shown (team lead, 8 Nov: "what if they cannot clear the step even with three hints?")."""
        s = self.step
        if s and s.get("answer") and self.view()["step"]["stuck"] and s["id"] not in self.p.shown:
            self.p.shown.append(s["id"])
            state.save(self.root, self.p)
            self._say("Here is the answer, and why it works. Type it in yourself, then save.")

    def poll_git(self) -> None:
        """Git steps finish when the repo really is in that state, however the student got there."""
        s = self.step
        was = self.branch
        self.branch = gitstate.branch(self.root)
        if self.branch != was or (not self.pack and packs.code_for_branch(self.branch)):
            self.refresh()
            return
        if s and s["kind"] == "setup" and probe.can_import(s["needs"]):
            self._advance("Installed. Python can use these now.")
        if s and s["kind"] == "connect" and (self.root / ".madhu" / "token").is_file():
            self._advance("Connected. Madhu knows who you are now.")
        if s and s["kind"] == "key":
            self.rescue_msg = keys.problem(self.root, s["vars"])
            if not self.rescue_msg:
                self._advance("Your key is in .env, and Git will never send .env to GitHub.")
            return
        if not s or s["kind"] != "git":
            self.rescue_msg = ""
            return
        changed = gitstate.changed_files(self.root)
        self.rescue_msg = gitstate.rescue(self.root, s["git"], changed)
        if s["git"] == "merged" and gitstate.merged_main(self.root) and not changed:
            self._advance("Merged. You solved a real conflict.")
        elif s["git"] == "committed" and not changed and gitstate.commits_ahead(self.root) > 0:
            self._advance("Committed. Your work is saved in Git.")
        elif s["git"] == "pushed" and not changed and gitstate.is_pushed(self.root):
            self._advance("Pushed. GitHub has your work.")

    def restore(self) -> str:
        """Safety net: go back to the last version that worked. Trying things must feel cheap."""
        files = state.restore(self.root, (self.pack or {}).get("watch", []))
        self._say("Back to your last working version: " + ", ".join(files) + "." if files else "No working version is saved yet.")
        return self.msg

    # ---- what to show ----
    def view(self) -> dict:
        base = {"branch": self.branch, "msg": self.msg, "tone": self.tone, "flash": self.flash, "welcome": self.welcome, "mentor": self.mentor}
        if not self.pack:
            return {**base, **nextup.arrive(self)}
        out = {**base, "mode": "pack", "code": self.pack["code"], "title": self.pack["title"], "total": self.total,
               "index": min(self.p.step + 1, self.total), "line": self.line, "best": self.p.best, "rescue": self.rescue_msg,
               "where": self.pack.get("where", ""), "mission": self.pack["title"], "shown": len(self.p.shown),
               "outline": [{"t": s.get("title", ""), "k": s["kind"]} for s in self.pack["steps"]]}
        s = self.step
        if s is None:
            # A finished mission must never be a dead end: once the next mission exists, say how to get to it.
            return {**out, "mode": "finished", "next": self.pack.get("next", "Go back to the portal."), "next_cmd": nextup.after(self)}
        fields = ("id", "kind", "title", "body", "cmd", "file", "at", "options", "goal", "prompt", "count", "ask", "gets", "gives", "approach", "where", "done")
        step = {k: s[k] for k in fields if k in s}
        step["hints"] = s.get("hints", [])[: self.p.hints]
        step["hints_left"] = max(0, len(s.get("hints", [])) - self.p.hints)
        step["answered"] = self.p.answered
        step["reveal"] = self.reveal
        step["phase"] = self.p.phase
        step["chat"] = self.p.chat
        step["examples"] = self._try_table(s)
        step["stuck"] = s["kind"] in ("write", "break") and step["hints_left"] == 0 and self.p.attempts >= len(s.get("hints", [])) + 2
        step["can_show"] = bool(s.get("answer"))
        step["answer"] = s["answer"] if s.get("id") in self.p.shown else None
        return {**out, "step": step}

    def _try_table(self, s: dict) -> list[dict]:
        """The Try it table, worked out again only when the step changes or the student saves: it runs their code."""
        if not s.get("examples"):
            return []
        key = (self.pack["code"], self.p.step, self._saves)
        if key != self._ex_key:
            self._ex_key, self.examples = key, examples.run(self.root, s["examples"])
        return self.examples
