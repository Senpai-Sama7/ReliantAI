"""
HubSpot CRM Integration
Syncs leads between ReliantAI and HubSpot
Ensures both Sales Intelligence and ReliantAI systems stay in sync
"""

import os
import requests
from typing import Optional, Dict, List
from dataclasses import dataclass

from config import setup_logging, OWNER_INFO

logger = setup_logging("hubspot_sync")


@dataclass
class HubSpotContact:
    """HubSpot contact data structure"""
    email: str
    firstname: str
    lastname: str
    phone: Optional[str] = None
    company: Optional[str] = None
    lifecycle_stage: str = "marketingqualifiedlead"
    lead_source: Optional[str] = None
    hs_lead_status: Optional[str] = None


class HubSpotSync:
    """
    Syncs contacts between ReliantAI and HubSpot CRM
    
    Your Sales Intelligence System already creates contacts in HubSpot.
    This module ensures ReliantAI updates those contacts with dispatch info.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("HUBSPOT_API_KEY")
        self.base_url = "https://api.hubapi.com"
        
        if not self.api_key:
            logger.warning("HUBSPOT_API_KEY not set - HubSpot sync disabled")
    
    def create_or_update_contact(self, contact: HubSpotContact) -> Dict:
        """Create or update a contact in HubSpot"""
        if not self.api_key:
            return {"error": "HubSpot API key not configured"}
        
        url = f"{self.base_url}/contacts/v1/contact/createOrUpdate/email/{contact.email}"
        
        data = {
            "properties": [
                {"property": "email", "value": contact.email},
                {"property": "firstname", "value": contact.firstname},
                {"property": "lastname", "value": contact.lastname},
                {"property": "lifecyclestage", "value": contact.lifecycle_stage},
                {"property": "lead_source", "value": contact.lead_source or "ReliantAI"},
            ]
        }
        
        if contact.phone:
            data["properties"].append({"property": "phone", "value": contact.phone})
        if contact.company:
            data["properties"].append({"property": "company", "value": contact.company})
        if contact.hs_lead_status:
            data["properties"].append({"property": "hs_lead_status", "value": contact.hs_lead_status})
        
        try:
            response = requests.post(
                url,
                json=data,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"HubSpot contact synced: {contact.email}")
            return {"status": "success", "contact_id": response.json().get("vid")}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HubSpot sync failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def update_contact_lifecycle(self, email: str, stage: str) -> Dict:
        """Update a contact's lifecycle stage"""
        if not self.api_key:
            return {"error": "HubSpot API key not configured"}
        
        url = f"{self.base_url}/contacts/v1/contact/email/{email}/profile"
        
        data = {
            "properties": [
                {"property": "lifecyclestage", "value": stage}
            ]
        }
        
        try:
            response = requests.post(
                url,
                json=data,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"HubSpot lifecycle updated: {email} → {stage}")
            return {"status": "success"}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HubSpot update failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_contact_by_email(self, email: str) -> Optional[Dict]:
        """Retrieve a contact from HubSpot by email"""
        if not self.api_key:
            return None
        
        url = f"{self.base_url}/contacts/v1/contact/email/{email}/profile"
        
        try:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"HubSpot lookup failed: {e}")
            return None
    
    def create_note(self, contact_id: str, note: str) -> Dict:
        """Add a note to a contact's timeline"""
        if not self.api_key:
            return {"error": "HubSpot API key not configured"}
        
        url = f"{self.base_url}/engagements/v1/engagements"
        
        data = {
            "engagement": {
                "type": "NOTE",
                "timestamp": int(datetime.now().timestamp() * 1000)
            },
            "associations": {
                "contactIds": [contact_id]
            },
            "metadata": {
                "body": note
            }
        }
        
        try:
            response = requests.post(
                url,
                json=data,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"HubSpot note added to contact {contact_id}")
            return {"status": "success", "engagement_id": response.json().get("engagement", {}).get("id")}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HubSpot note creation failed: {e}")
            return {"status": "error", "error": str(e)}
