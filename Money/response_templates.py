"""
7-Beat Response Model for HVAC Dispatch
Structured SMS/WhatsApp responses following proven persuasion framework.

Based on Citadel's 7-Beat Outreach Model, adapted for customer service:
1. ACKNOWLEDGE - Confirm receipt and show empathy
2. CLASSIFY - State urgency level clearly  
3. NEXT_STEPS - Explain what happens next
4. CTA - Clear call-to-action
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from config import setup_logging, OWNER_INFO

logger = setup_logging("response_templates")


class UrgencyLevel(str, Enum):
    """Standardized urgency levels"""
    EMERGENCY = "emergency"  # Gas leak, no heat in freezing temps, etc.
    HIGH = "high"            # No AC in 95°F+, no heat in 40°F-
    STANDARD = "standard"    # Normal service requests
    LOW = "low"              # Maintenance, quotes


@dataclass
class ResponseBeat:
    """Single beat in the response structure"""
    beat_type: str
    content: str
    required: bool = True


@dataclass  
class BeatResponse:
    """Complete structured response with audit trail"""
    full_text: str
    beats: List[ResponseBeat]
    beat_audit: Dict[str, bool]
    character_count: int
    sms_segments: int


class ResponseTemplateEngine:
    """
    Generates professional, structured SMS responses for HVAC dispatch.
    
    All responses follow the 4-beat framework:
    - ACKNOWLEDGE: Show we heard them and care
    - CLASSIFY: Confirm urgency level  
    - NEXT_STEPS: What we're doing now
    - CTA: What they need to do
    """
    
    # SMS segment limit (160 chars for pure GSM-7, 70 for UCS-2)
    # We target 140 to leave room for signature
    SMS_LIMIT = 140
    
    # Brand info
    BRAND_NAME = OWNER_INFO.get("company", "ReliantAI")
    BRAND_PHONE = OWNER_INFO.get("phone", "+1-832-947-7028")
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load beat templates for each urgency level"""
        return {
            UrgencyLevel.EMERGENCY: {
                "acknowledge": [
                    "Emergency received — {issue_type} is serious.",
                    "Got it — {issue_type} needs immediate attention.",
                    "Understood — {issue_type} flagged as emergency.",
                ],
                "classify": [
                    "PRIORITY DISPATCH activated.",
                    "Emergency protocol engaged.",
                    "URGENT response dispatched.",
                ],
                "next_steps": [
                    "Tech notified, ETA within 1 hour.",
                    "Finding nearest available tech now.",
                    "Dispatching emergency crew.",
                ],
                "cta": [
                    "Reply READY when tech can enter.",
                    "Confirm: Reply YES to lock priority.",
                    "Stay put — help inbound. Reply OK.",
                ],
            },
            UrgencyLevel.HIGH: {
                "acknowledge": [
                    "Received — {issue_type} in this weather is urgent.",
                    "Got it — no {comfort_type} needs fast fix.",
                    "Understood — {issue_type} is high priority.",
                ],
                "classify": [
                    "HIGH PRIORITY queued.",
                    "Fast-track dispatch activated.",
                    "Priority service assigned.",
                ],
                "next_steps": [
                    "Checking tech availability now...",
                    "Matching you with available tech...",
                    "Scheduling next available window...",
                ],
                "cta": [
                    "Reply CONFIRM to hold your slot.",
                    "Lock it in: Reply YES.",
                    "Want this slot? Reply GO.",
                ],
            },
            UrgencyLevel.STANDARD: {
                "acknowledge": [
                    "Thanks for reaching out about {issue_type}.",
                    "Got your request for {issue_type}.",
                    "Received — {issue_type} noted.",
                ],
                "classify": [
                    "Standard service scheduled.",
                    "In the queue for next available.",
                    "Regular service appointment set.",
                ],
                "next_steps": [
                    "Tech will arrive within 4 hours.",
                    "Scheduling for today or tomorrow...",
                    "You'll get ETA once tech is assigned.",
                ],
                "cta": [
                    "Reply OK to confirm address.",
                    "Confirm details: Reply YES.",
                    "Good to go? Reply CONFIRM.",
                ],
            },
            UrgencyLevel.LOW: {
                "acknowledge": [
                    "Thanks for the {issue_type} inquiry.",
                    "Got your {issue_type} request.",
                    "Received — {issue_type} for planning.",
                ],
                "classify": [
                    "Maintenance/quote queued.",
                    "Non-urgent request logged.",
                    "Scheduled for next routine visit.",
                ],
                "next_steps": [
                    "We'll call to schedule soon.",
                    "Coordination team will reach out.",
                    "Expect scheduling call within 24hrs.",
                ],
                "cta": [
                    "Reply TIME for preferred windows.",
                    "Best time to call? Reply with hours.",
                    "Any timing constraints? Reply INFO.",
                ],
            },
        }
    
    def generate_response(
        self,
        issue_type: str,
        urgency: UrgencyLevel,
        comfort_type: Optional[str] = None,
        tech_eta: Optional[str] = None
    ) -> BeatResponse:
        """
        Generate structured 4-beat response.
        
        Args:
            issue_type: Type of issue ("AC not working", "furnace leak", etc.)
            urgency: UrgencyLevel enum
            comfort_type: "cooling" or "heating" (for context-aware templates)
            tech_eta: Optional specific ETA to include
            
        Returns:
            BeatResponse with full text and beat audit
        """
        import random
        
        templates = self.templates.get(urgency, self.templates[UrgencyLevel.STANDARD])
        comfort = comfort_type or ("cooling" if "AC" in issue_type.upper() else "heating")
        
        # Select one template from each beat
        acknowledge = random.choice(templates["acknowledge"]).format(
            issue_type=issue_type,
            comfort_type=comfort
        )
        classify = random.choice(templates["classify"])
        next_steps = tech_eta or random.choice(templates["next_steps"])
        cta = random.choice(templates["cta"])
        
        # Build beats
        beats = [
            ResponseBeat("acknowledge", acknowledge),
            ResponseBeat("classify", classify),
            ResponseBeat("next_steps", next_steps),
            ResponseBeat("cta", cta),
        ]
        
        # Combine with proper spacing
        full_text = f"{acknowledge} {classify} {next_steps} {cta}"
        
        # Calculate SMS segments
        char_count = len(full_text)
        segments = (char_count // 160) + 1 if char_count > 160 else 1
        
        # Build audit
        beat_audit = {
            "acknowledge": len(acknowledge) >= 10,
            "classify": len(classify) >= 5,
            "next_steps": len(next_steps) >= 10,
            "cta": len(cta) >= 5,
            "total_length_valid": char_count <= 640,  # 4 segments max
        }
        
        logger.info(f"Generated {urgency.value} response: {char_count} chars, {segments} segment(s)")
        
        return BeatResponse(
            full_text=full_text,
            beats=beats,
            beat_audit=beat_audit,
            character_count=char_count,
            sms_segments=segments
        )
    
    def generate_followup(
        self,
        dispatch_id: str,
        status: str,
        tech_name: Optional[str] = None,
        eta_minutes: Optional[int] = None
    ) -> str:
        """Generate follow-up status update"""
        if status == "tech_assigned":
            return f"Tech {tech_name or 'assigned'} en route. ETA {eta_minutes or '30'} mins. Reply OK to confirm you're on-site."
        elif status == "tech_arrived":
            return f"Your tech has arrived and is assessing the situation. Stand by for diagnosis."
        elif status == "job_complete":
            return f"Job complete! Invoice sent separately. Rate your experience: Reply 1-5. Questions? Call {self.BRAND_PHONE}"
        elif status == "delayed":
            return f"Update: Tech running {eta_minutes or '15'} mins behind. New ETA being calculated. Reply OK or call {self.BRAND_PHONE}"
        else:
            return f"Status update for {dispatch_id}: {status}. Questions? Call {self.BRAND_PHONE}"
    
    def generate_cold_escalation(self, original_issue: str) -> str:
        """Generate response when cold lead becomes hot"""
        return (
            f"Update on your {original_issue}: We've escalated this to priority status "
            f"based on weather conditions. Tech will arrive within 2 hours. "
            f"Reply URGENT if situation has worsened."
        )


# Convenience functions for direct use
def generate_dispatch_response(
    issue_summary: str,
    urgency: str,
    outdoor_temp: Optional[float] = None
) -> str:
    """
    Generate response for new dispatch.
    
    Args:
        issue_summary: Customer's issue description
        urgency: "life_safety", "emergency", "high", "standard", or "low"
        outdoor_temp: Current temperature (for context)
        
    Returns:
        Formatted SMS response string
    """
    engine = ResponseTemplateEngine()
    
    # Map urgency string to enum (handle both triage and direct levels)
    urgency_map = {
        "life_safety": UrgencyLevel.EMERGENCY,
        "emergency": UrgencyLevel.EMERGENCY,
        "urgent": UrgencyLevel.HIGH,
        "high": UrgencyLevel.HIGH,
        "standard": UrgencyLevel.STANDARD,
        "routine": UrgencyLevel.LOW,
        "low": UrgencyLevel.LOW,
    }
    level = urgency_map.get(urgency.lower(), UrgencyLevel.STANDARD)
    
    # Determine comfort type from issue
    comfort = None
    if any(word in issue_summary.lower() for word in ["ac", "cool", "air", " conditioning"]):
        comfort = "cooling"
    elif any(word in issue_summary.lower() for word in ["heat", "furnace", "warm", "boiler"]):
        comfort = "heating"
    
    response = engine.generate_response(issue_summary, level, comfort)
    return response.full_text


def generate_followup_message(
    dispatch_id: str,
    status: str,
    **kwargs
) -> str:
    """Generate follow-up message"""
    engine = ResponseTemplateEngine()
    return engine.generate_followup(dispatch_id, status, **kwargs)


# Pre-defined quick responses
QUICK_RESPONSES = {
    "welcome": (
        "Thanks for contacting ReliantAI HVAC! "
        "We received your message and are routing it to the right tech now. "
        "You'll get an ETA within 15 mins."
    ),
    "outside_hours": (
        "After-hours emergency line. If this is life-safety (gas leak, electrical fire), "
        f"call 911. For HVAC emergency, leave message or call {OWNER_INFO.get('phone', '+1-832-947-7028')}. "
        "We monitor 24/7 for true emergencies."
    ),
    "unrecognized": (
        "We couldn't understand your message. Reply HELP for options or call "
        f"{OWNER_INFO.get('phone', '+1-832-947-7028')} to speak with dispatch."
    ),
    "help_menu": (
        "ReliantAI HVAC Commands:\n"
        "STATUS - Check your dispatch\n"
        "CANCEL - Cancel request\n"
        "URGENT - Escalate to emergency\n"
        "CALL - Request phone call\n"
        f"Or call: {OWNER_INFO.get('phone', '+1-832-947-7028')}"
    ),
}
