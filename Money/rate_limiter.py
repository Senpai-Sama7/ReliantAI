"""
Sliding Window Rate Limiter
Production-grade rate limiting per IP/phone with thread safety.

Based on Citadel's proven pattern, enhanced for HVAC dispatch:
- Per-phone SMS rate limiting
- Per-IP API rate limiting  
- Sliding window (not fixed) for smoother limits
- Thread-safe with proper locking
"""

from __future__ import annotations

import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum

from config import setup_logging

logger = setup_logging("rate_limiter")


class RateLimitScope(str, Enum):
    """Rate limit scopes"""
    SMS = "sms"
    WHATSAPP = "whatsapp"
    API = "api"
    WEBHOOK = "webhook"


@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    current_count: int
    limit: int
    window_seconds: int
    retry_after: Optional[int] = None  # Seconds until next allowed request
    
    @property
    def remaining(self) -> int:
        """Remaining requests in window"""
        return max(0, self.limit - self.current_count)
    
    @property
    def is_limited(self) -> bool:
        """True if rate limited"""
        return not self.allowed


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding window rate limiter.
    
    Tracks requests per key (IP, phone number) within a time window.
    Automatically prunes old entries to prevent memory growth.
    
    Usage:
        limiter = SlidingWindowRateLimiter()
        
        # Check if request allowed
        result = limiter.check("+15551234567", scope="sms", limit=5)
        if not result.allowed:
            raise RateLimitExceeded()
    """
    
    def __init__(
        self,
        default_limit: int = 60,
        window_seconds: int = 60,
        cleanup_interval: int = 100
    ):
        """
        Initialize rate limiter.
        
        Args:
            default_limit: Default max requests per window
            window_seconds: Time window in seconds
            cleanup_interval: Clean up stale entries every N checks
        """
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.cleanup_interval = cleanup_interval
        
        # Buckets: {(key, scope): [timestamps]}
        self._buckets: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._check_counter = 0
    
    def check(
        self,
        key: str,
        scope: str = "default",
        limit: Optional[int] = None
    ) -> RateLimitResult:
        """
        Check if request is within rate limit.
        
        Args:
            key: Identifier (IP address, phone number)
            scope: Rate limit scope (sms, api, etc.)
            limit: Override default limit for this check
            
        Returns:
            RateLimitResult with allowed=True/False and details
        """
        limit = limit or self.default_limit
        now = time.time()
        cutoff = now - self.window_seconds
        bucket_key = (key, scope)
        
        with self._lock:
            self._check_counter += 1
            
            # Prune old entries
            bucket = self._buckets[bucket_key]
            self._buckets[bucket_key] = [t for t in bucket if t > cutoff]
            
            # Check limit
            current_count = len(self._buckets[bucket_key])
            
            if current_count >= limit:
                # Rate limited - calculate retry after
                oldest = min(self._buckets[bucket_key]) if self._buckets[bucket_key] else now
                retry_after = int(oldest + self.window_seconds - now)
                
                logger.warning(
                    f"Rate limit exceeded: {key} ({scope}) - "
                    f"{current_count}/{limit} in {self.window_seconds}s"
                )
                
                return RateLimitResult(
                    allowed=False,
                    current_count=current_count,
                    limit=limit,
                    window_seconds=self.window_seconds,
                    retry_after=max(1, retry_after)
                )
            
            # Allow request - record timestamp
            self._buckets[bucket_key].append(now)
            
            # Periodic cleanup of empty buckets
            if self._check_counter % self.cleanup_interval == 0:
                self._cleanup_empty_buckets()
            
            return RateLimitResult(
                allowed=True,
                current_count=current_count + 1,
                limit=limit,
                window_seconds=self.window_seconds,
                retry_after=None
            )
    
    def _cleanup_empty_buckets(self) -> None:
        """Remove empty buckets to prevent memory growth"""
        now = time.time()
        cutoff = now - self.window_seconds
        
        empty_keys = [
            k for k, timestamps in self._buckets.items()
            if not timestamps or all(t <= cutoff for t in timestamps)
        ]
        
        for k in empty_keys:
            del self._buckets[k]
        
        if empty_keys:
            logger.debug(f"Cleaned up {len(empty_keys)} empty rate limit buckets")
    
    def get_status(self, key: str, scope: str = "default") -> RateLimitResult:
        """Get current rate limit status without incrementing"""
        now = time.time()
        cutoff = now - self.window_seconds
        bucket_key = (key, scope)
        
        with self._lock:
            bucket = self._buckets.get(bucket_key, [])
            valid_timestamps = [t for t in bucket if t > cutoff]
            current_count = len(valid_timestamps)
            
            return RateLimitResult(
                allowed=current_count < self.default_limit,
                current_count=current_count,
                limit=self.default_limit,
                window_seconds=self.window_seconds,
                retry_after=None
            )
    
    def reset(self, key: Optional[str] = None, scope: Optional[str] = None) -> None:
        """Reset rate limit for a key/scope (for testing/emergencies)"""
        with self._lock:
            if key is None:
                # Clear all
                self._buckets.clear()
                logger.info("All rate limits reset")
            elif scope is None:
                # Clear all scopes for key
                keys_to_delete = [k for k in self._buckets if k[0] == key]
                for k in keys_to_delete:
                    del self._buckets[k]
                logger.info(f"Rate limits reset for {key}")
            else:
                # Clear specific key+scope
                bucket_key = (key, scope)
                if bucket_key in self._buckets:
                    del self._buckets[bucket_key]
                    logger.info(f"Rate limit reset for {key} ({scope})")


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(message)


# Global rate limiter instance
_rate_limiter: Optional[SlidingWindowRateLimiter] = None


def get_rate_limiter(
    default_limit: int = 60,
    window_seconds: int = 60
) -> SlidingWindowRateLimiter:
    """Get or create global rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = SlidingWindowRateLimiter(
            default_limit=default_limit,
            window_seconds=window_seconds
        )
    return _rate_limiter


def _check_rate_by_scope(key: str, scope: str, default_limit: int) -> RateLimitResult:
    """Generic rate limit check by scope"""
    return get_rate_limiter().check(key, scope=scope, limit=default_limit)


# Convenience functions for common use cases
def check_sms_rate(phone: str, limit: int = 5) -> RateLimitResult:
    """Check SMS rate limit for a phone number"""
    return _check_rate_by_scope(phone, "sms", limit)


def check_api_rate(client_id: str, limit: int = 60) -> RateLimitResult:
    """Check API rate limit for a client (IP or API key)"""
    return _check_rate_by_scope(client_id, "api", limit)


def check_webhook_rate(source: str, limit: int = 30) -> RateLimitResult:
    """Check webhook rate limit for a source"""
    return _check_rate_by_scope(source, "webhook", limit)


def require_rate_limit(
    key: str,
    scope: str = "default",
    limit: int = 60
) -> None:
    """
    Check rate limit and raise exception if exceeded.
    
    Usage:
        require_rate_limit(phone_number, "sms", limit=5)
    """
    result = get_rate_limiter().check(key, scope, limit)
    if not result.allowed:
        raise RateLimitExceeded(
            message=f"Rate limit exceeded: {result.current_count}/{result.limit}",
            retry_after=result.retry_after
        )
