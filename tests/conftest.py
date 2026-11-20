"""Tests always use AskMate's own sentences, never a real AI: the same answer every time, and no free calls used up."""

import os

os.environ["ASKMATE_LLM"] = "fake"
