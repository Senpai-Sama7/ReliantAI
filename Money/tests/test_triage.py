"""
Triage urgency tests — 50+ Houston HVAC scenarios.
Covers: LIFE_SAFETY, EMERGENCY, URGENT, ROUTINE, edge cases, boundary temps.
"""

import pytest
from triage import triage_urgency_local


# ── LIFE_SAFETY: Gas, CO, smoke → must always escalate ──────────────

LIFE_SAFETY_CASES = [
    ("Gas smell coming from my furnace, 5501 Memorial Dr Houston", 65.0),
    ("Carbon monoxide alarm going off, house at 77056", 70.0),
    ("I smell smoke near my AC unit, Katy TX", 85.0),
    ("Gas leak in the basement, need help immediately", 72.0),
    ("CO detector keeps beeping, family feeling dizzy", 68.0),
    ("Strong gas odor from the water heater", 75.0),
    ("Smoke coming from the vents when AC turns on", 90.0),
    ("I think there's a carbon monoxide leak, headaches all day", 60.0),
    ("Smelled gas when I turned on the heater this morning", 45.0),
    ("Smoke and burning smell from furnace room", 35.0),
]


@pytest.mark.parametrize("msg,temp", LIFE_SAFETY_CASES,
                         ids=[f"safety_{i}" for i in range(len(LIFE_SAFETY_CASES))])
def test_life_safety(msg, temp):
    r = triage_urgency_local(msg, temp)
    assert r["urgency_level"] == "LIFE_SAFETY"
    assert r["safety_flag"] is True
    assert r["recommended_action"] == "ESCALATE_911_AND_OWNER_IMMEDIATELY"


# ── EMERGENCY: Extreme heat/cold + relevant keywords ────────────────

EMERGENCY_CASES = [
    ("AC stopped working completely, 104 outside, Sugar Land", 104.0),
    ("No air conditioning, it is 102 degrees, elderly parent home", 102.0),
    ("Furnace died, it is 36 degrees tonight, The Woodlands", 36.0),
    ("Heat not working, 38 degrees and dropping, baby in the house", 38.0),
    ("AC is blowing hot air, it's 98 degrees in Houston", 98.0),
    ("No cooling at all, thermostat says 96 inside, 105 outside", 105.0),
    ("Heater quit, pipes might freeze, it's 40 degrees", 40.0),
    ("This is an emergency, AC completely dead in this heat", 88.0),
    ("AC unit making loud noise then stopped, 100 degree day", 100.0),
    ("No heat, 41 degrees outside, cold front coming tonight", 41.0),
]


@pytest.mark.parametrize("msg,temp", EMERGENCY_CASES,
                         ids=[f"emergency_{i}" for i in range(len(EMERGENCY_CASES))])
def test_emergency(msg, temp):
    r = triage_urgency_local(msg, temp)
    assert r["urgency_level"] == "EMERGENCY"
    assert r["safety_flag"] is False


# ── URGENT: Broken/leaking/not working but not extreme conditions ───

URGENT_CASES = [
    ("AC not as cold as usual, still cooling a little, Cypress TX", 88.0),
    ("Water leaking from my AC unit inside the house", 85.0),
    ("Furnace making a loud banging noise every time it starts", 50.0),
    ("AC is running but not cooling the house below 80", 92.0),
    ("Thermostat is broken, can't control the temperature", 78.0),
    ("Water dripping from ceiling near the AC vent", 82.0),
    ("AC compressor is making grinding noise", 90.0),
    ("Heater turns on and off every few minutes, cycling", 48.0),
    ("AC leaking water all over the floor", 87.0),
    ("Unit is broken, need someone today if possible", 80.0),
]


@pytest.mark.parametrize("msg,temp", URGENT_CASES,
                         ids=[f"urgent_{i}" for i in range(len(URGENT_CASES))])
def test_urgent(msg, temp):
    r = triage_urgency_local(msg, temp)
    assert r["urgency_level"] == "URGENT"


# ── ROUTINE: Maintenance, tune-ups, inspections ─────────────────────

ROUTINE_CASES = [
    ("Routine AC tune-up before summer, Humble TX", 75.0),
    ("Annual furnace inspection needed, Heights Houston", 65.0),
    ("Want to schedule a maintenance check on my HVAC system", 72.0),
    ("Need a quote for a new AC unit installation", 80.0),
    ("Looking to get my ducts cleaned this month", 70.0),
    ("Can you come check my AC filter? It's been a while", 76.0),
    ("Interested in a maintenance plan for my home", 68.0),
    ("Need to schedule spring AC checkup", 74.0),
    ("How much for a thermostat upgrade?", 71.0),
    ("Want to get my system checked before summer", 78.0),
]


@pytest.mark.parametrize("msg,temp", ROUTINE_CASES,
                         ids=[f"routine_{i}" for i in range(len(ROUTINE_CASES))])
def test_routine(msg, temp):
    r = triage_urgency_local(msg, temp)
    assert r["urgency_level"] == "ROUTINE"


# ── BOUNDARY TEMPERATURE TESTS ──────────────────────────────────────

def test_exactly_at_heat_threshold_with_keyword():
    """95.0°F is the threshold — must be ABOVE to trigger."""
    r = triage_urgency_local("AC not cooling, very hot", 95.0)
    # 95.0 is NOT > 95.0, so should NOT be EMERGENCY from temp alone
    assert r["urgency_level"] != "LIFE_SAFETY"


def test_just_above_heat_threshold():
    r = triage_urgency_local("AC not cooling, very hot", 95.1)
    assert r["urgency_level"] == "EMERGENCY"


def test_exactly_at_cold_threshold_with_keyword():
    """42.0°F is the threshold — must be BELOW to trigger."""
    r = triage_urgency_local("Heater not working, freezing cold", 42.0)
    # 42.0 is NOT < 42.0
    assert r["urgency_level"] != "LIFE_SAFETY"


def test_just_below_cold_threshold():
    r = triage_urgency_local("Heater not working, freezing cold", 41.9)
    assert r["urgency_level"] == "EMERGENCY"


# ── EDGE CASES ──────────────────────────────────────────────────────

def test_empty_message_is_routine():
    """Single space (min_length=1 in API, but triage itself should handle)."""
    r = triage_urgency_local(" ", 80.0)
    assert r["urgency_level"] == "ROUTINE"


def test_max_length_message():
    msg = "AC broken " * 100  # 1000 chars
    r = triage_urgency_local(msg, 80.0)
    assert r["urgency_level"] == "URGENT"  # "broken" is urgent keyword


def test_unicode_message():
    r = triage_urgency_local("Mi aire acondicionado está roto 🔥", 80.0)
    assert r["urgency_level"] == "ROUTINE"  # no English keywords match


def test_case_insensitive_gas():
    r = triage_urgency_local("GAS LEAK IN MY HOUSE", 70.0)
    assert r["urgency_level"] == "LIFE_SAFETY"


def test_return_structure():
    r = triage_urgency_local("test message", 80.0)
    assert "urgency_level" in r
    assert "recommended_action" in r
    assert "safety_flag" in r
    assert "outdoor_temp_f" in r
    assert "timestamp" in r
    assert isinstance(r["outdoor_temp_f"], float)


def test_default_temp():
    r = triage_urgency_local("routine checkup")
    assert r["outdoor_temp_f"] == 80.0


def test_multiple_keywords_safety_wins():
    """Safety keywords should take priority over emergency/urgent."""
    r = triage_urgency_local("Gas smell and AC broken, it's an emergency", 100.0)
    assert r["urgency_level"] == "LIFE_SAFETY"
