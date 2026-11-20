"""Every setting AskMate uses, read in one place.

Settings come from the computer's environment. On your laptop they come from a file called .env (copy .env.example).
On Render you type them in your service's Environment page. Keys never go in your code and never go to GitHub.
"""

import os
from pathlib import Path

HERE = Path(__file__).parent


def _from_env_file() -> dict:
    """KEY=value lines from .env, if you made one. A setting already in the environment always wins."""
    values = {}
    path = HERE / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                name, value = line.split("=", 1)
                values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def setting(name: str, default: str = "") -> str:
    return os.environ.get(name) or _from_env_file().get(name) or default


COMPANY = "HomeShine"
AI_MODE = setting("ASKMATE_LLM", "auto")          # "fake" means never call a real AI: tests and checks use it
GROQ_KEY = setting("GROQ_API_KEY")
GROQ_MODEL = setting("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_URL = "https://api.groq.com/openai/v1"
GEMINI_KEY = setting("GEMINI_API_KEY")
GEMINI_MODEL = setting("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
DAILY_AI_CALLS = int(setting("DAILY_AI_CALLS", "200"))   # your free key allows more; this keeps strangers from using it all
