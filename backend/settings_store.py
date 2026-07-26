"""
settings_store.py
------------------
Agent configuration (FR-7, FR-8, FR-9): business name, agent name, greeting,
escalation keywords, and language. Editable from the Settings view without
touching code.
"""

import json
from pathlib import Path

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
SETTINGS_PATH = STORAGE_DIR / "settings.json"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SETTINGS = {
    "business_name": "Riverside Fitness",
    "agent_name": "Ava",
    "greeting": "Thanks for calling Riverside Fitness, this is Ava. How can I help you today?",
    "voice_id": "en_samantha",
    "escalation_keywords": [
        "complaint", "refund", "injury", "hurt", "emergency", "accident",
        "lawsuit", "sue", "angry", "manager", "cancel my membership", "dispute",
    ],
    "language": "en",
    "fallback_message": "I don't have that information yet — let me connect you with our team so they can help directly.",
}


def get_settings() -> dict:
    if SETTINGS_PATH.exists():
        return json.loads(SETTINGS_PATH.read_text())
    save_settings(DEFAULT_SETTINGS)
    return DEFAULT_SETTINGS


def save_settings(settings: dict) -> dict:
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2))
    return settings
