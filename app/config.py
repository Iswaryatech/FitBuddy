import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
FITNESS_MODEL = os.getenv("FITNESS_MODEL", "gemini-3.8-flash")
TIP_MODEL = os.getenv("TIP_MODEL", "gemini-3.8-flash")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./movemap.db")


def gemini_enabled() -> bool:
    key = GEMINI_API_KEY
    return bool(key) and "PASTE_YOUR" not in key and "YOUR_REAL_KEY" not in key
