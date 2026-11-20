"""Find the products a customer means. Code decides this, never the AI, so an answer can always be checked.

Right now AskMate only understands exact product codes, like OPC 109. Real customers say "rimless toilet" or "18 by 14
basin", so in Sprint 1 you teach it to understand words.
"""

import re

from catalogue import clean_code

STOPWORDS = {"a", "an", "the", "do", "does", "you", "have", "has", "is", "are", "there", "any", "for", "with", "i", "me",
             "my", "want", "need", "please", "show", "what", "which", "of", "in", "to", "and", "or", "sell", "price",
             "cost", "how", "much", "it", "your", "get", "can", "available"}
SYNONYMS = {"commode": "toilet", "wc": "toilet", "toilets": "toilet", "faucet": "tap", "taps": "tap", "basins": "basin", "sinks": "basin", "lavatory": "basin", "lavatories": "basin", "bidets": "bidet", "showers": "shower", "bathtubs": "bathtub",}
CODE = re.compile(r"\b([A-Za-z]{2,5})\s*-?\s*(\d{3})\b")


def words(text):
    """The words in a question or a product, ready to compare."""
    text = text.lower().replace(" by ", "x").replace(" x ", "x")
    for mark in "?!.,()":
        text = text.replace(mark, " ")
    return [w for w in text.split() if w not in STOPWORDS]


def meaning(word):
    """The word the product list uses for what the customer said."""
    return SYNONYMS.get(word, word)


def product_words(product):
    """Every word that describes a product: its name, type, features, size and colour."""
    text = " ".join(product[k] for k in ("name", "category", "features", "size", "colour"))
    found = set(words(text))
    for w in list(found):
        parts = w.split("x")
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            found.add(parts[0] + "x" + parts[1])        # 18x14x7 also matches a customer who says 18x14
    return found


def score(asked, product):
    """How many of the customer's words describe this product."""
    return len(set(asked) & product_words(product))


def codes_in(question):
    """Product codes typed in a question, cleaned the same way as the list: 'opc-180' gives ['OPC 180']."""
    return [clean_code(letters + " " + digits) for letters, digits in CODE.findall(question)]


def find(question, products):
    """The codes of the products the customer means, cheapest first."""
    wanted = codes_in(question)
    if wanted:
        return [p["code"] for p in products if p["code"] in wanted]
    asked = [meaning(w) for w in words(question)]
    scores = {p["code"]: score(asked, p) for p in products}
    best = max(scores.values(), default=0)
    if best == 0:
        return []
    found = sorted((p for p in products if scores[p["code"]] == best), key=lambda p: p["price"])
    if "cheapest" in asked:
        found = found[:1]
    return [p["code"] for p in found]


def decide(found):
    """What to do. Nothing found: say no. One product: answer. More than one: ask which one."""
    if not found:
        return "refuse"
    if len(found) == 1:
        return "answer"
    return "ask"
