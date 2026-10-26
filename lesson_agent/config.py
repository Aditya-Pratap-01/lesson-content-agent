
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL_NAME = os.getenv(
    "GROQ_MODEL_NAME",
    "openai/gpt-oss-120b",
).strip()

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
DATABASE_PATH = PROJECT_ROOT / os.getenv(
    "DATABASE_PATH", "data/agent_memory.db"
)
OUTPUT_DIR = PROJECT_ROOT / os.getenv("OUTPUT_DIR", "output")


def validate_config() -> None:
    if not GROQ_API_KEY or GROQ_API_KEY == "your_actual_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY missing hai. Project root ki .env file check karo."
        )

    if MAX_RETRIES < 0 or MAX_RETRIES > 2:
        raise ValueError("MAX_RETRIES 0 se 2 ke beech hona chahiye.")

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
