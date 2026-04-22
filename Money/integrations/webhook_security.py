"""
HMAC-SHA256 Webhook Security
Production-grade webhook signature verification with timestamp skew enforcement.

Based on Citadel's proven pattern, adapted for ReliantAI HVAC.
Prevents replay attacks and signature timing attacks.
"""

import hmac
import hashlib
import time
import json
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

from config import setup_logging

logger = setup_logging("webhook_security")


@dataclass
class WebhookVerificationResult:
    """Result of webhook signature verification"""
    valid: bool
    error: Optional[str] = None
    timestamp: Optional[int] = None
    skew_seconds: Optional[int] = None


class WebhookVerifier:
    """
    Verifies webhook signatures using HMAC-SHA256.
    
    Expected header format:
        X-Webhook-Timestamp: 1708800000
        X-Webhook-Signature: sha256=<hex_hmac>
    
    HMAC computation: HMAC_SHA256(secret, "{timestamp}.{raw_body}")
    """
    
    def __init__(self, secret: str, max_skew_seconds: int = 300):
        """
        Initialize verifier.
        
        Args:
            secret: The webhook signing secret
            max_skew_seconds: Maximum allowed timestamp skew (default 5 minutes)
        """
        if not secret or len(secret) < 16:
            raise ValueError("Webhook secret must be at least 16 characters")
        self.secret = secret
        self.max_skew = max_skew_seconds
    
    def verify(
        self,
        raw_body: bytes,
        timestamp_header: str,
        signature_header: str
    ) -> WebhookVerificationResult:
        """
        Verify webhook signature.
        
        Args:
            raw_body: Raw request body bytes
            timestamp_header: X-Webhook-Timestamp value
            signature_header: X-Webhook-Signature value (format: sha256=<hex>)
            
        Returns:
            WebhookVerificationResult with valid=True/False and error details
        """
        # Parse timestamp
        try:
            ts = int(timestamp_header)
        except (ValueError, TypeError):
            logger.warning(f"Invalid timestamp header: {timestamp_header}")
            return WebhookVerificationResult(
                valid=False,
                error="Invalid timestamp format"
            )
        
        # Check timestamp skew (prevent replay attacks)
        now = int(time.time())
        skew = abs(now - ts)
        if skew > self.max_skew:
            logger.warning(
                f"Timestamp skew exceeded: {skew}s (max: {self.max_skew}s). "
                f"Timestamp: {ts}, Now: {now}"
            )
            return WebhookVerificationResult(
                valid=False,
                error=f"Timestamp skew exceeded ({skew}s > {self.max_skew}s)",
                timestamp=ts,
                skew_seconds=skew
            )
        
        # Validate signature format
        if not signature_header or not signature_header.startswith("sha256="):
            logger.warning(f"Invalid signature format: {signature_header}")
            return WebhookVerificationResult(
                valid=False,
                error="Invalid signature format (expected sha256=<hex>)",
                timestamp=ts
            )
        
        # Extract sent signature
        try:
            sent_sig = signature_header.split("=", 1)[1].strip().lower()
        except IndexError:
            return WebhookVerificationResult(
                valid=False,
                error="Invalid signature format (missing =)",
                timestamp=ts
            )
        
        # Compute expected signature
        message = f"{ts}.".encode("utf-8") + raw_body
        expected_sig = hmac.new(
            self.secret.encode("utf-8"),
            message,
            hashlib.sha256
        ).hexdigest().lower()
        
        # Constant-time comparison (prevent timing attacks)
        if not hmac.compare_digest(sent_sig, expected_sig):
            logger.warning("Signature mismatch")
            return WebhookVerificationResult(
                valid=False,
                error="Signature mismatch",
                timestamp=ts,
                skew_seconds=skew
            )
        
        logger.info(f"Webhook verified successfully (skew: {skew}s)")
        return WebhookVerificationResult(
            valid=True,
            timestamp=ts,
            skew_seconds=skew
        )
    
    def sign(
        self,
        payload: Dict,
        timestamp: Optional[int] = None
    ) -> Tuple[bytes, Dict[str, str]]:
        """
        Sign a webhook payload.
        
        Args:
            payload: Dictionary to sign
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            Tuple of (raw_body_bytes, headers_dict)
        """
        # Serialize payload with consistent format
        raw_body = json.dumps(
            payload,
            separators=(",", ":"),
            sort_keys=True,
            ensure_ascii=False
        ).encode("utf-8")
        
        # Use provided timestamp or current time
        ts = timestamp or int(time.time())
        
        # Compute signature
        message = f"{ts}.".encode("utf-8") + raw_body
        sig = hmac.new(
            self.secret.encode("utf-8"),
            message,
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "X-Webhook-Timestamp": str(ts),
            "X-Webhook-Signature": f"sha256={sig}",
            "Content-Type": "application/json"
        }
        
        return raw_body, headers


class MultiVerifier:
    """
    Multiple webhook verifiers for different sources.
    Supports Make.com, HubSpot, and custom sources.
    """
    
    def __init__(self):
        self.verifiers: Dict[str, WebhookVerifier] = {}
    
    def register(self, source: str, secret: str, max_skew: int = 300) -> None:
        """Register a verifier for a source"""
        self.verifiers[source] = WebhookVerifier(secret, max_skew)
        logger.info(f"Registered webhook verifier for source: {source}")
    
    def verify(
        self,
        source: str,
        raw_body: bytes,
        timestamp_header: str,
        signature_header: str
    ) -> WebhookVerificationResult:
        """Verify webhook from a specific source"""
        if source not in self.verifiers:
            return WebhookVerificationResult(
                valid=False,
                error=f"Unknown webhook source: {source}"
            )
        return self.verifiers[source].verify(
            raw_body, timestamp_header, signature_header
        )
    
    def sign(self, source: str, payload: Dict) -> Tuple[bytes, Dict[str, str]]:
        """Sign payload for a specific source"""
        if source not in self.verifiers:
            raise ValueError(f"Unknown webhook source: {source}")
        return self.verifiers[source].sign(payload)


# Convenience functions for common use cases
def verify_make_webhook(
    raw_body: bytes,
    timestamp_header: str,
    signature_header: str,
    secret: str
) -> WebhookVerificationResult:
    """Verify Make.com (Integromat) webhook"""
    verifier = WebhookVerifier(secret)
    return verifier.verify(raw_body, timestamp_header, signature_header)


def verify_hubspot_webhook(
    raw_body: bytes,
    timestamp_header: str,
    signature_header: str,
    secret: str
) -> WebhookVerificationResult:
    """Verify HubSpot webhook"""
    verifier = WebhookVerifier(secret, max_skew_seconds=600)
    return verifier.verify(raw_body, timestamp_header, signature_header)


def create_test_verifier(secret: str = "test-secret-1234567890") -> WebhookVerifier:
    """Create a test verifier for unit tests"""
    return WebhookVerifier(secret, max_skew_seconds=3600)
