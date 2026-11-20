"""Ask your AskMate one question, with the real AI if your .env has a key.

Type:  python try_ai.py "Do you have a rimless toilet?"
"""

import sys

import ai
from answer import reply
from catalogue import load_catalogue

question = " ".join(sys.argv[1:]) or "Do you have a rimless toilet?"
result = reply(question, load_catalogue())
print(result["answer"])
print(f"(written by: {result['model']}{'. The AI is resting' if result['resting'] else ''})")
if not ai.providers():
    print("No key found in .env, so AskMate used its own sentence. That answer is just as right.")
