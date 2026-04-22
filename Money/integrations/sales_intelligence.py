"""
Sales Intelligence System Integration
Connects Gmail/lead scoring automation to ReliantAI dispatch system
"""

import os
import json
import requests
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime

from config import setup_logging, OWNER_INFO
from database import save_dispatch, log_message

logger = setup_logging("sales_intelligence")


class LeadScorer:
    """
    Scores leads based on HVAC keywords and urgency signals
    Used by Sales Intelligence System to prioritize leads
    """
    
    # HVAC-relevant keywords with weights
    KEYWORD_WEIGHTS = {
        # High urgency (10-15 points)
        "emergency": 15,
        "urgent": 12,
        "asap": 12,
        "broken": 10,
        "not working": 10,
        "leak": 12,
        "flooding": 15,
        "no heat": 12,
        "no ac": 12,
        "no cooling": 12,
        "no air": 12,
        
        # Medium urgency (5-9 points)
        "repair": 8,
        "fix": 8,
        "service": 5,
        "maintenance": 5,
        "install": 6,
        "replace": 7,
        "quote": 5,
        "estimate": 5,
        
        # Topic keywords (3-5 points)
        "ac": 3,
        "air conditioning": 3,
        "hvac": 5,
        "heating": 3,
        "furnace": 4,
        "thermostat": 3,
        "duct": 3,
        "ventilation": 3,
        "cooling": 3,
        "refrigerant": 4,
        "compressor": 4,
    }
    
    @classmethod
    def score_lead(cls, subject: str, body: str) -> Dict:
        """
        Calculate lead score based on keyword matches
        
        Returns:
            {
                "score": int (0-100),
                "keywords_matched": list,
                "urgency_level": str ("hot", "warm", "cold"),
                "intent_signals": list
            }
        """
        text = f"{subject} {body}".lower()
        score = 0
        keywords_matched = []
        intent_signals = []
        
        for keyword, weight in cls.KEYWORD_WEIGHTS.items():
            if keyword in text:
                score += weight
                keywords_matched.append(keyword)
                
                # Categorize intent
                if weight >= 10:
                    intent_signals.append("urgent_service")
                elif weight >= 5:
                    intent_signals.append("service_request")
                else:
                    intent_signals.append("hvac_interest")
        
        # Cap at 100
        score = min(score, 100)
        
        # Determine urgency level
        if score >= 70:
            urgency_level = "hot"
        elif score >= 40:
            urgency_level = "warm"
        else:
            urgency_level = "cold"
        
        return {
            "score": score,
            "keywords_matched": list(set(keywords_matched)),
            "urgency_level": urgency_level,
            "intent_signals": list(set(intent_signals))
        }


def parse_sales_email(email_data: Dict) -> Dict:
    """
    Parse email data from Sales Intelligence System
    
    Args:
        email_data: Raw email data from Gmail scanner
        
    Returns:
        Parsed lead data ready for dispatch creation
    """
    scorer = LeadScorer()
    score_result = scorer.score_lead(
        email_data.get("subject", ""),
        email_data.get("body", "")
    )
    
    return {
        "sender_name": email_data.get("from_name", "Unknown"),
        "sender_email": email_data.get("from_email", ""),
        "subject": email_data.get("subject", ""),
        "preview": email_data.get("body", "")[:500],  # First 500 chars
        "timestamp": email_data.get("received_at", datetime.now().isoformat()),
        "lead_score": score_result,
        "sheet_row_id": email_data.get("google_sheets_row"),
        "hubspot_contact_id": email_data.get("hubspot_contact_id"),
        "source": "gmail_scanner"
    }


def create_dispatch_from_sales_lead(lead_data: Dict) -> str:
    """
    Top-level function to create a dispatch from a sales lead
    
    This is the main entry point used by the webhook endpoint.
    
    Args:
        lead_data: Parsed lead data from Sales Intelligence System
        
    Returns:
        dispatch_id: The ID of the created dispatch
    """
    connector = SalesIntelligenceConnector()
    result = connector.receive_lead(lead_data)
    
    if result.get("status") == "created":
        return result.get("dispatch_id")
    elif result.get("status") == "skipped":
        logger.info(f"Lead skipped: {result.get('reason')}")
        return f"SKIPPED-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    else:
        logger.error(f"Failed to create dispatch: {result}")
        raise RuntimeError(f"Dispatch creation failed: {result.get('error', 'Unknown error')}")


@dataclass
class LeadScore:
    """Lead scoring data from Sales Intelligence System"""
    score: int
    keywords_matched: List[str]
    urgency_level: str  # "hot", "warm", "cold"
    intent_signals: List[str]
    

