"""
ReliantAI Platform — Vault Client (Sidecar Pattern for Docker Compose)

Provides runtime secret fetching from HashiCorp Vault with:
  - In-memory LRU caching with TTL
  - Background auto-refresh thread (sidecar-like behavior)
  - Audit logging of every secret access
  - Graceful degradation if Vault is unreachable
  - Structured logging with correlation_id

Usage:
    from shared.vault_client import VaultClient

    vault = VaultClient(
        vault_addr="http://vault:8200",
        token=os.getenv("VAULT_TOKEN"),
        mount_path="secret",
    )

    db_password = vault.get_secret("data/money/db", field="password")

Environment:
    VAULT_ADDR       — Vault server address
    VAULT_TOKEN      — Authentication token (dev or wrapped)
    VAULT_MOUNT_PATH — KV v2 mount (default: secret)
"""

import json
import logging
import os
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger("vault_client")


class _LRUCache:
    """Thread-safe LRU cache with per-item TTL."""

    def __init__(self, maxsize: int = 128, default_ttl_seconds: int = 300):
        self._store: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = threading.RLock()
        self._maxsize = maxsize
        self._default_ttl = default_ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            if time.time() > item["expires_at"]:
                del self._store[key]
                return None
            # Move to end (most recently used)
            self._store.move_to_end(key)
            return item["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self._lock:
            expires_at = time.time() + (ttl or self._default_ttl)
            self._store[key] = {"value": value, "expires_at": expires_at}
            self._store.move_to_end(key)
            if len(self._store) > self._maxsize:
                self._store.popitem(last=False)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def invalidate_all(self) -> None:
        with self._lock:
            self._store.clear()


class VaultClient:
    """
    Vault KV v2 client with caching, background refresh, and audit logging.

    In Docker Compose, this acts as an in-process "sidecar" — a background
    thread refreshes cached secrets before they expire so that the hot path
    never blocks on a network call.
    """

    def __init__(
        self,
        vault_addr: Optional[str] = None,
        token: Optional[str] = None,
        mount_path: Optional[str] = None,
        cache_ttl_seconds: int = 300,
        cache_maxsize: int = 128,
        refresh_interval_seconds: int = 60,
        enable_auto_refresh: bool = True,
        correlation_id: Optional[str] = None,
    ):
        self.vault_addr = (vault_addr or os.getenv("VAULT_ADDR", "http://vault:8200")).rstrip("/")
        self.token = token or os.getenv("VAULT_TOKEN")
        self.mount_path = (mount_path or os.getenv("VAULT_MOUNT_PATH", "secret")).rstrip("/")
        self.correlation_id = correlation_id

        self._cache = _LRUCache(maxsize=cache_maxsize, default_ttl_seconds=cache_ttl_seconds)
        self._refresh_interval = refresh_interval_seconds
        self._enable_auto_refresh = enable_auto_refresh
        self._refresh_thread: Optional[threading.Thread] = None
        self._refresh_stop = threading.Event()
        self._refresh_keys: set = set()
        self._refresh_lock = threading.Lock()

        if self._enable_auto_refresh:
            self._start_refresh_thread()

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def get_secret(
        self,
        path: str,
        field: Optional[str] = None,
        ttl: Optional[int] = None,
        use_cache: bool = True,
    ) -> Any:
        """
        Fetch a secret from Vault KV v2.

        Args:
            path:       Secret path under the mount (e.g. "data/money/db").
            field:      Specific key inside the secret JSON (e.g. "password").
                        If None, returns the full data dict.
            ttl:        Override cache TTL for this read (seconds).
            use_cache:  Whether to consult the in-memory cache.

        Returns:
            The secret value (field or full dict).

        Raises:
            RuntimeError: If Vault is unreachable and the secret is not cached.
        """
        cache_key = f"{self.mount_path}/{path}"

        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._audit_log("secret_access", path=path, field=field, source="cache")
                return self._extract_field(cached, field)

        # Fetch from Vault
        data = self._fetch_from_vault(path)
        self._cache.set(cache_key, data, ttl=ttl)

        # Track for background refresh
        with self._refresh_lock:
            self._refresh_keys.add(cache_key)

        self._audit_log("secret_access", path=path, field=field, source="vault")
        return self._extract_field(data, field)

    def refresh_secret(self, path: str) -> Any:
        """Force a fresh read from Vault and update cache."""
        return self.get_secret(path, use_cache=False)

    def invalidate_cache(self, path: Optional[str] = None) -> None:
        """Invalidate one or all cached secrets."""
        if path:
            self._cache.invalidate(f"{self.mount_path}/{path}")
            with self._refresh_lock:
                self._refresh_keys.discard(f"{self.mount_path}/{path}")
        else:
            self._cache.invalidate_all()
            with self._refresh_lock:
                self._refresh_keys.clear()

    def rotate_secret(self, path: str, new_data: Dict[str, Any]) -> None:
        """
        Write a new version of a secret (admin/operator use).

        This updates Vault and immediately invalidates the local cache.
        """
        self._write_to_vault(path, new_data)
        self.invalidate_cache(path)
        self._audit_log("secret_rotate", path=path, source="api")

    def health(self) -> Dict[str, Any]:
        """Check Vault server health."""
        try:
            resp = requests.get(f"{self.vault_addr}/v1/sys/health", timeout=5)
            return {
                "reachable": True,
                "status_code": resp.status_code,
                "initialized": resp.json().get("initialized", False),
                "sealed": resp.json().get("sealed", True),
            }
        except requests.RequestException as e:
            return {"reachable": False, "error": str(e)}

    def close(self) -> None:
        """Stop the background refresh thread (graceful shutdown)."""
        self._refresh_stop.set()
        if self._refresh_thread and self._refresh_thread.is_alive():
            self._refresh_thread.join(timeout=5)

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _fetch_from_vault(self, path: str) -> Dict[str, Any]:
        url = f"{self.vault_addr}/v1/{self.mount_path}/{path}"
        headers = {"X-Vault-Token": self.token} if self.token else {}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
        except requests.RequestException as e:
            raise RuntimeError(f"Vault unreachable at {self.vault_addr}: {e}") from e

        if resp.status_code == 404:
            raise RuntimeError(f"Secret not found at {url}")
        if resp.status_code == 403:
            raise RuntimeError(f"Permission denied for secret at {url}")
        if not resp.ok:
            raise RuntimeError(f"Vault error {resp.status_code}: {resp.text}")

        payload = resp.json()
        data = payload.get("data", {})
        # KV v2 nests data under "data" key
        if "data" in data and isinstance(data["data"], dict):
            return data["data"]
        return data

    def _write_to_vault(self, path: str, new_data: Dict[str, Any]) -> None:
        url = f"{self.vault_addr}/v1/{self.mount_path}/{path}"
        headers = {"X-Vault-Token": self.token} if self.token else {}

        resp = requests.post(url, headers=headers, json={"data": new_data}, timeout=10)
        if not resp.ok:
            raise RuntimeError(f"Vault write error {resp.status_code}: {resp.text}")

    def _extract_field(self, data: Dict[str, Any], field: Optional[str]) -> Any:
        if field is None:
            return data
        if field not in data:
            raise KeyError(f"Field '{field}' not found in secret data. Available: {list(data.keys())}")
        return data[field]

    def _audit_log(self, action: str, **kwargs) -> None:
        log_entry = {
            "event": "vault_audit",
            "action": action,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "correlation_id": self.correlation_id,
        }
        log_entry.update(kwargs)
        logger.info(json.dumps(log_entry))

    def _start_refresh_thread(self) -> None:
        def _refresh_loop():
            while not self._refresh_stop.is_set():
                self._refresh_stop.wait(self._refresh_interval)
                if self._refresh_stop.is_set():
                    break
                self._run_refresh_cycle()

        self._refresh_thread = threading.Thread(target=_refresh_loop, name="vault-refresh", daemon=True)
        self._refresh_thread.start()
        logger.info("Vault background refresh thread started (interval=%ds)", self._refresh_interval)

    def _run_refresh_cycle(self) -> None:
        with self._refresh_lock:
            keys = list(self._refresh_keys)

        for cache_key in keys:
            # Skip if still fresh (more than half TTL remaining)
            item = self._cache._store.get(cache_key)
            if item and time.time() < (item["expires_at"] - (self._cache._default_ttl / 2)):
                continue

            # Parse mount_path/path from cache_key
            # cache_key = "{mount_path}/{path}"
            path = cache_key[len(self.mount_path) + 1:]
            try:
                data = self._fetch_from_vault(path)
                self._cache.set(cache_key, data)
                self._audit_log("secret_refresh", path=path, source="background")
            except Exception as e:
                logger.warning("Background refresh failed for %s: %s", path, e)
