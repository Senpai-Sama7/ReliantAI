"""
HVAC AI Dispatch — Centralized Configuration
Loads .env, validates required keys, and exports all constants.
Import this module first in every other module.
"""

import os
import sys
import logging
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env from project root ──────────────────────────────
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)


# ── Validation helper ─────────────────────────────────────────
def _require(name: str) -> str:
    """Return env var or a placeholder if missing."""
    val = os.environ.get(name)
    if not val:
        # If we're just doing triage tests or local dev, don't crash
        if os.environ.get("ENV") == "test":
            return f"MOCK_{name}"
        print(f"[FATAL] Missing required environment variable: {name}", file=sys.stderr)
        print("        Copy .env.example → .env and fill in your keys.", file=sys.stderr)
        sys.exit(1)
    return val


# ── Required secrets ──────────────────────────────────────────
GEMINI_API_KEY: str = _require("GEMINI_API_KEY")
LANGSMITH_API_KEY: str = _require("LANGSMITH_API_KEY")
TWILIO_SID: str = _require("TWILIO_SID")
TWILIO_TOKEN: str = _require("TWILIO_TOKEN")
TWILIO_FROM_PHONE: str = _require("TWILIO_FROM_PHONE")
COMPOSIO_API_KEY: str = _require("COMPOSIO_API_KEY")
OWNER_PHONE: str = _require("OWNER_PHONE")
TECH_PHONE_NUMBER: str = _require("TECH_PHONE_NUMBER")

# ── Optional / defaulted config ──────────────────────────────
DISPATCH_API_KEY: str = os.environ.get("DISPATCH_API_KEY", "change-me-in-env")
DATABASE_PATH: str = os.environ.get("DATABASE_PATH", "dispatch.db")
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
ENV: str = os.environ.get("ENV", "dev").lower()

# ── LangSmith tracing env vars (set once at import time) ─────
# NOTE: LangSmith tracing temporarily disabled during Gemini migration.
# Re-enable once LangSmith API key permissions are verified.
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ.pop("LANGCHAIN_API_KEY", None)

if DISPATCH_API_KEY == "change-me-in-env" and ENV != "test":
    print("[FATAL] DISPATCH_API_KEY must be set to a real value in production.", file=sys.stderr)
    sys.exit(1)

# ── LLM config ────────────────────────────────────────────────
# CrewAI v1.10 uses litellm for model routing.
# "gemini/" prefix tells litellm to use the Google Gemini provider.
# litellm reads from GEMINI_API_KEY or GOOGLE_API_KEY env vars.
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY  # litellm compat
LLM_MODEL: str = "gemini/gemini-3.1-flash"
LLM_TEMPERATURE: float = 0.0
LLM_MAX_TOKENS: int = 900

# ── Owner / Business Info ───────────────────────────────────
OWNER_INFO = {
    "name": "Douglas Mitchell",
    "email": "DouglasMitchell@ReliantAI.org",
    "phone": "+1-832-947-7028",
    "location": "Houston, TX",
    "linkedin": "https://www.linkedin.com/in/douglas-mitchell-the-architect/",
    "company": "ReliantAI.org",
    "tagline": "Tailored SEO & Geo-targeted websites for businesses",
}

# ── Houston-specific constants ────────────────────────────────
SAFETY_KEYWORDS: list[str] = [
    "gas", "co ", "carbon monoxide", "smoke", "fire", "explosion",
]
EMERGENCY_HEAT_THRESHOLD_F: float = 95.0
EMERGENCY_COLD_THRESHOLD_F: float = 42.0
HEAT_KEYWORDS: list[str] = ["ac", "air", "cool", "heat", "hot", "conditioning", "acondicionado"]
COLD_KEYWORDS: list[str] = ["heat", "furnace", "heater", "warm", "calefactor", "calentador"]
URGENT_KEYWORDS: list[str] = [
    "not cooling", "not heating", "no hot water", "leak", "flood",
    "broken", "stopped", "died", "not working", "no air", "tripping",
    "noise", "rattling", "grinding", "banging", "cycling", "humidity",
    "ice", "frozen", "dripping", "hot", "not as cold", "not turning",
    "not responding", "wrong", "smell", "warm air", "no funciona",
]

HOUSTON_ZONES: list[str] = [
    "Katy/West Houston",
    "Sugar Land/SW Houston",
    "The Woodlands/North",
    "Heights/Inner Loop",
    "Pearland/South",
    "Pasadena/East",
    "Cypress/NW Houston",
    "Spring/Klein",
    "Humble/Kingwood/NE",
    "Missouri City/Fort Bend",
]

# ── Logging setup ─────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"

def setup_logging(name: str = "hvac_dispatch") -> logging.Logger:
    """Configure and return a logger with console + file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    if not logger.handlers:
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console)

        fh = logging.FileHandler("hvac_dispatch.log")
        fh.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(fh)

    return logger
