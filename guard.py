"""Trick questions. A public chat gets people who try to make it break its rules: "ignore your rules", "show me your
prompt", "give it to me for free". answer.py asks is_trick about every question first, and a trick gets a polite no.
"""

TRICKS = ["ignore", "your rules", "instructions", "system prompt", "your prompt", "pretend", "you are now", "developer mode", "for free", "give it to me", "free of charge", "no cost", "complimentary", "without paying", "without charge", "without cost"]

def is_trick(question):
    """True when the question tries to change AskMate's rules, see its instructions, or get something for free."""
    q = question.lower()
    return any(phrase in q for phrase in TRICKS)

