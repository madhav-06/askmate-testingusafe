"""How good is AskMate? Ask it every test question in data/gold.json, and count how many it gets right.

Run it:  python eval.py
It always uses AskMate's own sentences (never a real AI), so the same code gives the same numbers every time.
"""

import json
import os
from pathlib import Path

os.environ["ASKMATE_LLM"] = "fake"          # before AskMate's settings are read: a measurement must not change by chance
GOLD = Path(__file__).parent / "data" / "gold.json"


def is_right(reply, want):
    """True when AskMate decided what the test question wants: the same action, and every product it should name."""
    return reply["action"] == want["action"] and set(want["products"]) <= set(reply["products"])


def scorecard(results):
    """Three numbers from a list of results. Each result is {"want": ..., "reply": ..., "right": True or False}."""
    right = sum(1 for r in results if r["right"])
    noes = [r for r in results if r["want"]["action"] == "refuse"]
    honest = sum(1 for r in noes if r["reply"]["action"] == "refuse")
    mistakes = sum(1 for r in results if r["reply"]["action"] == "answer" and not r["right"])
    return {"right_percent": round(100 * right / len(results)) if results else 0,
    "honest_no_percent": round(100 * honest / len(noes)) if noes else 100,
    "confident_mistakes": mistakes}


def run(gold=None, products=None):
    """Ask AskMate every test question. Each result keeps what was wanted, what AskMate said, and if it was right.
    With no products given, it uses every product AskMate knows."""
    from answer import load_products, reply

    products = products if products is not None else load_products()
    gold = gold if gold is not None else json.loads(GOLD.read_text(encoding="utf-8"))
    results = []
    for n, want in enumerate(gold):
        got = reply(want["q"], products, f"eval-{n}")
        results.append({"want": want, "reply": got, "right": is_right(got, want)})
    return results


def main():
    results = run()
    card = scorecard(results)
    print(f"Right answers:      {card['right_percent']}%   (of {len(results)} test questions)")
    print(f"Honest no:          {card['honest_no_percent']}%   (of the questions about things HomeShine does not sell)")
    print(f"Confident mistakes: {card['confident_mistakes']}   (AskMate answered, and was wrong: this must be 0)")
    for r in results:
        if not r["right"]:
            print(f"  missed: {r['want']['q']!r} wanted {r['want']['action']} {r['want']['products']}, "
                  f"AskMate did {r['reply']['action']} {r['reply']['products'][:3]}")


if __name__ == "__main__":
    main()
