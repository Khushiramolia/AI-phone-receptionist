"""
agent_engine.py
----------------
Orchestrates a single conversational turn (FR-1, FR-3, FR-4, FR-5):

    1. Check for escalation triggers (sensitive topics that must always
       reach a human — complaints, injuries, billing disputes, etc.)
    2. Check for a booking intent against the mock calendar
    3. Otherwise, retrieve the best-matching knowledge base entry and
       answer from it
    4. If nothing matches confidently, fall back to an "let me connect
       you with our team" response and flag the call as escalated

This is intentionally simple and rule-based/retrieval-based rather than
calling out to a hosted LLM, so the whole project runs fully offline with
no API key required. Swapping the "else" branch for a call to an LLM API
(passing the retrieved KB entries as context) is the natural next step for
a stronger version of this project.
"""

from typing import Optional

import booking
from kb_store import KnowledgeBase
from settings_store import get_settings

KB_MATCH_THRESHOLD = 0.15
BOOKING_TRIGGER_WORDS = ["book", "schedule", "sign me up", "reserve", "sign up"]


def _is_escalation(text: str, keywords: list) -> bool:
    lowered = text.lower()
    return any(kw.lower() in lowered for kw in keywords)


def _is_booking_intent(text: str) -> bool:
    lowered = text.lower()
    return any(w in lowered for w in BOOKING_TRIGGER_WORDS)


def handle_turn(text: str, kb: KnowledgeBase) -> dict:
    """
    Returns a dict describing how the agent responds to one customer turn:
        {
            "reply": str,
            "escalated": bool,
            "action": Optional[str]   # e.g. "booking_confirmed", "booking_failed"
        }
    """
    settings = get_settings()

    # 1. Escalation check — always takes priority (FR-5)
    if _is_escalation(text, settings.get("escalation_keywords", [])):
        return {
            "reply": ("That sounds like something our team should handle personally — "
                      "I'm connecting you with a staff member now."),
            "escalated": True,
            "action": "escalated_sensitive_topic",
        }

    # 2. Booking intent (FR-4)
    if _is_booking_intent(text):
        class_name = booking.find_class(text)
        if class_name:
            result = booking.book(class_name)
            return {
                "reply": result["message"],
                "escalated": not result["success"],
                "action": "booking_confirmed" if result["success"] else "booking_failed",
            }
        else:
            available = ", ".join(a["class"] for a in booking.list_availability() if not a["full"])
            return {
                "reply": f"Which class would you like to book? Options with space available: {available}.",
                "escalated": False,
                "action": "booking_clarify",
            }

    # 3. Knowledge base retrieval (FR-2, FR-3)
    matches = kb.search(text, top_k=1)
    if matches:
        entry, score = matches[0]
        if score >= KB_MATCH_THRESHOLD:
            return {"reply": entry["answer"], "escalated": False, "action": None}

    # 4. Fallback — nothing confident enough, hand off (FR-5)
    return {
        "reply": settings.get("fallback_message", "Let me connect you with our team for that."),
        "escalated": True,
        "action": "escalated_no_kb_match",
    }