@dataclass
class SalesLead:
    """Lead data from Sales Intelligence System"""
    source: str  # "gmail", "hubspot", "manual"
    sender_name: str
    sender_email: str
    subject: str
    preview: str
    timestamp: str
    lead_score: LeadScore
    sheet_row_id: Optional[str] = None
    hubspot_contact_id: Optional[str] = None


class SalesIntelligenceConnector:
    """
    Connects Sales Intelligence System to ReliantAI dispatch
    
    Your Sales Intelligence System:
    - Monitors Gmail for leads
    - Scores leads (hot=70+, warm=40-69, cold=<40)
    - Creates HubSpot contacts
    - Logs to Google Sheets
    - Sends Slack alerts
    
    This connector receives those leads and creates dispatches
    """
    
    def __init__(self):
        self.owner_email = OWNER_INFO.get("email", "DouglasMitchell@ReliantAI.org")
        self.owner_phone = OWNER_INFO.get("phone", "+1-832-947-7028")
        self.hot_threshold = 70
        self.warm_threshold = 40
    
    def check_connection(self) -> Dict:
        """Check if the Sales Intelligence integration is properly configured"""
        return {
            "status": "active",
            "owner_configured": bool(self.owner_email and self.owner_phone),
            "hot_threshold": self.hot_threshold,
            "warm_threshold": self.warm_threshold,
            "capabilities": [
                "receive_leads",
                "score_leads", 
                "create_dispatches",
                "notify_owner"
            ]
        }
        
    def receive_lead(self, lead_data: Dict) -> Dict:
        """
        Receive a lead from Sales Intelligence System
        
        Expected lead_data format:
        {
            "sender_name": "John Doe",
            "sender_email": "john@company.com",
            "subject": "Urgent: AC not working",
            "preview": "My AC stopped working, need service ASAP...",
            "timestamp": "2026-03-03T21:42:00Z",
            "lead_score": {
                "score": 85,
                "keywords_matched": ["urgent", "asap", "not working"],
                "urgency_level": "hot",
                "intent_signals": ["service_request", "urgent"]
            },
            "sheet_row_id": "A12",
            "hubspot_contact_id": "12345"
        }
        """
        try:
            lead = self._parse_lead(lead_data)
            
            # Determine if this is an HVAC lead
            if not self._is_hvac_lead(lead):
                logger.info(f"Lead from {lead.sender_email} not HVAC-related, skipping dispatch")
                return {"status": "skipped", "reason": "not_hvac_lead"}
            
            # Create dispatch for hot/warm leads
            if lead.lead_score.score >= self.hot_threshold:
                return self._create_hot_lead_dispatch(lead)
            elif lead.lead_score.score >= self.warm_threshold:
                return self._create_warm_lead_dispatch(lead)
            else:
                logger.info(f"Cold lead ({lead.lead_score.score} pts), logged only")
                return {"status": "logged", "score": lead.lead_score.score}
                
        except Exception as e:
            logger.error(f"Failed to process lead: {e}")
            return {"status": "error", "error": str(e)}
    
    def _parse_lead(self, data: Dict) -> SalesLead:
        """Parse lead data from Sales Intelligence System"""
        score_data = data.get("lead_score", {})
        
        lead_score = LeadScore(
            score=score_data.get("score", 0),
            keywords_matched=score_data.get("keywords_matched", []),
            urgency_level=score_data.get("urgency_level", "cold"),
            intent_signals=score_data.get("intent_signals", [])
        )
        
        return SalesLead(
            source=data.get("source", "gmail"),
            sender_name=data.get("sender_name", "Unknown"),
            sender_email=data.get("sender_email", ""),
            subject=data.get("subject", ""),
            preview=data.get("preview", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            lead_score=lead_score,
            sheet_row_id=data.get("sheet_row_id"),
            hubspot_contact_id=data.get("hubspot_contact_id")
        )
    
    def _is_hvac_lead(self, lead: SalesLead) -> bool:
        """Check if lead is HVAC-related based on keywords"""
        hvac_keywords = [
            "ac", "air conditioning", "hvac", "heating", "cooling",
            "furnace", "thermostat", "ventilation", "duct", "repair",
            "maintenance", "service", "not working", "broken", "leak"
        ]
        
        text = f"{lead.subject} {lead.preview}".lower()
        return any(keyword in text for keyword in hvac_keywords)
    
    def _create_hot_lead_dispatch(self, lead: SalesLead) -> Dict:
        """Create urgent dispatch for hot leads (70+ score)"""
        dispatch_id = f"SI-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Save to database
        save_dispatch(
            dispatch_id=dispatch_id,
            customer_name=lead.sender_name,
            customer_phone=lead.sender_email,  # Will extract phone if available
            issue_summary=f"{lead.subject}\n{lead.preview}",
            urgency="EMERGENCY" if "urgent" in lead.lead_score.keywords_matched else "HIGH",
            status="hot_lead_from_sales_intel",
            crew_result={
                "source": "sales_intelligence",
                "lead_score": lead.lead_score.score,
                "keywords": lead.lead_score.keywords_matched,
                "sheet_row": lead.sheet_row_id,
                "hubspot_id": lead.hubspot_contact_id,
                "sender_email": lead.sender_email,
            }
        )
        
        logger.info(f"🔥 HOT LEAD DISPATCH CREATED: {dispatch_id} (Score: {lead.lead_score.score})")
        
        # Send notification to owner
        self._notify_owner(lead, dispatch_id)
        
        return {
            "status": "created",
            "dispatch_id": dispatch_id,
            "priority": "hot",
            "score": lead.lead_score.score,
            "message": "Hot lead converted to dispatch"
        }
    
    def _create_warm_lead_dispatch(self, lead: SalesLead) -> Dict:
        """Create standard dispatch for warm leads (40-69 score)"""
        dispatch_id = f"SI-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        save_dispatch(
            dispatch_id=dispatch_id,
            customer_name=lead.sender_name,
            customer_phone=lead.sender_email,
            issue_summary=f"{lead.subject}\n{lead.preview}",
            urgency="STANDARD",
            status="warm_lead_from_sales_intel",
            crew_result={
                "source": "sales_intelligence",
                "lead_score": lead.lead_score.score,
                "keywords": lead.lead_score.keywords_matched,
                "sheet_row": lead.sheet_row_id,
            }
        )
        
        logger.info(f"🟡 WARM LEAD LOGGED: {dispatch_id} (Score: {lead.lead_score.score})")
        
        return {
            "status": "created",
            "dispatch_id": dispatch_id,
            "priority": "warm",
            "score": lead.lead_score.score
        }
    
    def _notify_owner(self, lead: SalesLead, dispatch_id: str):
        """Send notification to Douglas about hot lead"""
        message = f"""
🔥 HOT LEAD ALERT - ReliantAI System

Lead Score: {lead.lead_score.score}/100 (HOT)
From: {lead.sender_name} <{lead.sender_email}>
Subject: {lead.subject}

Preview: {lead.preview[:200]}...

Keywords Matched: {', '.join(lead.lead_score.keywords_matched)}
Dispatch ID: {dispatch_id}

Action Required: Follow up within 1 hour for maximum conversion.
View in admin: http://localhost:8000/admin
        """.strip()
        
        # Log the notification
        log_message(
            direction="outbound",
            phone=self.owner_phone,
            body=message,
            channel="sales_intel_alert"
        )
        
        logger.info(f"Alert sent to {self.owner_email} for hot lead {dispatch_id}")


