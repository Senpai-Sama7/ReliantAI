"""
Slack Integration
Real-time alerts for high-value leads and system events
"""

import os
import requests
from typing import Optional, Dict
from datetime import datetime

from config import setup_logging

logger = setup_logging("slack_alerts")


class SlackNotifier:
    """
    Sends real-time alerts to Slack channels
    Notifies your team when hot leads come in
    """
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
        
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not set - Slack alerts disabled")
    
    def send_hot_lead_alert(self, lead: Dict, score: int) -> Dict:
        """Send alert for high-value leads (score 70+)"""
        if not self.webhook_url:
            return {"status": "disabled"}
        
        color = "#FF0000" if score >= 90 else "#FFA500" if score >= 80 else "#FFD700"
        
        message = {
            "text": f"🔥 Hot Lead Detected (Score: {score})",
            "attachments": [
                {
                    "color": color,
                    "fields": [
                        {
                            "title": "Sender",
                            "value": lead.get("sender_name", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Email",
                            "value": lead.get("sender_email", "N/A"),
                            "short": True
                        },
                        {
                            "title": "Subject",
                            "value": lead.get("subject", "N/A"),
                            "short": False
                        },
                        {
                            "title": "Dispatch ID",
                            "value": lead.get("dispatch_id", "Pending..."),
                            "short": True
                        },
                        {
                            "title": "Status",
                            "value": lead.get("dispatch_status", "🆕 New"),
                            "short": True
                        }
                    ],
                    "footer": "ReliantAI Sales Intelligence",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        return self._send(message)
    
    def send_cold_escalation_alert(self, lead: Dict) -> Dict:
        """Alert when a cold lead converts to a hot lead"""
        if not self.webhook_url:
            return {"status": "disabled"}
        
        message = {
            "text": "⚠️ Cold Lead Escalated!",
            "attachments": [
                {
                    "color": "#FF6B35",
                    "text": f"Lead previously marked cold is now showing activity:\n\n{lead.get('preview', '')[:200]}",
                    "fields": [
                        {
                            "title": "Previous Status",
                            "value": "❄️ Cold",
                            "short": True
                        },
                        {
                            "title": "Current Status",
                            "value": f"🔥 Hot (Score: {lead.get('lead_score', {}).get('score', 0)})",
                            "short": True
                        }
                    ],
                    "footer": "ReliantAI Sales Intelligence"
                }
            ]
        }
        
        return self._send(message)
    
    def send_system_alert(self, title: str, message: str, level: str = "info") -> Dict:
        """Send system health/status alerts"""
        if not self.webhook_url:
            return {"status": "disabled"}
        
        colors = {
            "info": "#36A2F1",
            "warning": "#FFCC00",
            "error": "#FF4444",
            "success": "#36A64F"
        }
        
        payload = {
            "attachments": [
                {
                    "color": colors.get(level, colors["info"]),
                    "title": title,
                    "text": message,
                    "footer": "ReliantAI System",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        return self._send(payload)
    
    def _send(self, payload: Dict) -> Dict:
        """Internal method to send Slack message"""
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info("Slack alert sent successfully")
            return {"status": "sent"}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Slack alert failed: {e}")
            return {"status": "error", "error": str(e)}


class NotificationRouter:
    """
    Routes notifications based on lead score and type
    Your Sales Intelligence System sends different alerts for different scenarios
    """
    
    def __init__(self):
        self.slack = SlackNotifier()
    
    def route_lead_notification(self, lead: Dict):
        """
        Route lead notifications based on score:
        - 90+: Immediate Slack alert + SMS
        - 80-89: Slack alert
        - 70-79: Log only (check dashboard)
        - <70: Cold lead tracking
        """
        score = lead.get("lead_score", {}).get("score", 0)
        
        if score >= 90:
            # Critical: Both Slack and SMS
            self.slack.send_hot_lead_alert(lead, score)
            # SMS notification would go here
            
        elif score >= 80:
            # High priority: Slack only
            self.slack.send_hot_lead_alert(lead, score)
            
        elif score >= 70:
            # Standard hot lead
            self.slack.send_hot_lead_alert(lead, score)
            
        else:
            # Cold lead - track but don't alert
            logger.info(f"Cold lead logged: {lead.get('sender_email')}")
    
    def send_dispatch_created_alert(self, dispatch_id: str, customer: str, urgency: str):
        """Notify when a new dispatch is created"""
        urgency_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(urgency, "⚪")
        
        self.slack.send_system_alert(
            title=f"{urgency_emoji} New Dispatch Created",
            message=f"Dispatch **{dispatch_id}** for *{customer}*\nUrgency: {urgency.upper()}",
            level="success" if urgency == "low" else "info"
        )
