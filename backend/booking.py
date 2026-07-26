"""
booking.py
----------
Mock calendar integration (FR-4). A real deployment would call out to
Calendly, Google Calendar, or an internal scheduling API — this stand-in
uses an in-memory schedule so the agent can demonstrate "check availability
and book a slot" without needing external accounts.
"""

from datetime import datetime
from typing import Optional

_SCHEDULE = {
    "Saturday 7:00am Spin": {"capacity": 12, "booked": 9},
    "Saturday 8:30am Beginner Yoga": {"capacity": 15, "booked": 15},
    "Sunday 9:00am HIIT": {"capacity": 10, "booked": 4},
    "Monday 6:00pm Spin": {"capacity": 12, "booked": 11},
    "Wednesday 6:00am Bootcamp": {"capacity": 8, "booked": 3},
}


def list_availability() -> list:
    return [
        {"class": name, "spots_left": info["capacity"] - info["booked"], "full": info["booked"] >= info["capacity"]}
        for name, info in _SCHEDULE.items()
    ]


def find_class(mention: str) -> Optional[str]:
    """Very simple substring match against class names, for demo purposes."""
    mention_lower = mention.lower()
    for name in _SCHEDULE:
        if any(word in mention_lower for word in name.lower().split()):
            return name
    return None


def book(class_name: str) -> dict:
    info = _SCHEDULE.get(class_name)
    if info is None:
        return {"success": False, "message": f"I couldn't find a class called '{class_name}'."}
    if info["booked"] >= info["capacity"]:
        return {"success": False, "message": f"'{class_name}' is fully booked, unfortunately."}
    info["booked"] += 1
    return {"success": True, "message": f"You're booked into {class_name}. See you there!",
             "booked_at": datetime.utcnow().isoformat()}
