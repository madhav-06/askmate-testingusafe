"""Find the products a customer means. Code decides this, never the AI, so an answer can always be checked.

Right now AskMate only understands exact product codes, like OPC 109. Real customers say "rimless toilet" or "18 by 14
basin", so in Sprint 1 you teach it to understand words.
"""

import re

from catalogue import clean_code

STOPWORDS = {"a", "an", "the", "do", "does", "you", "have", "has", "is", "are", "there", "any", "for", "with", "i", "me",
             "my", "want", "need", "please", "show", "what", "which", "of", "in", "to", "and", "or", "sell", "price",
             "cost", "how", "much", "it", "your", "get", "can", "available"}
SYNONYMS = {}
CODE = re.compile(r"\b([A-Za-z]{2,5})\s*-?\s*(\d{3})\b")


def words(text):
    """The words in a question or a product, ready to compare."""
    return text.lower().split()


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
    return 0


def codes_in(question):
    """Product codes typed in a question, cleaned the same way as the list: 'opc-180' gives ['OPC 180']."""
    return [clean_code(letters + " " + digits) for letters, digits in CODE.findall(question)]


def find(question, products):
    """The codes of the products the customer means, cheapest first. Right now: only exact product codes."""
    wanted = codes_in(question)
    return [p["code"] for p in products if p["code"] in wanted]


def decide(found):
    """What to do. Nothing found: say no. One product: answer. More than one: ask which one."""
    if not found:
        return "refuse"
    if len(found) == 1:
        return "answer"
    return "ask"
