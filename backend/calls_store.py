"""
calls_store.py
---------------
Call logging (FR-6): every simulated call is recorded as a transcript with
turn-by-turn detail and an outcome (resolved vs. escalated), so staff could
review it — this is the "dashboard staff can review" requirement.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
CALLS_PATH = STORAGE_DIR / "calls.json"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _load() -> dict:
    if CALLS_PATH.exists():
        return json.loads(CALLS_PATH.read_text())
    return {}


def _save(calls: dict) -> None:
    CALLS_PATH.write_text(json.dumps(calls, indent=2))


def create_call(greeting: str) -> dict:
    calls = _load()
    call_id = str(uuid.uuid4())[:8]
    call = {
        "id": call_id,
        "started_at": datetime.utcnow().isoformat(),
        "ended_at": None,
        "turns": [{"speaker": "agent", "text": greeting}],
        "escalated": False,
        "resolved": False,
        "status": "in_progress",
    }
    calls[call_id] = call
    _save(calls)
    return call


def append_turn(call_id: str, speaker: str, text: str, meta: Optional[dict] = None) -> Optional[dict]:
    calls = _load()
    call = calls.get(call_id)
    if call is None:
        return None
    turn = {"speaker": speaker, "text": text}
    if meta:
        turn["meta"] = meta
    call["turns"].append(turn)
    if meta and meta.get("escalated"):
        call["escalated"] = True
    _save(calls)
    return call


def end_call(call_id: str) -> Optional[dict]:
    calls = _load()
    call = calls.get(call_id)
    if call is None:
        return None
    call["ended_at"] = datetime.utcnow().isoformat()
    call["status"] = "escalated" if call["escalated"] else "resolved"
    call["resolved"] = not call["escalated"]
    _save(calls)
    return call


def list_calls() -> list:
    calls = _load()
    result = list(calls.values())
    result.sort(key=lambda c: c["started_at"], reverse=True)
    return result


def get_call(call_id: str) -> Optional[dict]:
    return _load().get(call_id)
