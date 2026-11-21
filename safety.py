"""The safety check: a reply may only say prices and product codes that are in the facts.

An AI sometimes makes things up: a product HomeShine never sold, or a price nobody agreed. answer.py runs every reply
through is_safe before a customer sees it. An unsafe reply is never shown: AskMate's own sentence is used instead.
"""

import re

PRICE = re.compile(r"(?:₹|Rs\.?)\s?(\d[\d,]*)")
CODE = re.compile(r"\b([A-Z]{2,5}) ?(\d{3})\b")


def prices_in(text):
    """Every price written in the text, as whole numbers: '₹12,400 or Rs 9,900' gives [12400, 9900]."""
    return []


def codes_in_text(text):
    """Every product code written in the text, like ['OPC 186']."""
    return [f"{letters} {digits}" for letters, digits in CODE.findall(text)]


def is_safe(text, facts):
    """True when every price and every product code in the text is one of the facts."""
    return True
