"""
HVAC AI Dispatch — PostgreSQL Persistence Layer
Enterprise-grade dispatch history + message log.
"""

import json
import os
import threading
from datetime import datetime, timezone
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool

from config import setup_logging

logger = setup_logging("hvac_db")

_pool = None
_pool_lock = threading.Lock()

def get_database_url() -> str:
    """Resolve the active database URL, honoring runtime/test overrides."""
    return os.environ.get("DATABASE_URL", "postgresql://reliantai:change-in-production@127.0.0.1:5435/reliantai_integration")

def get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                db_url = get_database_url()
                _pool = pool.ThreadedConnectionPool(1, 20, dsn=db_url)
    return _pool

def close_all_connections() -> None:
    """Close every tracked PostgreSQL connection."""
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.closeall()
            _pool = None

def close_thread_local_connection() -> None:
    """
    No-op for PostgreSQL connection pool.
    
    This function exists for backward compatibility with tests that were written
    for the older SQLite-based database implementation. In the PostgreSQL
    connection pool model, thread-local connections are managed automatically
    by the pool, so this function does nothing.
    """
    # No-op: connection pool manages thread-local connections automatically

def init_db() -> None:
    """Create tables if they don't exist. Call once at startup."""
    conn = get_pool().getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dispatches (
                    dispatch_id   TEXT PRIMARY KEY,
                    customer_name TEXT,
                    customer_phone TEXT,
                    address       TEXT,
                    issue_summary TEXT,
                    urgency       TEXT,
                    tech_name     TEXT,
                    eta           TEXT,
                    status        TEXT DEFAULT 'pending',
                    crew_result   TEXT,
                    created_at    TEXT,
                    updated_at    TEXT
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id            SERIAL PRIMARY KEY,
                    direction     TEXT,          -- 'inbound' | 'outbound'
                    phone         TEXT,
                    body          TEXT,
                    sms_sid       TEXT,
                    channel       TEXT DEFAULT 'sms',   -- 'sms' | 'whatsapp'
                    created_at    TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_dispatches_status ON dispatches(status);
                CREATE INDEX IF NOT EXISTS idx_messages_phone ON messages(phone);

                -- Customers table for multi-tenant billing
                CREATE TABLE IF NOT EXISTS customers (
                    id              SERIAL PRIMARY KEY,
                    stripe_customer_id TEXT UNIQUE,
                    stripe_subscription_id TEXT,
                    api_key         TEXT UNIQUE NOT NULL,
                    email           TEXT NOT NULL,
                    name            TEXT,
                    company         TEXT,
                    phone           TEXT,
                    plan            TEXT DEFAULT 'free', -- free, starter, professional, enterprise
                    status          TEXT DEFAULT 'active', -- active, inactive, past_due, cancelled
                    billing_status  TEXT DEFAULT 'trialing', -- trialing, active, past_due, cancelled
                    trial_ends_at   TIMESTAMP,
                    subscription_starts_at TIMESTAMP,
                    subscription_ends_at TIMESTAMP,
                    monthly_revenue DECIMAL(10, 2) DEFAULT 0,
                    lead_source     TEXT,
                    notes           TEXT,
                    outreach_status TEXT DEFAULT 'new', -- new, contacted, qualified, proposal, closed_won, closed_lost
                    outreach_last_contact TIMESTAMP,
                    outreach_next_contact TIMESTAMP,
                    created_at      TIMESTAMP DEFAULT NOW(),
                    updated_at      TIMESTAMP DEFAULT NOW()
                );

                -- Customer events table for audit/revenue tracking
                CREATE TABLE IF NOT EXISTS customer_events (
                    id              SERIAL PRIMARY KEY,
                    customer_id     INTEGER REFERENCES customers(id) ON DELETE CASCADE,
                    event_type      TEXT NOT NULL, -- dispatch_created, api_called, subscription_started, payment_succeeded, etc.
                    event_data      JSONB,
                    revenue_impact  DECIMAL(10, 2) DEFAULT 0,
                    created_at      TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_customers_api_key ON customers(api_key);
                CREATE INDEX IF NOT EXISTS idx_customers_stripe_id ON customers(stripe_customer_id);
                CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
                CREATE INDEX IF NOT EXISTS idx_customers_outreach ON customers(outreach_status);
                CREATE INDEX IF NOT EXISTS idx_customer_events_customer ON customer_events(customer_id);
                CREATE INDEX IF NOT EXISTS idx_customer_events_type ON customer_events(event_type);
                CREATE INDEX IF NOT EXISTS idx_customer_events_created ON customer_events(created_at);
            """)
        conn.commit()
    finally:
        get_pool().putconn(conn)
    logger.info("Database initialized at PostgreSQL target.")

# ── Dispatch CRUD ──────────────────────────────────────────────

def save_dispatch(
    dispatch_id: str,
    customer_name: str = "",
    customer_phone: str = "",
    address: str = "",
    issue_summary: str = "",
    urgency: str = "",
    tech_name: str = "",
    eta: str = "",
    status: str = "pending",
    crew_result: Optional[dict] = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = get_pool().getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO dispatches
                   (dispatch_id, customer_name, customer_phone, address,
                    issue_summary, urgency, tech_name, eta, status,
                    crew_result, created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (dispatch_id) DO UPDATE SET
                    customer_name = EXCLUDED.customer_name,
                    customer_phone = EXCLUDED.customer_phone,
                    address = EXCLUDED.address,
                    issue_summary = EXCLUDED.issue_summary,
                    urgency = EXCLUDED.urgency,
                    tech_name = EXCLUDED.tech_name,
                    eta = EXCLUDED.eta,
                    status = EXCLUDED.status,
                    crew_result = EXCLUDED.crew_result,
                    updated_at = EXCLUDED.updated_at
                """,
                (dispatch_id, customer_name, customer_phone, address,
                 issue_summary, urgency, tech_name, eta, status,
                 json.dumps(crew_result) if crew_result else None,
                 now, now),
            )
        conn.commit()
    finally:
        get_pool().putconn(conn)

def update_dispatch_status(dispatch_id: str, status: str, result: Optional[dict] = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = get_pool().getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """UPDATE dispatches SET status = %s, crew_result = %s, updated_at = %s
                   WHERE dispatch_id = %s""",
                (status, json.dumps(result) if result else None, now, dispatch_id),
            )
        conn.commit()
    finally:
        get_pool().putconn(conn)

def get_dispatch(dispatch_id: str) -> Optional[dict]:
    conn = get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM dispatches WHERE dispatch_id = %s", (dispatch_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    finally:
        get_pool().putconn(conn)

def get_recent_dispatches(limit: int = 50) -> list[dict]:
    conn = get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM dispatches ORDER BY created_at DESC LIMIT %s", (limit,)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    finally:
        get_pool().putconn(conn)

# ── Message log ────────────────────────────────────────────────

def log_message(
    direction: str,
    phone: str,
    body: str,
    sms_sid: str = "",
    channel: str = "sms",
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = get_pool().getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO messages (direction, phone, body, sms_sid, channel, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (direction, phone, body, sms_sid, channel, now),
            )
        conn.commit()
    finally:
        get_pool().putconn(conn)


# ── Customer CRUD ──────────────────────────────────────────────

import secrets


def generate_api_key() -> str:
    """Generate a secure API key for customer authentication."""
    return f"sk_{secrets.token_urlsafe(32)}"


def create_customer(
    email: str,
    name: str = "",
    company: str = "",
    phone: str = "",
    stripe_customer_id: str = "",
    plan: str = "free",
    lead_source: str = "",
    notes: str = "",
) -> dict:
    """Create a new customer with API key."""
    api_key = generate_api_key()
    # Convert empty string to None for nullable unique constraint
    stripe_id = stripe_customer_id if stripe_customer_id else None
    conn = get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """INSERT INTO customers
                   (api_key, email, name, company, phone, stripe_customer_id, plan, lead_source, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (api_key, email, name, company, phone, stripe_id, plan, lead_source, notes),
            )
            row = cursor.fetchone()
            conn.commit()
            return dict(row)
    finally:
        get_pool().putconn(conn)


def get_customer_by_api_key(api_key: str) -> Optional[dict]:
    """Get customer by API key for authentication."""
    conn = get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM customers WHERE api_key = %s AND status = 'active'",
                (api_key,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    finally:
        get_pool().putconn(conn)


def get_customer_by_id(customer_id: int) -> Optional[dict]:
    """Get customer by internal ID."""
    conn = get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM customers WHERE id = %s",
                (customer_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    finally:
        get_pool().putconn(conn)


def get_customer_by_stripe_id(stripe_customer_id: str) -> Optional[dict]:
    """Get customer by Stripe customer ID."""
    conn = get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM customers WHERE stripe_customer_id = %s",
                (stripe_customer_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    finally:
        get_pool().putconn(conn)


def update_customer(customer_id: int, **kwargs) -> Optional[dict]:
    """Update customer fields."""
    allowed_fields = {
        'email', 'name', 'company', 'phone', 'plan', 'status', 'billing_status',
        'stripe_customer_id', 'stripe_subscription_id', 'trial_ends_at',
        'subscription_starts_at', 'subscription_ends_at', 'monthly_revenue',
        'lead_source', 'notes', 'outreach_status', 'outreach_last_contact',
        'outreach_next_contact'
    }
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    if not updates:
        return get_customer_by_id(customer_id)
    
    conn = get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [customer_id]
            cursor.execute(
                f"UPDATE customers SET {set_clause}, updated_at = NOW() WHERE id = %s RETURNING *",
                values,
            )
            row = cursor.fetchone()
            conn.commit()
            return dict(row) if row else None
    finally:
        get_pool().putconn(conn)


def list_customers(
    status: Optional[str] = None,
    plan: Optional[str] = None,
    outreach_status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """List customers with optional filtering."""
    conn = get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = "SELECT * FROM customers WHERE 1=1"
            params = []
            if status:
                query += " AND status = %s"
                params.append(status)
            if plan:
                query += " AND plan = %s"
                params.append(plan)
            if outreach_status:
                query += " AND outreach_status = %s"
                params.append(outreach_status)
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    finally:
        get_pool().putconn(conn)


def delete_customer(customer_id: int) -> bool:
    """Soft delete a customer by setting status to inactive."""
    conn = get_pool().getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE customers SET status = 'inactive', updated_at = NOW() WHERE id = %s",
                (customer_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
    finally:
        get_pool().putconn(conn)


# ── Customer Events CRUD ───────────────────────────────────────

def log_customer_event(
    customer_id: int,
    event_type: str,
    event_data: Optional[dict] = None,
    revenue_impact: float = 0,
) -> dict:
    """Log a customer event for audit and revenue tracking."""
    conn = get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """INSERT INTO customer_events
                   (customer_id, event_type, event_data, revenue_impact)
                   VALUES (%s, %s, %s, %s)
                   RETURNING *""",
                (customer_id, event_type, json.dumps(event_data) if event_data else None, revenue_impact),
            )
            row = cursor.fetchone()
            conn.commit()
            return dict(row)
    finally:
        get_pool().putconn(conn)


def get_customer_events(
    customer_id: int,
    event_type: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    """Get events for a customer."""
    conn = get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if event_type:
                cursor.execute(
                    """SELECT * FROM customer_events
                       WHERE customer_id = %s AND event_type = %s
                       ORDER BY created_at DESC LIMIT %s""",
                    (customer_id, event_type, limit),
                )
            else:
                cursor.execute(
                    """SELECT * FROM customer_events
                       WHERE customer_id = %s
                       ORDER BY created_at DESC LIMIT %s""",
                    (customer_id, limit),
                )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    finally:
        get_pool().putconn(conn)


def get_dispatch_metrics() -> dict:
    """Server-side dispatch stats — one query, no client-side counting."""
    conn = get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE urgency ILIKE 'emergency') AS emergency_count,
                    COUNT(*) FILTER (WHERE status ILIKE 'complete') AS completed_count,
                    COUNT(*) FILTER (WHERE status IN ('pending','queued')) AS pending_count,
                    COUNT(*) FILTER (WHERE created_at::date = CURRENT_DATE) AS today_count,
                    COUNT(*) FILTER (WHERE urgency ILIKE 'emergency' AND created_at::date = CURRENT_DATE) AS today_emergency
                   FROM dispatches"""
            )
            row = cursor.fetchone()
            if not row:
                return {"total": 0, "emergency_count": 0, "completed_count": 0,
                        "pending_count": 0, "today_count": 0, "today_emergency": 0,
                        "emergency_pct": 0}
            d = dict(row)
            total = d["total"] or 0
            d["emergency_pct"] = round((d["emergency_count"] / total * 100), 1) if total else 0
            return d
    finally:
        get_pool().putconn(conn)


def search_dispatches(
    query: str = "",
    status: str = "",
    urgency: str = "",
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Full-text search and filter across dispatches."""
    conn = get_pool().getconn()
    try:
        conditions = []
        params: list = []

        if query:
            conditions.append(
                "(issue_summary ILIKE %s OR customer_name ILIKE %s OR customer_phone ILIKE %s OR address ILIKE %s)"
            )
            like = f"%{query}%"
            params.extend([like, like, like, like])
        if status:
            conditions.append("status ILIKE %s")
            params.append(status)
        if urgency:
            conditions.append("urgency ILIKE %s")
            params.append(urgency)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.extend([limit, offset])

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"SELECT * FROM dispatches {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
                params,
            )
            return [dict(r) for r in cursor.fetchall()]
    finally:
        get_pool().putconn(conn)


_DISPATCH_UPDATABLE_FIELDS = frozenset({
    "status", "tech_name", "eta", "urgency", "customer_name",
    "customer_phone", "address", "issue_summary", "crew_result",
})

def update_dispatch_fields(dispatch_id: str, **fields) -> Optional[dict]:
    """Partial update for any dispatch field (status, tech_name, eta, etc.)."""
    if not fields:
        return None
    # Whitelist field names to prevent SQL injection via kwarg keys
    unknown = set(fields) - _DISPATCH_UPDATABLE_FIELDS
    if unknown:
        raise ValueError(f"Non-updatable dispatch fields: {unknown}")
    now = datetime.now(timezone.utc).isoformat()
    fields["updated_at"] = now
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    params = list(fields.values()) + [dispatch_id]
    conn = get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                f"UPDATE dispatches SET {set_clause} WHERE dispatch_id = %s RETURNING *",
                params,
            )
            row = cursor.fetchone()
            conn.commit()
            return dict(row) if row else None
    finally:
        get_pool().putconn(conn)


def get_revenue_summary(days: int = 30) -> dict:
    """Get revenue summary for the last N days."""
    conn = get_pool().getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """SELECT 
                    COUNT(DISTINCT customer_id) as active_customers,
                    SUM(revenue_impact) as total_revenue,
                    COUNT(*) as total_events
                   FROM customer_events
                   WHERE created_at > NOW() - (INTERVAL '1 day' * %s)""",
                (days,),
            )
            row = cursor.fetchone()
            return dict(row) if row else {
                'active_customers': 0,
                'total_revenue': 0,
                'total_events': 0
            }
    finally:
        get_pool().putconn(conn)