# API Endpoint for receiving leads from Sales Intelligence
def create_sales_intelligence_endpoint(app):
    """Add endpoint to FastAPI app for receiving Sales Intelligence leads"""
    from fastapi import APIRouter, Header
    
    router = APIRouter(prefix="/integrations", tags=["integrations"])
    connector = SalesIntelligenceConnector()
    
    @router.post("/sales-intelligence/lead")
    async def receive_sales_lead(
        lead_data: dict,
        x_api_key: str = Header(default=None)
    ):
        """
        Receive leads from Sales Intelligence System
        
        Your Make.com/Rube automation should POST hot leads here:
        
        POST /integrations/sales-intelligence/lead
        Headers: {"x-api-key": "your_dispatch_api_key"}
        Body: {
            "sender_name": "John Doe",
            "sender_email": "john@company.com",
            "subject": "AC repair needed",
            "preview": "My AC is not working...",
            "lead_score": {"score": 85, "urgency_level": "hot", ...}
        }
        """
        # Validate API key
        from config import DISPATCH_API_KEY
        if x_api_key != DISPATCH_API_KEY:
            return {"error": "Invalid API key"}, 401
        
        result = connector.receive_lead(lead_data)
        return result
    
    @router.get("/sales-intelligence/status")
    async def sales_intel_status():
        """Get Sales Intelligence integration status"""
        return {
            "status": "active",
            "hot_threshold": connector.hot_threshold,
            "warm_threshold": connector.warm_threshold,
            "owner": OWNER_INFO.get("name"),
            "capabilities": [
                "receive_leads",
                "score_leads",
                "create_dispatches",
                "notify_owner"
            ]
        }
    
    app.include_router(router)
    logger.info("Sales Intelligence integration endpoints registered")
    return router
