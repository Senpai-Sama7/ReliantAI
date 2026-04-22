"""
triage.py — Local urgency triage logic for HVAC dispatch.

This is the production-grade, zero-AI fallback triage engine.
Used by main.py when CrewAI is unavailable, and by the test suite
for scenario validation.
"""

from datetime import datetime, timezone

from config import (
    SAFETY_KEYWORDS, URGENT_KEYWORDS,
    HEAT_KEYWORDS, COLD_KEYWORDS,
    EMERGENCY_HEAT_THRESHOLD_F, EMERGENCY_COLD_THRESHOLD_F,
)


def triage_urgency_local(description: str, outdoor_temp_f: float = 80.0) -> dict:
    desc_lower = description.lower()
    safety_hit = any(k in desc_lower for k in SAFETY_KEYWORDS)
    heat_emergency = (outdoor_temp_f > EMERGENCY_HEAT_THRESHOLD_F and any(w in desc_lower for w in HEAT_KEYWORDS))
    cold_emergency = (outdoor_temp_f < EMERGENCY_COLD_THRESHOLD_F and any(w in desc_lower for w in COLD_KEYWORDS))
    emergency_check = heat_emergency or cold_emergency
    urgent_hit = any(k in desc_lower for k in URGENT_KEYWORDS)

    if safety_hit:
        level, action = "LIFE_SAFETY", "ESCALATE_911_AND_OWNER_IMMEDIATELY"
    elif emergency_check or "emergency" in desc_lower:
        level, action = "EMERGENCY", "DISPATCH_NEXT_AVAILABLE_WITH_OWNER_APPROVAL"
    elif urgent_hit:
        level, action = "URGENT", "SAME_DAY_DISPATCH"
    else:
        level, action = "ROUTINE", "NEXT_AVAILABLE_SLOT"

    return {
        "urgency_level": level,
        "recommended_action": action,
        "safety_flag": level == "LIFE_SAFETY",
        "outdoor_temp_f": outdoor_temp_f,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
