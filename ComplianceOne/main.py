"""
ComplianceOne - Compliance & Audit Management Service
Real, working implementation for SOC2, GDPR, HIPAA compliance tracking
"""

import os
import json
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException, Header, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import sys
import os
from security_middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    InputValidationMiddleware,
    AuditLogMiddleware,
    verify_api_key
)

# Database
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool

app = FastAPI(title="ComplianceOne", version="1.0.0")

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
    allow_headers=["X-API-Key", "X-Request-ID", "Content-Type", "Authorization"],
    max_age=3600,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

# Database pool
_db_pool = None

def get_db_pool():
    global _db_pool
    if _db_pool is None:
        db_url = os.environ.get("DATABASE_URL", "postgresql://localhost/complianceone")
        _db_pool = psycopg2.pool.ThreadedConnectionPool(1, 10, db_url)
    return _db_pool

def init_db():
    """Initialize database tables"""
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS compliance_frameworks (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    version TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS compliance_controls (
                    id SERIAL PRIMARY KEY,
                    framework_id INTEGER REFERENCES compliance_frameworks(id),
                    control_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(framework_id, control_id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS compliance_audits (
                    id SERIAL PRIMARY KEY,
                    audit_id TEXT UNIQUE NOT NULL,
                    framework_id INTEGER REFERENCES compliance_frameworks(id),
                    status TEXT DEFAULT 'in_progress',
                    started_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP,
                    findings JSONB DEFAULT '{}',
                    score INTEGER,
                    auditor TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS compliance_evidence (
                    id SERIAL PRIMARY KEY,
                    control_id INTEGER REFERENCES compliance_controls(id),
                    audit_id INTEGER REFERENCES compliance_audits(id),
                    evidence_type TEXT,
                    file_hash TEXT,
                    metadata JSONB,
                    collected_at TIMESTAMP DEFAULT NOW(),
                    collected_by TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS compliance_violations (
                    id SERIAL PRIMARY KEY,
                    control_id INTEGER REFERENCES compliance_controls(id),
                    severity TEXT,
                    description TEXT,
                    detected_at TIMESTAMP DEFAULT NOW(),
                    resolved_at TIMESTAMP,
                    status TEXT DEFAULT 'open'
                )
            """)
        conn.commit()
    finally:
        pool.putconn(conn)

# Models
class FrameworkCreate(BaseModel):
    name: str
    description: str
    version: str = "1.0"

class ControlCreate(BaseModel):
    framework_id: int
    control_id: str
    title: str
    description: str
    category: str
    severity: str = "medium"

class AuditCreate(BaseModel):
    framework_id: int
    auditor: str

class EvidenceSubmit(BaseModel):
    control_id: int
    evidence_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ViolationReport(BaseModel):
    control_id: int
    severity: str
    description: str

# API Key validation is now handled by shared security middleware
# dependency 'verify_api_key' imported from shared.security_middleware

# Routes
@app.on_event("startup")
async def startup():
    init_db()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "complianceone", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/frameworks")
async def create_framework(data: FrameworkCreate, api_key: str = Depends(verify_api_key)):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO compliance_frameworks (name, description, version) VALUES (%s, %s, %s) RETURNING id",
                (data.name, data.description, data.version)
            )
            framework_id = cur.fetchone()[0]
        conn.commit()
        return {"id": framework_id, "name": data.name, "created": True}
    finally:
        pool.putconn(conn)

@app.get("/frameworks")
async def list_frameworks():
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM compliance_frameworks ORDER BY created_at DESC")
            frameworks = cur.fetchall()
        return {"frameworks": [dict(row) for row in frameworks]}
    finally:
        pool.putconn(conn)

@app.post("/controls")
async def create_control(data: ControlCreate, api_key: str = Depends(verify_api_key)):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO compliance_controls 
                   (framework_id, control_id, title, description, category, severity) 
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (data.framework_id, data.control_id, data.title, data.description, data.category, data.severity)
            )
            control_id = cur.fetchone()[0]
        conn.commit()
        return {"id": control_id, "control_id": data.control_id, "created": True}
    finally:
        pool.putconn(conn)

@app.get("/frameworks/{framework_id}/controls")
async def list_controls(framework_id: int):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM compliance_controls WHERE framework_id = %s ORDER BY control_id",
                (framework_id,)
            )
            controls = cur.fetchall()
        return {"controls": [dict(row) for row in controls]}
    finally:
        pool.putconn(conn)

@app.post("/audits")
async def create_audit(data: AuditCreate, api_key: str = Depends(verify_api_key)):
    audit_id = f"AUD-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{hashlib.sha256(str(data.framework_id).encode()).hexdigest()[:8]}"
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO compliance_audits (audit_id, framework_id, auditor) VALUES (%s, %s, %s) RETURNING id",
                (audit_id, data.framework_id, data.auditor)
            )
            db_id = cur.fetchone()[0]
        conn.commit()
        return {"id": db_id, "audit_id": audit_id, "status": "in_progress"}
    finally:
        pool.putconn(conn)

@app.get("/audits")
async def list_audits():
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT a.*, f.name as framework_name 
                FROM compliance_audits a 
                JOIN compliance_frameworks f ON a.framework_id = f.id 
                ORDER BY a.started_at DESC
            """)
            audits = cur.fetchall()
        return {"audits": [dict(row) for row in audits]}
    finally:
        pool.putconn(conn)

@app.post("/audits/{audit_id}/complete")
async def complete_audit(audit_id: str, score: int, findings: Dict[str, Any], api_key: str = Depends(verify_api_key)):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE compliance_audits 
                   SET status = 'completed', completed_at = NOW(), score = %s, findings = %s 
                   WHERE audit_id = %s""",
                (score, json.dumps(findings), audit_id)
            )
        conn.commit()
        return {"audit_id": audit_id, "status": "completed", "score": score}
    finally:
        pool.putconn(conn)

@app.post("/evidence")
async def submit_evidence(data: EvidenceSubmit, api_key: str = Depends(verify_api_key)):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO compliance_evidence 
                   (control_id, evidence_type, metadata, collected_by) 
                   VALUES (%s, %s, %s, %s) RETURNING id""",
                (data.control_id, data.evidence_type, json.dumps(data.metadata), "api")
            )
            evidence_id = cur.fetchone()[0]
        conn.commit()
        return {"id": evidence_id, "submitted": True}
    finally:
        pool.putconn(conn)

@app.post("/violations")
async def report_violation(data: ViolationReport, api_key: str = Depends(verify_api_key)):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO compliance_violations (control_id, severity, description) VALUES (%s, %s, %s) RETURNING id",
                (data.control_id, data.severity, data.description)
            )
            violation_id = cur.fetchone()[0]
        conn.commit()
        return {"id": violation_id, "reported": True, "status": "open"}
    finally:
        pool.putconn(conn)

@app.get("/violations")
async def list_violations(status: Optional[str] = None):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if status:
                cur.execute(
                    "SELECT * FROM compliance_violations WHERE status = %s ORDER BY detected_at DESC",
                    (status,)
                )
            else:
                cur.execute("SELECT * FROM compliance_violations ORDER BY detected_at DESC")
            violations = cur.fetchall()
        return {"violations": [dict(row) for row in violations]}
    finally:
        pool.putconn(conn)

@app.get("/dashboard")
async def compliance_dashboard():
    """Real-time compliance dashboard data"""
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Framework stats
            cur.execute("SELECT COUNT(*) as total_frameworks FROM compliance_frameworks")
            total_frameworks = cur.fetchone()["total_frameworks"]
            
            # Control stats
            cur.execute("SELECT COUNT(*) as total_controls FROM compliance_controls")
            total_controls = cur.fetchone()["total_controls"]
            
            # Audit stats
            cur.execute("SELECT COUNT(*) as total_audits FROM compliance_audits")
            total_audits = cur.fetchone()["total_audits"]
            cur.execute("SELECT COUNT(*) as completed_audits FROM compliance_audits WHERE status = 'completed'")
            completed_audits = cur.fetchone()["completed_audits"]
            
            # Violation stats
            cur.execute("SELECT COUNT(*) as open_violations FROM compliance_violations WHERE status = 'open'")
            open_violations = cur.fetchone()["open_violations"]
            
            # Recent activity
            cur.execute("""
                SELECT v.*, c.title as control_title
                FROM compliance_violations v
                JOIN compliance_controls c ON v.control_id = c.id
                ORDER BY v.detected_at DESC
                LIMIT 10
            """)
            recent_violations = [dict(row) for row in cur.fetchall()]
        
        return {
            "summary": {
                "frameworks": total_frameworks,
                "controls": total_controls,
                "audits": {"total": total_audits, "completed": completed_audits},
                "violations": {"open": open_violations}
            },
            "recent_violations": recent_violations,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    finally:
        pool.putconn(conn)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
