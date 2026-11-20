"""The official check, run by GitHub Actions on the student's pull request.

The result reaches the portal as GitHub annotations, which the portal reads from the check run, so no secret lives in
the student's repo. GitHub keeps only about 10 of each kind per step, so this sends one summary and the first failures.
"""

from __future__ import annotations

import sys
from pathlib import Path

from madhukit import customers, gitstate, packs

MAX_FAILS = 9
_ESC = {"%": "%25", "\r": "%0D", "\n": "%0A"}


def _clean(text: str) -> str:
    return "".join(_ESC.get(c, c) for c in str(text))[:240]


def report(root: Path, code: str) -> int:
    """Prints annotations and returns the process exit code: 0 only when every customer is happy."""
    pack = packs.load(root, code) if code else None
    if not pack or not pack.get("line"):
        print(f"::notice title=MADHU_SCORE::none {code or 'no-ticket'}")
        return 0
    required = [c for c in pack["line"]["customers"] if not c.get("stretch")]
    stretch = [c for c in pack["line"]["customers"] if c.get("stretch")]
    res = customers.run_line(root, {**pack["line"], "customers": required})
    print(f"::notice title=MADHU_SCORE::{res['happy']} of {res['total']}")
    if stretch:
        extra = customers.run_line(root, {**pack["line"], "customers": stretch})
        print(f"::notice title=MADHU_STRETCH::{extra['happy']} of {extra['total']}")
    if res["error"]:
        print(f"::error title=MADHU_ERROR::{_clean(res['error']['title'] + ': ' + res['error']['plain'])}")
    for c in res["unhappy"][:MAX_FAILS]:
        print(f"::error title=MADHU_CUSTOMER::{_clean(c['name'] + ' asked: ' + c['ask'].replace(chr(183), ' ') + '. Wanted: ' + c['wanted'] + '. Your bot: ' + c['said'])}")
    return 0 if res["happy"] == res["total"] else 1


def main() -> int:
    import os

    root = Path.cwd()
    head = os.environ.get("GITHUB_HEAD_REF") or gitstate.branch(root)
    return report(root, packs.code_for_branch(head))


if __name__ == "__main__":
    sys.exit(main())
