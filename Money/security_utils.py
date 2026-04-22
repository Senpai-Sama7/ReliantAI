"""
Security utilities for Money API
SSRF protection, input validation, and security helpers
"""

import re
from urllib.parse import urlparse
from typing import Optional, Set

# Allowed URL schemes for external requests
ALLOWED_SCHEMES: Set[str] = {"https", "http"}

# Blocked host patterns (private IPs, internal networks)
BLOCKED_HOST_PATTERNS = [
    r"^127\.",  # Loopback
    r"^10\.",   # Private Class A
    r"^172\.(1[6-9]|2[0-9]|3[0-1])\.",  # Private Class B
    r"^192\.168\.",  # Private Class C
    r"^0\.",   # Current network
    r"^169\.254\.",  # Link-local
    r"^::1$",  # IPv6 loopback
    r"^fc00:",  # IPv6 private
    r"^fe80:",  # IPv6 link-local
    r"\.internal$",  # Internal domains
    r"\.local$",     # mDNS
    r"\.localhost$",  # Localhost variants
]

# Allowed external hosts (whitelist approach)
ALLOWED_EXTERNAL_HOSTS: Set[str] = {
    "api.claude.com",
    "api.anthropic.com",
    "hooks.zapier.com",
    "api.twilio.com",
    "api.openai.com",
    "api.github.com",
    "api.dropbox.com",
    "api.box.com",
    "api.google.com",
    "api.composio.dev",
    "api.langsmith.com",
    "api.crewai.com",
    # Add other approved external APIs here
}


def is_private_ip(host: str) -> bool:
    """Check if host is a private/internal IP address."""
    for pattern in BLOCKED_HOST_PATTERNS:
        if re.search(pattern, host, re.IGNORECASE):
            return True
    return False


def validate_external_url(url: str, allow_list: Optional[Set[str]] = None) -> bool:
    """
    Validate URL for safe external requests (SSRF protection)
    
    Args:
        url: URL to validate
        allow_list: Optional set of allowed hosts (overrides default)
        
    Returns:
        True if URL is safe for external requests
        
    Raises:
        ValueError: If URL is invalid or unsafe
    """
    allowed_hosts = allow_list or ALLOWED_EXTERNAL_HOSTS
    
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")
    
    # Check scheme
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"URL scheme '{parsed.scheme}' not allowed. Use http/https.")
    
    # Get hostname
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must have a hostname")
    
    # Normalize hostname
    hostname = hostname.lower().strip()
    
    # Check for private/internal IPs (SSRF protection)
    if is_private_ip(hostname):
        raise ValueError(f"URL hostname '{hostname}' resolves to private/internal network. SSRF protection triggered.")
    
    # Check port (block common internal ports)
    port = parsed.port
    if port and port in {22, 23, 25, 53, 110, 143, 3306, 5432, 6379, 27017, 9200}:
        raise ValueError(f"Port {port} is blocked for security reasons")
    
    # Check against allowlist
    if hostname not in allowed_hosts:
        # Check for subdomains of allowed hosts
        is_allowed = any(
            hostname == allowed or hostname.endswith(f".{allowed}")
            for allowed in allowed_hosts
        )
        if not is_allowed:
            raise ValueError(f"URL hostname '{hostname}' not in allowed external hosts list")
    
    return True


def safe_requests_get(url: str, **kwargs):
    """
    Safe wrapper for requests.get with SSRF protection
    
    Usage:
        response = safe_requests_get("https://api.example.com/data", timeout=5)
    """
    import requests
    
    validate_external_url(url)
    return requests.get(url, **kwargs)


def safe_requests_post(url: str, **kwargs):
    """
    Safe wrapper for requests.post with SSRF protection
    
    Usage:
        response = safe_requests_post("https://api.example.com/webhook", json=data, timeout=5)
    """
    import requests
    
    validate_external_url(url)
    return requests.post(url, **kwargs)


# Input validation helpers

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove any directory components
    filename = filename.replace("..", "_")
    filename = filename.replace("/", "_")
    filename = filename.replace("\\", "_")
    
    # Remove null bytes
    filename = filename.replace("\x00", "")
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:250] + "." + ext if ext else filename[:255]
    
    return filename


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format (E.164)."""
    # Remove common formatting characters
    cleaned = re.sub(r"[\s\-\.\(\)]", "", phone)
    
    # E.164 format: + followed by 10-15 digits
    pattern = r"^\+[1-9]\d{9,14}$"
    return bool(re.match(pattern, cleaned))


def sanitize_log_message(message: str) -> str:
    """Sanitize message for safe logging (prevent log injection)."""
    # Remove newlines to prevent log injection
    message = message.replace("\n", " ").replace("\r", " ")
    
    # Limit length
    if len(message) > 1000:
        message = message[:997] + "..."
    
    return message


# Security headers helper
def get_security_headers() -> dict:
    """Get recommended security headers for API responses."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
