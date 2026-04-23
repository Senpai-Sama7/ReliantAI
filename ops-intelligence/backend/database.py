"""
Ops Intelligence — PostgreSQL persistence layer.
All 7 operational domains write here.
"""

import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from typing import Any, Optional

DB_URL = os.getenv(
    "DATABASE_URL",
    os.getenv("OPS_DB_PATH", "postgresql://user:pass@localhost/ops_intelligence"),
)


def _get_conn_raw():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)


class _CursorWrapper:
    """sqlite3-style cursor wrapper for psycopg2."""
    def __init__(self, cursor):
        self._cursor = cursor

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()


class _ConnWrapper:
    """sqlite3-style connection wrapper for psycopg2."""
    def __init__(self, conn):
        self._conn = conn

    def executescript(self, sql: str):
        """Execute multi-statement SQL (psycopg2 doesn't have executescript)."""
        cursor = self._conn.cursor()
        cursor.execute(sql)
        cursor.close()

    def execute(self, sql: str, params=None):
        """Execute SQL and return a cursor wrapper."""
        # Translate sqlite3 ? placeholders to psycopg2 %s
        if params is not None and "?" in sql:
            sql = sql.replace("?", "%s")
        cursor = self._conn.cursor()
        cursor.execute(sql, params)
        return _CursorWrapper(cursor)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def _get_conn():
    return _ConnWrapper(_get_conn_raw())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS incidents (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            severity    TEXT NOT NULL DEFAULT 'SEV-2',
            phase       TEXT NOT NULL DEFAULT 'triage',
            status      TEXT NOT NULL DEFAULT 'active',
            blast_radius TEXT,
            root_cause  TEXT,
            timeline    TEXT NOT NULL DEFAULT '[]',
            created_at  TEXT NOT NULL,
            resolved_at TEXT
        );

        CREATE TABLE IF NOT EXISTS debt_items (
            id                  TEXT PRIMARY KEY,
            name                TEXT NOT NULL,
            description         TEXT,
            interest_per_year   REAL NOT NULL DEFAULT 0,
            principal_cost      REAL NOT NULL DEFAULT 0,
            roi                 REAL GENERATED ALWAYS AS (
                CASE WHEN principal_cost > 0
                     THEN (interest_per_year / principal_cost) * 100
                     ELSE 0 END
            ) STORED,
            status              TEXT NOT NULL DEFAULT 'open',
            created_at          TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cost_snapshots (
            id                  TEXT PRIMARY KEY,
            service_name        TEXT NOT NULL,
            monthly_cost        REAL NOT NULL,
            savings_opportunity REAL NOT NULL DEFAULT 0,
            category            TEXT NOT NULL DEFAULT 'compute',
            notes               TEXT,
            recorded_at         TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pipelines (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'healthy',
            quality_score   REAL NOT NULL DEFAULT 100,
            cost_per_record REAL NOT NULL DEFAULT 0,
            records_per_day INTEGER NOT NULL DEFAULT 0,
            last_run        TEXT,
            sla_minutes     INTEGER NOT NULL DEFAULT 60,
            phase           TEXT NOT NULL DEFAULT 'ingestion'
        );

        CREATE TABLE IF NOT EXISTS performance_items (
            id              TEXT PRIMARY KEY,
            service         TEXT NOT NULL,
            metric          TEXT NOT NULL,
            current_value   REAL NOT NULL,
            baseline_value  REAL NOT NULL,
            unit            TEXT NOT NULL DEFAULT 'ms',
            bottleneck      TEXT,
            root_cause      TEXT,
            status          TEXT NOT NULL DEFAULT 'open',
            created_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS migrations (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            phase           TEXT NOT NULL DEFAULT 'scope',
            risk_level      TEXT NOT NULL DEFAULT 'medium',
            rollback_ready  INTEGER NOT NULL DEFAULT 0,
            zero_downtime   INTEGER NOT NULL DEFAULT 1,
            kill_switch     INTEGER NOT NULL DEFAULT 0,
            validation_pct  REAL NOT NULL DEFAULT 0,
            started_at      TEXT,
            completed_at    TEXT,
            created_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS api_contracts (
            id                  TEXT PRIMARY KEY,
            endpoint            TEXT NOT NULL,
            version             TEXT NOT NULL DEFAULT 'v1',
            method              TEXT NOT NULL DEFAULT 'GET',
            service             TEXT NOT NULL,
            breaking_changes    INTEGER NOT NULL DEFAULT 0,
            doc_complete        INTEGER NOT NULL DEFAULT 0,
            consistency_score   REAL NOT NULL DEFAULT 100,
            last_checked        TEXT,
            notes               TEXT,
            created_at          TEXT NOT NULL
        );

        -- ── REVENUE INTELLIGENCE ─────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS revenue_leads (
            id              TEXT PRIMARY KEY,
            external_id     TEXT,
            company         TEXT NOT NULL,
            contact_name    TEXT,
            phone           TEXT,
            email           TEXT,
            city            TEXT,
            rating          REAL NOT NULL DEFAULT 0,
            review_count    INTEGER NOT NULL DEFAULT 0,
            has_website     INTEGER NOT NULL DEFAULT 0,
            lead_score      REAL NOT NULL DEFAULT 0,
            product_line    TEXT NOT NULL DEFAULT 'hvac',
            deal_value      REAL NOT NULL DEFAULT 0,
            stage           TEXT NOT NULL DEFAULT 'new',
            source          TEXT NOT NULL DEFAULT 'csv',
            notes           TEXT,
            last_contacted  TEXT,
            created_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS revenue_events (
            id              TEXT PRIMARY KEY,
            lead_id         TEXT,
            event_type      TEXT NOT NULL,
            product_line    TEXT NOT NULL DEFAULT 'hvac',
            amount          REAL NOT NULL DEFAULT 0,
            description     TEXT,
            reference_id    TEXT,
            recorded_at     TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS billing_records (
            id              TEXT PRIMARY KEY,
            lead_id         TEXT NOT NULL,
            company         TEXT NOT NULL,
            line_items      TEXT NOT NULL DEFAULT '[]',
            subtotal        REAL NOT NULL DEFAULT 0,
            status          TEXT NOT NULL DEFAULT 'draft',
            invoice_date    TEXT NOT NULL,
            due_date        TEXT,
            paid_at         TEXT
        );
    """)
    conn.commit()


# ── Incidents ──────────────────────────────────────────────────────────────

def create_incident(id: str, title: str, severity: str, blast_radius: str = "") -> dict:
    conn = _get_conn()
    now = _now()
    timeline = json.dumps([{"phase": "triage", "ts": now, "note": "Incident opened"}])
    conn.execute(
        "INSERT INTO incidents (id, title, severity, phase, status, blast_radius, timeline, created_at) "
        "VALUES (?, ?, ?, 'triage', 'active', ?, ?, ?)",
        (id, title, severity, blast_radius, timeline, now)
    )
    conn.commit()
    return get_incident(id)


def get_incident(id: str) -> Optional[dict]:
    row = _get_conn().execute("SELECT * FROM incidents WHERE id=?", (id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_incidents(status: str = None) -> list[dict]:
    if status:
        rows = _get_conn().execute(
            "SELECT * FROM incidents WHERE status=? ORDER BY created_at DESC", (status,)
        ).fetchall()
    else:
        rows = _get_conn().execute(
            "SELECT * FROM incidents ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def advance_incident_phase(id: str, phase: str, note: str = "") -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT timeline FROM incidents WHERE id=?", (id,)).fetchone()
    if not row:
        return None
    timeline = json.loads(row["timeline"])
    timeline.append({"phase": phase, "ts": _now(), "note": note})
    conn.execute(
        "UPDATE incidents SET phase=?, timeline=? WHERE id=?",
        (phase, json.dumps(timeline), id)
    )
    conn.commit()
    return get_incident(id)


def resolve_incident(id: str, root_cause: str) -> Optional[dict]:
    conn = _get_conn()
    now = _now()
    row = conn.execute("SELECT timeline FROM incidents WHERE id=?", (id,)).fetchone()
    if not row:
        return None
    timeline = json.loads(row["timeline"])
    timeline.append({"phase": "resolved", "ts": now, "note": f"Root cause: {root_cause}"})
    conn.execute(
        "UPDATE incidents SET status='resolved', phase='resolved', root_cause=?, "
        "resolved_at=?, timeline=? WHERE id=?",
        (root_cause, now, json.dumps(timeline), id)
    )
    conn.commit()
    return get_incident(id)


# ── Debt items ─────────────────────────────────────────────────────────────

def create_debt_item(id: str, name: str, description: str,
                     interest_per_year: float, principal_cost: float) -> dict:
    conn = _get_conn()
    conn.execute(
        "INSERT INTO debt_items (id, name, description, interest_per_year, principal_cost, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (id, name, description, interest_per_year, principal_cost, _now())
    )
    conn.commit()
    return get_debt_item(id)


def get_debt_item(id: str) -> Optional[dict]:
    row = _get_conn().execute("SELECT * FROM debt_items WHERE id=?", (id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_debt_items(status: str = None) -> list[dict]:
    if status:
        rows = _get_conn().execute(
            "SELECT * FROM debt_items WHERE status=? ORDER BY roi DESC", (status,)
        ).fetchall()
    else:
        rows = _get_conn().execute(
            "SELECT * FROM debt_items ORDER BY roi DESC"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_debt_status(id: str, status: str) -> Optional[dict]:
    _get_conn().execute("UPDATE debt_items SET status=? WHERE id=?", (status, id))
    _get_conn().commit()
    return get_debt_item(id)


# ── Cost snapshots ─────────────────────────────────────────────────────────

def create_cost_snapshot(id: str, service_name: str, monthly_cost: float,
                         savings_opportunity: float, category: str, notes: str = "") -> dict:
    conn = _get_conn()
    conn.execute(
        "INSERT INTO cost_snapshots (id, service_name, monthly_cost, savings_opportunity, "
        "category, notes, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (id, service_name, monthly_cost, savings_opportunity, category, notes, _now())
    )
    conn.commit()
    return get_cost_snapshot(id)


def get_cost_snapshot(id: str) -> Optional[dict]:
    row = _get_conn().execute("SELECT * FROM cost_snapshots WHERE id=?", (id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_cost_snapshots() -> list[dict]:
    rows = _get_conn().execute(
        "SELECT * FROM cost_snapshots ORDER BY recorded_at DESC"
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def cost_summary() -> dict:
    conn = _get_conn()
    row = conn.execute(
        "SELECT SUM(monthly_cost) as total_cost, SUM(savings_opportunity) as total_savings, "
        "COUNT(*) as service_count FROM cost_snapshots"
    ).fetchone()
    return {
        "total_monthly_cost": row["total_cost"] or 0,
        "total_savings_opportunity": row["total_savings"] or 0,
        "service_count": row["service_count"] or 0,
    }


# ── Pipelines ──────────────────────────────────────────────────────────────

def upsert_pipeline(id: str, name: str, status: str, quality_score: float,
                    cost_per_record: float, records_per_day: int,
                    sla_minutes: int, phase: str) -> dict:
    conn = _get_conn()
    now = _now()
    conn.execute("""
        INSERT INTO pipelines (id, name, status, quality_score, cost_per_record,
                               records_per_day, last_run, sla_minutes, phase)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            status=excluded.status, quality_score=excluded.quality_score,
            cost_per_record=excluded.cost_per_record, records_per_day=excluded.records_per_day,
            last_run=excluded.last_run, sla_minutes=excluded.sla_minutes, phase=excluded.phase
    """, (id, name, status, quality_score, cost_per_record, records_per_day, now, sla_minutes, phase))
    conn.commit()
    return get_pipeline(id)


def get_pipeline(id: str) -> Optional[dict]:
    row = _get_conn().execute("SELECT * FROM pipelines WHERE id=?", (id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_pipelines() -> list[dict]:
    rows = _get_conn().execute("SELECT * FROM pipelines ORDER BY name").fetchall()
    return [_row_to_dict(r) for r in rows]


# ── Performance items ──────────────────────────────────────────────────────

def create_performance_item(id: str, service: str, metric: str,
                            current_value: float, baseline_value: float,
                            unit: str, bottleneck: str = "") -> dict:
    conn = _get_conn()
    conn.execute(
        "INSERT INTO performance_items (id, service, metric, current_value, baseline_value, "
        "unit, bottleneck, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (id, service, metric, current_value, baseline_value, unit, bottleneck, _now())
    )
    conn.commit()
    return get_performance_item(id)


def get_performance_item(id: str) -> Optional[dict]:
    row = _get_conn().execute("SELECT * FROM performance_items WHERE id=?", (id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_performance_items(status: str = None) -> list[dict]:
    if status:
        rows = _get_conn().execute(
            "SELECT * FROM performance_items WHERE status=? ORDER BY created_at DESC", (status,)
        ).fetchall()
    else:
        rows = _get_conn().execute(
            "SELECT * FROM performance_items ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def resolve_performance_item(id: str, root_cause: str) -> Optional[dict]:
    _get_conn().execute(
        "UPDATE performance_items SET status='resolved', root_cause=? WHERE id=?",
        (root_cause, id)
    )
    _get_conn().commit()
    return get_performance_item(id)


# ── Migrations ─────────────────────────────────────────────────────────────

def create_migration(id: str, name: str, risk_level: str) -> dict:
    conn = _get_conn()
    conn.execute(
        "INSERT INTO migrations (id, name, phase, risk_level, created_at) VALUES (?, ?, 'scope', ?, ?)",
        (id, name, risk_level, _now())
    )
    conn.commit()
    return get_migration(id)


def get_migration(id: str) -> Optional[dict]:
    row = _get_conn().execute("SELECT * FROM migrations WHERE id=?", (id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_migrations() -> list[dict]:
    rows = _get_conn().execute(
        "SELECT * FROM migrations ORDER BY created_at DESC"
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def advance_migration_phase(id: str, phase: str, rollback_ready: bool = False,
                            kill_switch: bool = False, validation_pct: float = 0) -> Optional[dict]:
    conn = _get_conn()
    now = _now()
    started_at_sql = ""
    if phase == "execution":
        conn.execute(
            "UPDATE migrations SET phase=?, rollback_ready=?, kill_switch=?, "
            "validation_pct=?, started_at=? WHERE id=?",
            (phase, int(rollback_ready), int(kill_switch), validation_pct, now, id)
        )
    elif phase == "completed":
        conn.execute(
            "UPDATE migrations SET phase=?, rollback_ready=?, kill_switch=?, "
            "validation_pct=?, completed_at=? WHERE id=?",
            (phase, int(rollback_ready), int(kill_switch), validation_pct, now, id)
        )
    else:
        conn.execute(
            "UPDATE migrations SET phase=?, rollback_ready=?, kill_switch=?, validation_pct=? WHERE id=?",
            (phase, int(rollback_ready), int(kill_switch), validation_pct, id)
        )
    conn.commit()
    return get_migration(id)


# ── API Contracts ──────────────────────────────────────────────────────────

def create_api_contract(id: str, endpoint: str, version: str, method: str,
                        service: str, notes: str = "") -> dict:
    conn = _get_conn()
    conn.execute(
        "INSERT INTO api_contracts (id, endpoint, version, method, service, notes, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (id, endpoint, version, method, service, notes, _now())
    )
    conn.commit()
    return get_api_contract(id)


def get_api_contract(id: str) -> Optional[dict]:
    row = _get_conn().execute("SELECT * FROM api_contracts WHERE id=?", (id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_api_contracts(service: str = None) -> list[dict]:
    if service:
        rows = _get_conn().execute(
            "SELECT * FROM api_contracts WHERE service=? ORDER BY endpoint", (service,)
        ).fetchall()
    else:
        rows = _get_conn().execute(
            "SELECT * FROM api_contracts ORDER BY service, endpoint"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_api_contract_check(id: str, breaking_changes: int,
                              doc_complete: bool, consistency_score: float) -> Optional[dict]:
    conn = _get_conn()
    conn.execute(
        "UPDATE api_contracts SET breaking_changes=?, doc_complete=?, "
        "consistency_score=?, last_checked=? WHERE id=?",
        (breaking_changes, int(doc_complete), consistency_score, _now(), id)
    )
    conn.commit()
    return get_api_contract(id)


# ── Revenue Leads ──────────────────────────────────────────────────────────

def upsert_revenue_lead(id: str, external_id: str, company: str, contact_name: str,
                        phone: str, email: str, city: str, rating: float,
                        review_count: int, has_website: bool, lead_score: float,
                        product_line: str, deal_value: float, source: str,
                        notes: str = "") -> dict:
    conn = _get_conn()
    now = _now()
    conn.execute("""
        INSERT INTO revenue_leads (id, external_id, company, contact_name, phone, email,
            city, rating, review_count, has_website, lead_score, product_line,
            deal_value, source, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            lead_score=excluded.lead_score, notes=excluded.notes,
            rating=excluded.rating, review_count=excluded.review_count
    """, (id, external_id, company, contact_name, phone, email, city,
          rating, review_count, int(has_website), lead_score, product_line,
          deal_value, source, notes, now))
    conn.commit()
    return get_revenue_lead(id)


def get_revenue_lead(id: str) -> Optional[dict]:
    row = _get_conn().execute("SELECT * FROM revenue_leads WHERE id=?", (id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_revenue_leads(stage: str = None, product_line: str = None,
                       limit: int = 100) -> list[dict]:
    query = "SELECT * FROM revenue_leads WHERE 1=1"
    params: list = []
    if stage:
        query += " AND stage=?"
        params.append(stage)
    if product_line:
        query += " AND product_line=?"
        params.append(product_line)
    query += " ORDER BY lead_score DESC LIMIT ?"
    params.append(limit)
    rows = _get_conn().execute(query, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def advance_lead_stage(id: str, stage: str, notes: str = "") -> Optional[dict]:
    conn = _get_conn()
    conn.execute(
        "UPDATE revenue_leads SET stage=?, last_contacted=?, notes=? WHERE id=?",
        (stage, _now(), notes, id)
    )
    conn.commit()
    return get_revenue_lead(id)


def lead_funnel_stats() -> dict:
    conn = _get_conn()
    stages = ['new', 'contacted', 'interested', 'demo', 'negotiating', 'won', 'lost']
    funnel = {}
    for stage in stages:
        row = conn.execute(
            "SELECT COUNT(*) as cnt, SUM(deal_value) as val FROM revenue_leads WHERE stage=?",
            (stage,)
        ).fetchone()
        funnel[stage] = {"count": row["cnt"] or 0, "value": row["val"] or 0}
    # Pipeline value = interested + demo + negotiating
    pipeline_stages = ('interested', 'demo', 'negotiating')
    row = conn.execute(
        "SELECT SUM(deal_value) as val FROM revenue_leads WHERE stage IN (?,?,?)",
        pipeline_stages
    ).fetchone()
    return {
        "funnel": funnel,
        "pipeline_value": row["val"] or 0,
        "total_leads": sum(v["count"] for v in funnel.values()),
    }


# ── Revenue Events ─────────────────────────────────────────────────────────

def record_revenue_event(id: str, lead_id: str, event_type: str,
                         product_line: str, amount: float,
                         description: str = "", reference_id: str = "") -> dict:
    conn = _get_conn()
    conn.execute(
        "INSERT INTO revenue_events (id, lead_id, event_type, product_line, amount, "
        "description, reference_id, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (id, lead_id, event_type, product_line, amount, description, reference_id, _now())
    )
    conn.commit()
    return dict(_get_conn().execute("SELECT * FROM revenue_events WHERE id=?", (id,)).fetchone())


def list_revenue_events(product_line: str = None, days: int = 30) -> list[dict]:
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    if product_line:
        rows = _get_conn().execute(
            "SELECT * FROM revenue_events WHERE product_line=? AND recorded_at>=? ORDER BY recorded_at DESC",
            (product_line, cutoff)
        ).fetchall()
    else:
        rows = _get_conn().execute(
            "SELECT * FROM revenue_events WHERE recorded_at>=? ORDER BY recorded_at DESC",
            (cutoff,)
        ).fetchall()
    return [dict(r) for r in rows]


def revenue_summary(days: int = 30) -> dict:
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    conn = _get_conn()
    row = conn.execute(
        "SELECT SUM(amount) as total, COUNT(*) as events FROM revenue_events WHERE recorded_at>=?",
        (cutoff,)
    ).fetchone()
    by_product = conn.execute(
        "SELECT product_line, SUM(amount) as total FROM revenue_events "
        "WHERE recorded_at>=? GROUP BY product_line",
        (cutoff,)
    ).fetchall()
    return {
        "period_days": days,
        "total_revenue": round(row["total"] or 0, 2),
        "total_events": row["events"] or 0,
        "by_product": {r["product_line"]: round(r["total"] or 0, 2) for r in by_product},
    }


# ── Billing Records ────────────────────────────────────────────────────────

def create_billing_record(id: str, lead_id: str, company: str,
                          line_items: list, subtotal: float) -> dict:
    conn = _get_conn()
    now = _now()
    from datetime import timedelta
    due = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    conn.execute(
        "INSERT INTO billing_records (id, lead_id, company, line_items, subtotal, "
        "status, invoice_date, due_date) VALUES (?, ?, ?, ?, ?, 'draft', ?, ?)",
        (id, lead_id, company, json.dumps(line_items), subtotal, now, due)
    )
    conn.commit()
    return get_billing_record(id)


def get_billing_record(id: str) -> Optional[dict]:
    row = _get_conn().execute("SELECT * FROM billing_records WHERE id=?", (id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    if isinstance(d.get("line_items"), str):
        d["line_items"] = json.loads(d["line_items"])
    return d


def list_billing_records(status: str = None) -> list[dict]:
    if status:
        rows = _get_conn().execute(
            "SELECT * FROM billing_records WHERE status=? ORDER BY invoice_date DESC", (status,)
        ).fetchall()
    else:
        rows = _get_conn().execute(
            "SELECT * FROM billing_records ORDER BY invoice_date DESC"
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("line_items"), str):
            d["line_items"] = json.loads(d["line_items"])
        result.append(d)
    return result


def mark_invoice_sent(id: str) -> Optional[dict]:
    _get_conn().execute("UPDATE billing_records SET status='sent' WHERE id=?", (id,))
    _get_conn().commit()
    return get_billing_record(id)


def mark_invoice_paid(id: str) -> Optional[dict]:
    _get_conn().execute(
        "UPDATE billing_records SET status='paid', paid_at=? WHERE id=?", (_now(), id)
    )
    _get_conn().commit()
    return get_billing_record(id)


# ── Utilities ──────────────────────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    d = dict(row)
    # Parse timeline JSON if present
    if "timeline" in d and isinstance(d["timeline"], str):
        try:
            d["timeline"] = json.loads(d["timeline"])
        except (json.JSONDecodeError, TypeError):
            pass
    return d
