#!/usr/bin/env python3
"""
HVAC AI Dispatch Crew — Houston, TX
Production-Ready | CrewAI + Gemini + Twilio + Composio + LangSmith
Author: PharaohDoug AI Agency  |  March 2026

Env vars loaded via config.py (which reads .env automatically).
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

# ── Project config (loads .env, validates keys) ──────────────
from config import (
    TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM_PHONE,
    COMPOSIO_API_KEY, OWNER_PHONE, TECH_PHONE_NUMBER,
    LLM_MODEL,
    SAFETY_KEYWORDS, URGENT_KEYWORDS,
    EMERGENCY_HEAT_THRESHOLD_F, EMERGENCY_COLD_THRESHOLD_F,
    HEAT_KEYWORDS, COLD_KEYWORDS,
    setup_logging,
)
# ── Third-party ─────────────────────────────────────────────
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool as crewai_tool
from langsmith import traceable
from tenacity import retry, stop_after_attempt, wait_fixed
from twilio.rest import Client as TwilioClient
import threading

# Lock for thread-safe agent initialization
_agent_init_lock = threading.Lock()

# ── Database ─────────────────────────────────────────────────
from database import save_dispatch, log_message

logger = setup_logging("hvac_dispatch")


# ── Twilio helper (with tenacity retry) ──────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def _twilio_send(to: str, body: str) -> str:
    """Send SMS via Twilio with automatic retry on transient failure."""
    client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
    msg = client.messages.create(body=body, from_=TWILIO_FROM_PHONE, to=to)
    logger.info("SMS sent to %s: SID=%s", to, msg.sid)
    log_message(direction="outbound", phone=to, body=body, sms_sid=msg.sid)
    return msg.sid


# ════════════════════════════════════════════════════════════
# TOOLS
# ════════════════════════════════════════════════════════════

@crewai_tool
def triage_urgency(description: str, outdoor_temp_f: float = 80.0) -> str:
    """
    Houston-specific urgency classifier.
    Levels: LIFE_SAFETY | EMERGENCY | URGENT | ROUTINE
    Always returns valid JSON.
    LIFE_SAFETY => gas/CO/smoke => immediate 911 escalation.
    EMERGENCY   => no AC > 95°F or no heat < 40°F.
    """
    desc_lower = description.lower()

    # ── Safety check (highest priority) ──
    safety_hit = any(k in desc_lower for k in SAFETY_KEYWORDS)

    # ── Emergency check (Houston weather extremes) ──
    heat_emergency = (
        outdoor_temp_f > EMERGENCY_HEAT_THRESHOLD_F
        and any(w in desc_lower for w in HEAT_KEYWORDS)
    )
    cold_emergency = (
        outdoor_temp_f < EMERGENCY_COLD_THRESHOLD_F
        and any(w in desc_lower for w in COLD_KEYWORDS)
    )
    emergency_check = heat_emergency or cold_emergency

    # ── Urgent keyword scan ──
    urgent_hit = any(k in desc_lower for k in URGENT_KEYWORDS)

    # ── Classify ──
    if safety_hit:
        level = "LIFE_SAFETY"
        action = "ESCALATE_911_AND_OWNER_IMMEDIATELY"
    elif emergency_check or "emergency" in desc_lower:
        level = "EMERGENCY"
        action = "DISPATCH_NEXT_AVAILABLE_WITH_OWNER_APPROVAL"
    elif urgent_hit:
        level = "URGENT"
        action = "SAME_DAY_DISPATCH"
    else:
        level = "ROUTINE"
        action = "NEXT_AVAILABLE_SLOT"

    result = {
        "urgency_level": level,
        "recommended_action": action,
        "safety_flag": level == "LIFE_SAFETY",
        "outdoor_temp_f": outdoor_temp_f,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    logger.info("Triage result: %s", result)
    return json.dumps(result)


@crewai_tool
def check_tech_availability(requested_date: str, skill_needed: str = "general") -> str:
    """
    Check Google Calendar via Composio for available technicians.
    Returns JSON list of available slots and technician names.
    Raises RuntimeError if the Composio calendar integration is unavailable.
    """
    import urllib.request
    import urllib.error

    try:
        url = (
            "https://backend.composio.dev/api/v1/actions/"
            "GOOGLECALENDAR_LIST_EVENTS/execute"
        )
        payload = json.dumps({
            "connectedAccountId": COMPOSIO_API_KEY,
            "input": {
                "calendarId": "primary",
                "q": skill_needed,
                "timeMin": requested_date,
            },
        }).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": COMPOSIO_API_KEY,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            return json.dumps({"status": "live", "calendar_data": data})
    except Exception as exc:
        logger.error("Calendar API unavailable: %s", exc)
        raise RuntimeError(f"Composio calendar integration failed: {exc}") from exc


@crewai_tool
def dispatch_to_tech(
    tech_name: str,
    customer_name: str,
    address: str,
    issue_summary: str,
    eta: str,
    urgency: str,
) -> str:
    """
    Dispatch technician via Twilio SMS.
    Sends SMS to tech AND confirmation to owner.
    Returns dispatch confirmation JSON.
    """
    tech_msg = (
        f"[HVAC DISPATCH] {urgency} — Customer: {customer_name} | "
        f"Address: {address} | Issue: {issue_summary} | ETA: {eta}\n"
        f"Reply ACCEPT or DECLINE."
    )
    owner_msg = (
        f"[HVAC AI] Dispatched {tech_name} to {customer_name} ({address}). "
        f"Urgency: {urgency}. ETA: {eta}. Issue: {issue_summary}."
    )
    _twilio_send(TECH_PHONE_NUMBER, tech_msg)
    _twilio_send(OWNER_PHONE, owner_msg)

    dispatch_id = f"DSP-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"

    save_dispatch(
        dispatch_id=dispatch_id,
        customer_name=customer_name,
        address=address,
        issue_summary=issue_summary,
        urgency=urgency,
        tech_name=tech_name,
        eta=eta,
        status="dispatched",
    )

    result = {
        "dispatch_id": dispatch_id,
        "tech_name": tech_name,
        "customer_name": customer_name,
        "address": address,
        "eta": eta,
        "urgency": urgency,
        "sms_sent": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    logger.info("Dispatch confirmed: %s", result)
    return json.dumps(result)


@crewai_tool
def send_customer_update(
    customer_phone: str,
    customer_name: str,
    tech_name: str,
    eta: str,
    message_type: str,
) -> str:
    """
    Send personalized SMS update to customer.
    message_type: CONFIRMATION | ETA_UPDATE | COMPLETION | SAFETY_TIP | FOLLOWUP
    """
    messages = {
        "CONFIRMATION": (
            f"Hi {customer_name}! Your HVAC service is confirmed. "
            f"Technician {tech_name} is on the way, ETA: {eta}. "
            f"Questions? Reply to this message. — Houston HVAC AI"
        ),
        "ETA_UPDATE": (
            f"Hi {customer_name}, quick update: {tech_name} is running about "
            f"{eta} late due to Houston traffic. We apologize for the wait!"
        ),
        "SAFETY_TIP": (
            f"Hi {customer_name}, while you wait — if you smell gas or CO alarm sounds, "
            f"evacuate immediately and call 911. Your safety is #1. "
            f"Tech {tech_name} arriving soon."
        ),
        "COMPLETION": (
            f"Hi {customer_name}, your HVAC service is complete! "
            f"Happy with the work? Reply YES for 5-star review link. "
            f"Ask about our maintenance plans — saves 30% on repairs!"
        ),
        "FOLLOWUP": (
            f"Hi {customer_name}, this is a 48hr follow-up from your HVAC service. "
            f"Everything running well? If not, reply and we'll fix it free. "
            f"Thanks for choosing us!"
        ),
    }
    body = messages.get(message_type, f"Hi {customer_name}, your tech {tech_name} ETA: {eta}.")
    sid = _twilio_send(customer_phone, body)
    return json.dumps({"status": "sent", "sms_sid": sid, "message_type": message_type})


@crewai_tool
def escalate_to_owner(customer_details: str, urgency_level: str, reason: str) -> str:
    """
    LIFE_SAFETY or ambiguous emergency: immediately SMS owner for human decision.
    This is the mandatory human-in-the-loop gate for gas/CO/fire situations.
    """
    msg = (
        f"⚠️ [HVAC AI ESCALATION] {urgency_level}\n"
        f"Reason: {reason}\n"
        f"Customer: {customer_details}\n"
        f"ACTION REQUIRED: Reply DISPATCH or CALL911"
    )
    sid = _twilio_send(OWNER_PHONE, msg)
    logger.critical("ESCALATION sent to owner: %s", reason)
    return json.dumps({
        "escalated": True,
        "owner_notified": True,
        "sms_sid": sid,
        "awaiting_human_decision": True,
    })


# ════════════════════════════════════════════════════════════
# AGENTS
# ════════════════════════════════════════════════════════════

# Module-level agent variables - initialized by _ensure_agents()
triage_agent: Optional[Agent] = None
intake_agent: Optional[Agent] = None
scheduler_agent: Optional[Agent] = None
dispatch_agent: Optional[Agent] = None
followup_agent: Optional[Agent] = None


def _ensure_agents(outdoor_temp_f: float = 80.0) -> list[Agent]:
    """Initialize agents at module level if not already done."""
    global triage_agent, intake_agent, scheduler_agent, dispatch_agent, followup_agent
    
    # Fast path: check if already initialized without lock
    if triage_agent is not None:
        return [triage_agent, intake_agent, scheduler_agent, dispatch_agent, followup_agent]
    
    # Thread-safe initialization
    with _agent_init_lock:
        # Double-check after acquiring lock
        if triage_agent is not None:
            return [triage_agent, intake_agent, scheduler_agent, dispatch_agent, followup_agent]
        
        # Tools are already decorated with @crewai_tool, use them directly
        triage_agent = Agent(
        role="Houston Emergency Triage Specialist",
        goal=(
            "Instantly classify every inbound HVAC message with ZERO hallucinations. "
            "LIFE_SAFETY (gas/CO/smoke) must ALWAYS escalate to human. Never miss a safety flag."
        ),
        backstory=(
            "You are a calm, battle-tested dispatcher who has protected Houston families "
            "through Category 4 hurricanes and record 108°F heat waves. "
            "You have zero tolerance for ambiguity on safety — when in doubt, escalate."
        ),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        tools=[triage_urgency, escalate_to_owner],
        llm=LLM_MODEL,
    )

    intake_agent = Agent(
        role="Customer Intake Coordinator",
        goal=(
            "Collect complete, accurate intake data: full name, Houston-area address, "
            "callback phone, issue description, and equipment age if possible."
        ),
        backstory=(
            "You are warm, professional, and never miss critical details. "
            "You know that an incomplete address in Houston's sprawling metro "
            "costs 30+ minutes of tech drive time. You always confirm the zip code."
        ),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        tools=[],
        llm=LLM_MODEL,
    )

    scheduler_agent = Agent(
        role="Houston Dispatch Optimizer",
        goal=(
            "Match the best available technician to each call by skill, Houston zone "
            "(Katy / Sugar Land / The Woodlands / Heights / Pearland / Pasadena), "
            "and current workload. Always reserve one emergency time slot."
        ),
        backstory=(
            "You have memorized every freeway, tollway, and shortcut in the Houston metro. "
            "You optimize for minimum drive time and maximum customer satisfaction. "
            "You never double-book and always leave buffer for 2AM emergencies."
        ),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        tools=[check_tech_availability],
        llm=LLM_MODEL,
    )

    dispatch_agent = Agent(
        role="Dispatch Closer & Customer Communicator",
        goal=(
            "Confirm job details with customer, execute dispatch SMS to tech, "
            "send customer confirmation, and log everything with a unique dispatch ID."
        ),
        backstory=(
            "You close the loop fast and professionally. Customers feel cared for, "
            "not just processed. You handle objections calmly and keep the owner informed."
        ),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        tools=[dispatch_to_tech, send_customer_update],
        llm=LLM_MODEL,
    )

    followup_agent = Agent(
        role="Post-Dispatch Retention Specialist",
        goal=(
            "Send safety tips during wait, completion message, 48hr follow-up, "
            "and flag for maintenance contract upsell. Turn one-time customers into "
            "loyal recurring accounts."
        ),
        backstory=(
            "You know that 68% of HVAC customers who receive a follow-up message "
            "sign a maintenance contract within 30 days. You are the reason clients "
            "call back instead of going to the competition."
        ),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        tools=[send_customer_update],
        llm=LLM_MODEL,
    )
    
    return [triage_agent, intake_agent, scheduler_agent, dispatch_agent, followup_agent]


def build_tasks(outdoor_temp_f: float = 80.0):
    """Build task chain — inject outdoor temp for Houston weather-aware triage."""
    agents = _ensure_agents(outdoor_temp_f)
    ta, ia, sa, da, fa = agents

    task_triage = Task(
        description=(
            f"Triage the incoming customer message. Outdoor temp today: {outdoor_temp_f}°F.\n"
            "If LIFE_SAFETY detected (gas/CO/smoke/fire), call escalate_to_owner IMMEDIATELY.\n"
            "Return valid JSON with: urgency_level, recommended_action, safety_flag, reasoning."
        ),
        expected_output=(
            '{"urgency_level":"EMERGENCY","recommended_action":"DISPATCH_NEXT_AVAILABLE_WITH_OWNER_APPROVAL",'
            '"safety_flag":false,"reasoning":"AC failure in 102F heat wave"}'
        ),
        agent=ta,
    )

    task_intake = Task(
        description=(
            "Using the triage context, collect or confirm all intake fields:\n"
            "  - customer_name, address (with Houston zip), callback_phone, issue_description\n"
            "  - equipment_type (AC / furnace / heat pump / combo), approximate equipment age\n"
            "Return structured JSON. If any field missing, note it for human follow-up."
        ),
        expected_output=(
            '{"customer_name":"John Smith","address":"555 Main St, Houston TX 77002",'
            '"phone":"+15551234567","issue":"AC not cooling","equipment":"AC unit","age_years":8}'
        ),
        agent=ia,
        context=[task_triage],
    )

    task_schedule = Task(
        description=(
            "Find the optimal technician using check_tech_availability.\n"
            "Match by: skill required, Houston zone proximity to customer address, current load.\n"
            "For EMERGENCY/LIFE_SAFETY: find slot within 2 hours.\n"
            "Return top 2 options with reasoning."
        ),
        expected_output=(
            '{"option_1":{"tech":"Tech_Alex","zone":"Katy","available":"14:00","match_reason":"zone+skill"},'
            '"option_2":{"tech":"Tech_Maria","zone":"Sugar Land","available":"15:30","match_reason":"skill"}}'
        ),
        agent=sa,
        context=[task_intake],
    )

    task_dispatch = Task(
        description=(
            "Execute dispatch for option_1 from scheduling.\n"
            "1. Call dispatch_to_tech with full details.\n"
            "2. Call send_customer_update with message_type=CONFIRMATION.\n"
            "3. Return dispatch_id and confirmation status."
        ),
        expected_output=(
            '{"dispatch_id":"DSP-20260301-140000","tech_dispatched":"Tech_Alex",'
            '"customer_confirmed":true,"owner_notified":true}'
        ),
        agent=da,
        context=[task_schedule],
    )

    task_followup = Task(
        description=(
            "After dispatch confirmation:\n"
            "1. Send SAFETY_TIP if urgency is EMERGENCY or LIFE_SAFETY.\n"
            "2. Schedule COMPLETION message (send after 4 hours as proxy now).\n"
            "3. Flag for maintenance upsell in follow-up.\n"
            "Return full follow-up plan JSON."
        ),
        expected_output=(
            '{"safety_tip_sent":true,"completion_msg_scheduled":true,'
            '"upsell_flag":true,"followup_48hr_scheduled":true}'
        ),
        agent=fa,
        context=[task_dispatch],
    )

    return [task_triage, task_intake, task_schedule, task_dispatch, task_followup]


# ════════════════════════════════════════════════════════════
# CREW FACTORY
# ════════════════════════════════════════════════════════════

from metrics import track_agent_execution

@traceable(name="hvac_crew_run")
@track_agent_execution("hvac_crew")
def run_hvac_crew(customer_message: str, outdoor_temp_f: float = 80.0) -> dict:
    """
    Main entry point.  Call this from FastAPI or CLI.
    Returns full result dict with dispatch_id and all agent outputs.
    """
    logger.info("Incoming: '%s' | Temp: %s°F", customer_message, outdoor_temp_f)

    _ensure_agents(outdoor_temp_f)
    tasks = build_tasks(outdoor_temp_f=outdoor_temp_f)

    crew = Crew(
        agents=[triage_agent, intake_agent, scheduler_agent, dispatch_agent, followup_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        memory=True,
        cache=True,
    )

    result = crew.kickoff(inputs={
        "customer_message": customer_message,
        "outdoor_temp_f": outdoor_temp_f,
        "location": "Houston, TX",
    })

    logger.info("Crew completed: %s", str(result)[:200])
    return {
        "status": "complete",
        "raw": str(result),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def warmup_node():
    """Trigger initialization of agents and LLM connection."""
    logger.info("🚀 HVAC Node Warmup Sequence Initiated...")
    build_tasks(outdoor_temp_f=80.0)
    logger.info("✅ Node Warmup Complete: Agents Ready.")


# ════════════════════════════════════════════════════════════
# CLI TEST MODE
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="HVAC AI Dispatch — Houston")
    parser.add_argument(
        "--message",
        type=str,
        required=True,
        help="Customer HVAC service request message",
    )
    parser.add_argument("--temp", type=float, default=102.0)
    args = parser.parse_args()

    from database import init_db
    init_db()

    output = run_hvac_crew(customer_message=args.message, outdoor_temp_f=args.temp)
    print(json.dumps(output, indent=2))
