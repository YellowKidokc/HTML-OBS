"""Central configuration and filesystem layout.

Generated data NEVER lives inside source-code directories. Everything the
engine writes goes under data/ resolved relative to the project root.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # dotenv is optional at runtime; app must still open
    pass

# Project root = the folder that contains this atlas/ package.
ROOT = Path(__file__).resolve().parent.parent

DATA = ROOT / "data"
SOURCES = DATA / "sources"
CANONICAL = DATA / "canonical"
EXPORTS = DATA / "exports"
RENDERED = DATA / "rendered"
RECEIPTS = DATA / "receipts"
BACKUPS = DATA / "backups"
LOGS = DATA / "logs"
DB_PATH = DATA / "atlas.db"

PROMPTS = ROOT / "prompts"
TEMPLATES = ROOT / "templates"

ALL_DATA_DIRS = [DATA, SOURCES, CANONICAL, EXPORTS, RENDERED, RECEIPTS, BACKUPS, LOGS]


def ensure_dirs() -> None:
    """Create every required data folder. Safe to call repeatedly."""
    for d in ALL_DATA_DIRS:
        d.mkdir(parents=True, exist_ok=True)


# ---- AI provider config (never hard-code secrets) ------------------------

def deepseek_api_key() -> str:
    return os.environ.get("DEEPSEEK_API_KEY", "").strip()


def deepseek_model() -> str:
    return os.environ.get("DEEPSEEK_MODEL", "deepseek-chat").strip()


def deepseek_base_url() -> str:
    return os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()


def force_mock_ai() -> bool:
    return os.environ.get("ATLAS_USE_MOCK_AI", "0").strip() in ("1", "true", "True")


# Versioned rubric / method identifiers (kept versioned per spec Q, R).
METHOD_VERSION = "method-0.1.0"
ATLAS_RUBRIC = "ATLAS_1.0"
REFTEST_VERSION = "R1-R8_v1"
