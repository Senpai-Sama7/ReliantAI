"""
ComplianceOne Client - Integration module for the ReliantAI platform
Real, working client for compliance management
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

import requests

class ComplianceOneClient:
    """Client for interacting with ComplianceOne service"""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or os.environ.get("COMPLIANCEONE_URL", "http://localhost:8001")
        self.api_key = api_key or os.environ.get("COMPLIANCEONE_API_KEY", "")
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.json()
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}
    
    def create_framework(self, name: str, description: str, version: str = "1.0") -> Dict:
        """Create a compliance framework (e.g., SOC2, GDPR, HIPAA)"""
        data = {"name": name, "description": description, "version": version}
        response = requests.post(
            f"{self.base_url}/frameworks",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def list_frameworks(self) -> List[Dict]:
        """List all compliance frameworks"""
        response = requests.get(f"{self.base_url}/frameworks", headers=self.headers)
        response.raise_for_status()
        return response.json().get("frameworks", [])
    
    def create_control(self, framework_id: int, control_id: str, title: str, 
                       description: str, category: str, severity: str = "medium") -> Dict:
        """Create a compliance control"""
        data = {
            "framework_id": framework_id,
            "control_id": control_id,
            "title": title,
            "description": description,
            "category": category,
            "severity": severity
        }
        response = requests.post(
            f"{self.base_url}/controls",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def list_controls(self, framework_id: int) -> List[Dict]:
        """List controls for a framework"""
        response = requests.get(
            f"{self.base_url}/frameworks/{framework_id}/controls",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json().get("controls", [])
    
    def create_audit(self, framework_id: int, auditor: str) -> Dict:
        """Start a compliance audit"""
        data = {"framework_id": framework_id, "auditor": auditor}
        response = requests.post(
            f"{self.base_url}/audits",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def list_audits(self) -> List[Dict]:
        """List all audits"""
        response = requests.get(f"{self.base_url}/audits", headers=self.headers)
        response.raise_for_status()
        return response.json().get("audits", [])
    
    def complete_audit(self, audit_id: str, score: int, findings: Dict) -> Dict:
        """Complete an audit with findings"""
        response = requests.post(
            f"{self.base_url}/audits/{audit_id}/complete",
            params={"score": score},
            json=findings,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def submit_evidence(self, control_id: int, evidence_type: str, metadata: Dict) -> Dict:
        """Submit compliance evidence"""
        data = {
            "control_id": control_id,
            "evidence_type": evidence_type,
            "metadata": metadata
        }
        response = requests.post(
            f"{self.base_url}/evidence",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def report_violation(self, control_id: int, severity: str, description: str) -> Dict:
        """Report a compliance violation"""
        data = {
            "control_id": control_id,
            "severity": severity,
            "description": description
        }
        response = requests.post(
            f"{self.base_url}/violations",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def list_violations(self, status: Optional[str] = None) -> List[Dict]:
        """List compliance violations"""
        params = {}
        if status:
            params["status"] = status
        response = requests.get(
            f"{self.base_url}/violations",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json().get("violations", [])
    
    def get_dashboard(self) -> Dict:
        """Get compliance dashboard data"""
        response = requests.get(f"{self.base_url}/dashboard", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def setup_soc2_framework(self) -> Dict:
        """Helper to set up SOC2 compliance framework with common controls"""
        # Create framework
        framework = self.create_framework(
            "SOC2",
            "Service Organization Control 2 - Security, Availability, Processing Integrity",
            "2024"
        )
        framework_id = framework["id"]
        
        # Add common SOC2 controls
        controls = [
            ("CC6.1", "Logical Access Security", "Access controls are implemented", "Security", "high"),
            ("CC6.2", "Access Removal", "Access is removed upon termination", "Security", "high"),
            ("CC7.1", "Security Monitoring", "System monitoring is implemented", "Security", "high"),
            ("CC7.2", "Vulnerability Management", "Vulnerabilities are identified and remediated", "Security", "medium"),
            ("A1.1", "System Availability", "Systems are available for operation", "Availability", "high"),
            ("A1.2", "System Recovery", "Recovery procedures exist and are tested", "Availability", "high"),
        ]
        
        for control_id, title, description, category, severity in controls:
            self.create_control(framework_id, control_id, title, description, category, severity)
        
        return {"framework_id": framework_id, "controls_created": len(controls)}
    
    def setup_gdpr_framework(self) -> Dict:
        """Helper to set up GDPR compliance framework"""
        framework = self.create_framework(
            "GDPR",
            "General Data Protection Regulation - EU Data Protection",
            "2024"
        )
        framework_id = framework["id"]
        
        controls = [
            ("Art.5", "Data Processing Principles", "Lawful, fair, and transparent processing", "Principles", "critical"),
            ("Art.6", "Lawfulness of Processing", "Processing has valid legal basis", "Legal Basis", "critical"),
            ("Art.15", "Right of Access", "Data subjects can access their data", "Data Rights", "high"),
            ("Art.17", "Right to Erasure", "Data subjects can request deletion", "Data Rights", "high"),
            ("Art.25", "Data Protection by Design", "Privacy by design implemented", "Design", "high"),
            ("Art.32", "Security of Processing", "Appropriate security measures", "Security", "critical"),
        ]
        
        for control_id, title, description, category, severity in controls:
            self.create_control(framework_id, control_id, title, description, category, severity)
        
        return {"framework_id": framework_id, "controls_created": len(controls)}


# Convenience function for platform integration
def get_compliance_client() -> ComplianceOneClient:
    """Get configured ComplianceOne client"""
    return ComplianceOneClient()
