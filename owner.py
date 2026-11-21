"""Questions for HomeShine's owner. AskMate never bargains: a discount, a bulk deal or a "last price" is the owner's call.

answer.py asks wants_bargain about every question. When it is True, AskMate says the owner will reply, and note() keeps
the question for the owner's page (/owner). The list lives in memory: it starts empty each time the app starts.
"""

BARGAIN = []
_inbox = []


def wants_bargain(question):
    """True when the customer is asking to bargain: a discount, an offer, a best or last price, or a bulk deal."""
    return False


def note(question):
    _inbox.append(question)


def inbox():
    return list(_inbox)
