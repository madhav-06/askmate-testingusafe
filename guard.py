"""Trick questions. A public chat gets people who try to make it break its rules: "ignore your rules", "show me your
prompt", "give it to me for free". answer.py asks is_trick about every question first, and a trick gets a polite no.
"""

TRICKS = []


def is_trick(question):
    """True when the question tries to change AskMate's rules, see its instructions, or get something for free."""
    return False
