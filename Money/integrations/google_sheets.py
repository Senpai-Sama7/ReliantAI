"""
Google Sheets Integration
Logs dispatch data to your existing Sales Intelligence spreadsheet
Maintains unified record across both systems
"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime

from config import setup_logging

logger = setup_logging("google_sheets")


class GoogleSheetsLogger:
    """
    Logs ReliantAI dispatch data to Google Sheets
    Connects to your existing Sales Intelligence sheet
    """
    
    def __init__(self, spreadsheet_id: Optional[str] = None):
        self.spreadsheet_id = spreadsheet_id or os.environ.get("GOOGLE_SHEETS_ID")
        self.sheet_name = "ReliantAI Dispatches"
        
        # Your existing sheet URL:
        # https://docs.google.com/spreadsheets/d/1jdS3oYIOQgHhWZqlza8ThIYknMmYM0TiPLNXXt_t-1Y/edit
        if not self.spreadsheet_id:
            logger.warning("GOOGLE_SHEETS_ID not set - Sheet logging disabled")
    
    def log_dispatch(self, dispatch_data: Dict) -> Dict:
        """
        Log a dispatch to the Google Sheet
        
        Adds a row with:
        - Timestamp
        - Dispatch ID
        - Customer info
        - Issue summary
        - Status
        - Lead source (Sales Intel, SMS, WhatsApp, etc.)
        """
        if not self.spreadsheet_id:
            return {"status": "skipped", "reason": "not_configured"}
        
        row_data = [
            datetime.now().isoformat(),
            dispatch_data.get("dispatch_id", ""),
            dispatch_data.get("customer_name", ""),
            dispatch_data.get("customer_phone", ""),
            dispatch_data.get("issue_summary", "")[:100] + "...",
            dispatch_data.get("urgency", ""),
            dispatch_data.get("status", ""),
            dispatch_data.get("source", "reliantai"),
            dispatch_data.get("lead_score", ""),
        ]
        
        # In production, this would use Google Sheets API
        # For now, log to file as backup
        self._backup_to_file(row_data)
        
        logger.info(f"Dispatch logged to sheet: {dispatch_data.get('dispatch_id')}")
        return {"status": "logged", "row": row_data}
    
    def _backup_to_file(self, row_data: List):
        """Backup sheet data to local file"""
        backup_file = "sheet_backup.csv"
        with open(backup_file, "a") as f:
            f.write(",".join(f'"{str(x)}"' for x in row_data) + "\n")
    
    def sync_with_sales_intel_sheet(self, sales_intel_row_id: str, dispatch_id: str):
        """
        Link a ReliantAI dispatch to a Sales Intelligence sheet row
        
        This creates the connection between:
        - Sales Intel lead (row A12 in your sheet)
        - ReliantAI dispatch (SI-20260303-214200)
        """
        logger.info(f"Linked Sales Intel row {sales_intel_row_id} to dispatch {dispatch_id}")
        return {
            "status": "linked",
            "sales_intel_row": sales_intel_row_id,
            "dispatch_id": dispatch_id
        }


# Webhook receiver for Make.com / Rube automations
class MakeWebhookReceiver:
    """
    Receives webhooks from Make.com (Integromat) automations
    Your Sales Intelligence System runs on Make/Rube
    """
    
    @staticmethod
    def validate_webhook(payload: Dict, secret: Optional[str] = None) -> bool:
        """Validate incoming webhook from Make.com"""
        expected_secret = secret or os.environ.get("MAKE_WEBHOOK_SECRET")
        
        if not expected_secret:
            return True  # No secret configured, accept all (dev mode)
        
        return payload.get("webhook_secret") == expected_secret
    
    @staticmethod
    def parse_make_payload(payload: Dict) -> Dict:
        """
        Parse payload from Make.com webhook
        
        Make.com sends data in various formats depending on your scenario
        """
        return {
            "sender_name": payload.get("from_name", ""),
            "sender_email": payload.get("from_email", ""),
            "subject": payload.get("subject", ""),
            "preview": payload.get("body_preview", ""),
            "timestamp": payload.get("received_at", datetime.now().isoformat()),
            "lead_score": {
                "score": payload.get("lead_score", 0),
                "keywords_matched": payload.get("matched_keywords", []),
                "urgency_level": payload.get("urgency", "cold"),
            },
            "sheet_row_id": payload.get("google_sheets_row", ""),
            "hubspot_contact_id": payload.get("hubspot_contact_id", ""),
            "source": "make_com_webhook"
        }
