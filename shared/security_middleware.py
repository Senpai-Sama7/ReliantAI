"""
ReliantAI Platform - Security Middleware
Shared security utilities for all services
"""

import os
import re
import logging
from typing import Optional, Dict, List
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import secrets
import hashlib
import time
try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None
from datetime import datetime, timedelta

# Configure structured logging
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy (Production-grade)
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "  # Added ws support for dashboard
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests;"
        )
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS (HTTPS only)
        if os.getenv('ENVIRONMENT') in ['staging', 'production']:
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )
        
        # Permissions Policy
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()'
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed sliding window rate limiting middleware with in-memory fallback"""

    def __init__(self, app, requests_per_minute: int = 60,
                 redis_url: Optional[str] = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._redis_url = redis_url or os.getenv("REDIS_URL")
        self._redis = None
        self._local: Dict[str, List[float]] = {}
        self._local_max_ips = 10_000
        self.logger = logging.getLogger('rate_limit')

    async def _get_redis(self):
        if self._redis is None and self._redis_url and aioredis:
            try:
                self._redis = aioredis.from_url(
                    self._redis_url, decode_responses=True
                )
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    async def _check_redis(self, ip: str, now: float) -> bool:
        r = await self._get_redis()
        if r is None:
            return False
        try:
            key = f"rl:{ip}"
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, now - 60)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, 120)
            results = await pipe.execute()
            return results[2] > self.requests_per_minute
        except Exception as e:
            self.logger.warning(f"Redis rate limit error: {e}")
            return False

    def _check_local(self, ip: str, now: float) -> bool:
        window_start = now - 60
        if len(self._local) > self._local_max_ips:
            self._local = {
                k: v for k, v in self._local.items()
                if any(t > window_start for t in v)
            }
        bucket = self._local.setdefault(ip, [])
        self._local[ip] = [t for t in bucket if t > window_start]
        self._local[ip].append(now)
        return len(self._local[ip]) > self.requests_per_minute

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ['/health', '/nginx-health']:
            return await call_next(request)

        client_ip = request.client.host if request.client else 'unknown'
        now = time.time()

        # Try Redis first, fall back to in-memory
        rate_exceeded = await self._check_redis(client_ip, now)
        if not rate_exceeded:
            rate_exceeded = self._check_local(client_ip, now)

        if rate_exceeded:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Rate limit exceeded", "retry_after": 60}
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers['X-RateLimit-Limit'] = str(self.requests_per_minute)

        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Input validation and sanitization middleware"""
    
    # SQL injection patterns
    SQL_PATTERNS = [
        r'(\%27)|(\')|(\-\-)|(\%23)|(#)',
        r'((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))',
        r'\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))',
        r'((\%27)|(\'))union',
        r'exec(\s|\+)+(s|x)p\w+',
        r'UNION\s+SELECT',
        r'INSERT\s+INTO',
        r'DELETE\s+FROM',
        r'DROP\s+TABLE',
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?<\/script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe',
        r'<object',
        r'<embed',
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip validation for health checks
        if request.url.path in ['/health', '/nginx-health']:
            return await call_next(request)
        
        # Check query parameters
        for key, value in request.query_params.items():
            if self._is_suspicious(str(value)):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid input detected"}
                )
        
        return await call_next(request)
    
    def _is_suspicious(self, value: str) -> bool:
        """Check if input contains suspicious patterns"""
        value_lower = value.lower()
        
        # Check SQL injection patterns
        for pattern in self.SQL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        # Check XSS patterns
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Audit logging middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.enabled = os.getenv('AUDIT_LOG_ENABLED', 'false').lower() == 'true'
    
    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)
            
        start_time = time.time()
        
        # Log request
        audit_logger.info({
            "event": "request",
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else 'unknown',
            "user_agent": request.headers.get('user-agent', 'unknown')
        })
        
        response = await call_next(request)
        
        # Log response
        duration = time.time() - start_time
        audit_logger.info({
            "event": "response",
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "path": request.url.path
        })
        
        return response


def create_cors_middleware(app):
    """Apply CORS middleware to a FastAPI/Starlette app with fail-closed defaults.
    
    Requires CORS_ORIGINS environment variable to be set.
    Rejects wildcard '*' when used with allow_credentials=True.
    """
    
    # SECURITY FIX: Require explicit CORS_ORIGINS — no default wildcard.
    _cors_origins_raw = os.getenv("CORS_ORIGINS", "")
    if not _cors_origins_raw:
        raise RuntimeError(
            "CORS_ORIGINS environment variable is required. "
            "Set it to a comma-separated list of allowed origins. "
            "Do NOT use wildcard * or leave unset in production."
        )
    allowed_origins = [
        origin.strip() for origin in _cors_origins_raw.split(",") if origin.strip()
    ]
    if "*" in allowed_origins:
        raise RuntimeError(
            "CORS_ORIGINS contains wildcard '*' which is not allowed with allow_credentials=True. "
            "Specify explicit origins."
        )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "X-API-Key",
            "X-Request-ID",
            "Content-Type",
            "Authorization"
        ],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
        max_age=3600,
    )


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure token"""
    return secrets.token_urlsafe(length)


def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging"""
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def sanitize_log_message(message: str) -> str:
    """Sanitize message for logging (remove sensitive data)"""
    # Remove API keys
    message = re.sub(r'api[_-]?key[=:]\s*\S+', 'api_key=***', message, flags=re.IGNORECASE)
    # Remove tokens
    message = re.sub(r'token[=:]\s*\S+', 'token=***', message, flags=re.IGNORECASE)
    # Remove passwords
    message = re.sub(r'password[=:]\s*\S+', 'password=***', message, flags=re.IGNORECASE)
    # Remove secrets
    message = re.sub(r'secret[=:]\s*\S+', 'secret=***', message, flags=re.IGNORECASE)
    
    return message


# Security utilities for FastAPI dependency injection
async def verify_api_key(request: Request):
    """Verify API key from request headers"""
    api_key = request.headers.get('X-API-Key')
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Get expected API key from environment
    service_name = request.url.path.split('/')[1] if request.url.path else 'default'
    expected_key = os.getenv(f'{service_name.upper()}_API_KEY') or os.getenv('API_KEY')
    
    # HIGH-2 fix: Fail closed if no expected key is configured
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service authentication not configured"
        )
    
    # Use constant-time comparison to prevent timing attacks (bytes path)
    if not secrets.compare_digest(
        api_key.encode("utf-8"),
        expected_key.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


async def get_client_info(request: Request) -> dict:
    """Get client information for logging/analytics"""
    return {
        "ip": request.client.host if request.client else 'unknown',
        "user_agent": request.headers.get('user-agent', 'unknown'),
        "referer": request.headers.get('referer', 'none'),
    }
