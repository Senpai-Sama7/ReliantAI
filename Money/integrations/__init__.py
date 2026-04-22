"""
ReliantAI Integrations Module

Connects the HVAC dispatch system with external services:
- Sales Intelligence System (Gmail scanner)
- HubSpot CRM
- Google Sheets
- Slack notifications
- Secure webhooks with HMAC verification
"""

from .sales_intelligence import (
    SalesIntelligenceConnector,
    LeadScorer,
    parse_sales_email,
    create_dispatch_from_sales_lead
)
from .hubspot_sync import HubSpotSync, HubSpotContact
from .google_sheets import GoogleSheetsLogger, MakeWebhookReceiver
from .slack_alerts import SlackNotifier, NotificationRouter
from .webhook_security import (
    WebhookVerifier,
    WebhookVerificationResult,
    MultiVerifier,
    verify_make_webhook,
    verify_hubspot_webhook,
    create_test_verifier
)

__all__ = [
    # Sales Intelligence
    "SalesIntelligenceConnector",
    "LeadScorer",
    "parse_sales_email",
    "create_dispatch_from_sales_lead",
    
    # HubSpot
    "HubSpotSync",
    "HubSpotContact",
    
    # Google Sheets
    "GoogleSheetsLogger",
    "MakeWebhookReceiver",
    
    # Slack
    "SlackNotifier",
    "NotificationRouter",
    
    # Webhook Security
    "WebhookVerifier",
    "WebhookVerificationResult",
    "MultiVerifier",
    "verify_make_webhook",
    "verify_hubspot_webhook",
    "create_test_verifier",
]
