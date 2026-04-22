from __future__ import annotations

import json
import time
import hmac
import hashlib
from pathlib import Path

import pytest


@pytest.fixture()
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture()
def temp_db_path(tmp_path: Path) -> str:
    return str(tmp_path / "lead_queue.db")


def sign_webhook(secret: str, payload: dict) -> tuple[bytes, dict[str, str]]:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode("utf-8"), f"{ts}.".encode("utf-8") + raw, hashlib.sha256).hexdigest()
    return raw, {
        "X-Citadel-Timestamp": ts,
        "X-Citadel-Signature": f"sha256={sig}",
        "Content-Type": "application/json",
    }
