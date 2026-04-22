#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

log = logging.getLogger("citadel.lead_queue")

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH_DEFAULT = str(PROJECT_ROOT / "workspace" / "state" / "lead_queue.db")

PIPELINE_STATES = (
    "scouted",
    "qualified",
    "built",
    "approved",
    "deployed",
    "emailed",
    "replied",
    "disqualified",
)

VALID_TRANSITIONS = {
    "scouted": {"qualified", "disqualified"},
    "qualified": {"built", "disqualified"},
    "built": {"approved", "disqualified"},
    "approved": {"deployed", "disqualified"},
    "deployed": {"emailed", "disqualified"},
    "emailed": {"replied"},
    "replied": set(),
    "disqualified": set(),
}


@dataclass
class LeadUpsertPayload:
    lead_slug: str
    business_name: str
    vertical: str
    city: str
    state: str
    has_website: bool
    opportunity_score: int
    target: str
    source_payload_json: str
    website_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class LeadQueueDB:
    def __init__(self, db_path: str = DB_PATH_DEFAULT):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.db_path, check_same_thread=False)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=5000")
        con.execute("PRAGMA synchronous=NORMAL")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def init_db(self) -> None:
        with self.tx() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_slug          TEXT    NOT NULL UNIQUE,
                    business_name      TEXT    NOT NULL,
                    vertical           TEXT    NOT NULL,
                    city               TEXT    NOT NULL,
                    state              TEXT    NOT NULL,
                    has_website        INTEGER NOT NULL DEFAULT 0,
                    website_url        TEXT,
                    phone              TEXT,
                    email              TEXT,
                    opportunity_score  INTEGER NOT NULL DEFAULT 0,
                    target             TEXT    NOT NULL,
                    pipeline_status    TEXT    NOT NULL DEFAULT 'scouted',
                    deal_status        TEXT    NOT NULL DEFAULT 'open',
                    deal_value_cents   INTEGER NOT NULL DEFAULT 0,
                    source_payload_json TEXT,
                    created_at         TEXT    NOT NULL DEFAULT (datetime('now')),
                    updated_at         TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS lead_events (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id      INTEGER NOT NULL REFERENCES leads(id),
                    event_type   TEXT    NOT NULL,
                    from_status  TEXT,
                    to_status    TEXT,
                    actor        TEXT    NOT NULL,
                    run_id       TEXT,
                    payload_json TEXT    NOT NULL DEFAULT '{}',
                    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS builds (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id     INTEGER NOT NULL REFERENCES leads(id) UNIQUE,
                    build_dir   TEXT    NOT NULL,
                    entrypoint  TEXT    NOT NULL,
                    artifacts   TEXT    NOT NULL,
                    qa_notes    TEXT,
                    preview_url TEXT,
                    manifest_json TEXT,
                    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS deployments (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id      INTEGER NOT NULL REFERENCES leads(id),
                    provider     TEXT    NOT NULL,
                    success      INTEGER NOT NULL DEFAULT 0,
                    live_url     TEXT,
                    preview_url  TEXT,
                    external_ref TEXT,
                    payload_json TEXT,
                    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS outreach (
                    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id            INTEGER NOT NULL REFERENCES leads(id),
                    to_email           TEXT,
                    subject            TEXT    NOT NULL,
                    body_text          TEXT    NOT NULL,
                    body_html          TEXT,
                    compliance_footer  TEXT,
                    beat_audit_json    TEXT,
                    sent               INTEGER NOT NULL DEFAULT 0,
                    sent_at            TEXT,
                    external_ref       TEXT,
                    payload_json       TEXT,
                    created_at         TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS replies (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id       INTEGER NOT NULL REFERENCES leads(id),
                    channel       TEXT    NOT NULL DEFAULT 'email',
                    subject       TEXT,
                    body_excerpt  TEXT,
                    intent        TEXT,
                    external_ref  TEXT UNIQUE,
                    payload_json  TEXT,
                    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS webhook_receipts (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    source            TEXT    NOT NULL,
                    external_event_id TEXT    NOT NULL,
                    event_type        TEXT    NOT NULL,
                    lead_slug         TEXT,
                    payload_json      TEXT    NOT NULL,
                    status            TEXT    NOT NULL DEFAULT 'received',
                    error_text        TEXT,
                    created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
                    processed_at      TEXT,
                    UNIQUE(source, external_event_id)
                );

                CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(pipeline_status);
                CREATE INDEX IF NOT EXISTS idx_leads_vertical ON leads(vertical);
                CREATE INDEX IF NOT EXISTS idx_events_lead ON lead_events(lead_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_outreach_lead ON outreach(lead_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_deploy_lead ON deployments(lead_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_replies_lead ON replies(lead_id, created_at);

                CREATE TABLE IF NOT EXISTS db_version (
                    version    INTEGER NOT NULL,
                    applied_at TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                """
            )
            v = con.execute("SELECT MAX(version) FROM db_version").fetchone()[0]
            if v is None:
                con.execute("INSERT INTO db_version (version) VALUES (1)")

    def _lead_id(self, con: sqlite3.Connection, lead_slug: str) -> int:
        row = con.execute("SELECT id FROM leads WHERE lead_slug = ?", (lead_slug,)).fetchone()
        if not row:
            raise KeyError(f"Lead not found: {lead_slug}")
        return int(row["id"])

    def _emit_event(
        self,
        con: sqlite3.Connection,
        lead_id: int,
        event_type: str,
        *,
        actor: str = "system",
        from_status: Optional[str] = None,
        to_status: Optional[str] = None,
        run_id: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        con.execute(
            """
            INSERT INTO lead_events(lead_id, event_type, from_status, to_status, actor, run_id, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead_id,
                event_type,
                from_status,
                to_status,
                actor,
                run_id,
                json.dumps(payload or {}, separators=(",", ":"), sort_keys=True),
            ),
        )

    def upsert_lead(self, payload: LeadUpsertPayload, *, actor: str = "orchestrator", run_id: Optional[str] = None) -> dict[str, Any]:
        self.init_db()
        with self.tx() as con:
            existing = con.execute(
                "SELECT * FROM leads WHERE lead_slug = ?",
                (payload.lead_slug,),
            ).fetchone()
            if existing:
                con.execute(
                    """
                    UPDATE leads
                       SET business_name=?, vertical=?, city=?, state=?, has_website=?,
                           website_url=?, phone=?, email=?, opportunity_score=?, target=?,
                           source_payload_json=?, updated_at=datetime('now')
                     WHERE lead_slug=?
                    """,
                    (
                        payload.business_name,
                        payload.vertical,
                        payload.city,
                        payload.state,
                        int(payload.has_website),
                        payload.website_url,
                        payload.phone,
                        payload.email,
                        int(payload.opportunity_score),
                        payload.target,
                        payload.source_payload_json,
                        payload.lead_slug,
                    ),
                )
                lead_id = int(existing["id"])
                self._emit_event(
                    con,
                    lead_id,
                    "lead_refreshed",
                    actor=actor,
                    run_id=run_id,
                    payload={"target": payload.target, "opportunity_score": payload.opportunity_score},
                )
            else:
                cur = con.execute(
                    """
                    INSERT INTO leads(
                        lead_slug, business_name, vertical, city, state, has_website, website_url,
                        phone, email, opportunity_score, target, source_payload_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload.lead_slug,
                        payload.business_name,
                        payload.vertical,
                        payload.city,
                        payload.state,
                        int(payload.has_website),
                        payload.website_url,
                        payload.phone,
                        payload.email,
                        int(payload.opportunity_score),
                        payload.target,
                        payload.source_payload_json,
                    ),
                )
                lead_id = int(cur.lastrowid)
                self._emit_event(
                    con,
                    lead_id,
                    "lead_scouted",
                    actor=actor,
                    from_status=None,
                    to_status="scouted",
                    run_id=run_id,
                    payload={"target": payload.target},
                )

            row = con.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
            return dict(row)

    def set_status(self, lead_slug: str, new_status: str, *, actor: str = "system", run_id: Optional[str] = None, payload: Optional[dict[str, Any]] = None) -> None:
        if new_status not in PIPELINE_STATES:
            raise ValueError(f"Unknown pipeline status: {new_status}")
        with self.tx() as con:
            row = con.execute(
                "SELECT id, pipeline_status FROM leads WHERE lead_slug = ?",
                (lead_slug,),
            ).fetchone()
            if not row:
                raise KeyError(f"Lead not found: {lead_slug}")
            lead_id = int(row["id"])
            cur = str(row["pipeline_status"])
            if cur == new_status:
                return
            allowed = VALID_TRANSITIONS.get(cur, set())
            if new_status not in allowed:
                raise ValueError(f"Illegal pipeline transition {cur} -> {new_status}")
            con.execute(
                "UPDATE leads SET pipeline_status = ?, updated_at = datetime('now') WHERE id = ?",
                (new_status, lead_id),
            )
            self._emit_event(
                con,
                lead_id,
                "status_changed",
                actor=actor,
                from_status=cur,
                to_status=new_status,
                run_id=run_id,
                payload=payload or {},
            )

    def set_deal_status(
        self,
        lead_slug: str,
        deal_status: str,
        *,
        actor: str = "system",
        deal_value_cents: Optional[int] = None,
        run_id: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        if deal_status not in {"open", "won", "lost"}:
            raise ValueError(f"Invalid deal status: {deal_status}")
        with self.tx() as con:
            lead_id = self._lead_id(con, lead_slug)
            if deal_value_cents is None:
                con.execute(
                    "UPDATE leads SET deal_status=?, updated_at=datetime('now') WHERE id=?",
                    (deal_status, lead_id),
                )
            else:
                con.execute(
                    "UPDATE leads SET deal_status=?, deal_value_cents=?, updated_at=datetime('now') WHERE id=?",
                    (deal_status, int(deal_value_cents), lead_id),
                )
            self._emit_event(
                con,
                lead_id,
                "deal_status_changed",
                actor=actor,
                run_id=run_id,
                payload={"deal_status": deal_status, "deal_value_cents": deal_value_cents, **(payload or {})},
            )

    def record_build(
        self,
        lead_slug: str,
        build_dir: str,
        entrypoint: str,
        artifacts: list[str],
        qa_notes: str,
        preview_url: Optional[str],
        *,
        manifest: Optional[dict[str, Any]] = None,
        actor: str = "builder",
        run_id: Optional[str] = None,
    ) -> None:
        with self.tx() as con:
            lead_id = self._lead_id(con, lead_slug)
            con.execute(
                """
                INSERT INTO builds(lead_id, build_dir, entrypoint, artifacts, qa_notes, preview_url, manifest_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(lead_id) DO UPDATE SET
                    build_dir=excluded.build_dir,
                    entrypoint=excluded.entrypoint,
                    artifacts=excluded.artifacts,
                    qa_notes=excluded.qa_notes,
                    preview_url=excluded.preview_url,
                    manifest_json=excluded.manifest_json
                """,
                (
                    lead_id,
                    build_dir,
                    entrypoint,
                    json.dumps(artifacts, separators=(",", ":")),
                    qa_notes,
                    preview_url,
                    json.dumps(manifest or {}, separators=(",", ":"), sort_keys=True),
                ),
            )
            self._emit_event(
                con,
                lead_id,
                "build_recorded",
                actor=actor,
                run_id=run_id,
                payload={"build_dir": build_dir, "entrypoint": entrypoint, "preview_url": preview_url},
            )

    def get_build(self, lead_slug: str) -> Optional[dict[str, Any]]:
        with self.tx() as con:
            row = con.execute(
                """
                SELECT b.*, l.lead_slug
                  FROM builds b
                  JOIN leads l ON l.id = b.lead_id
                 WHERE l.lead_slug = ?
                """,
                (lead_slug,),
            ).fetchone()
            if not row:
                return None
            out = dict(row)
            out["artifacts"] = json.loads(out["artifacts"])
            out["manifest_json"] = json.loads(out["manifest_json"] or "{}")
            return out

    def record_deployment(
        self,
        lead_slug: str,
        provider: str,
        success: bool,
        live_url: Optional[str],
        preview_url: Optional[str],
        external_ref: Optional[str],
        payload: Optional[dict[str, Any]],
        *,
        actor: str = "deployer",
        run_id: Optional[str] = None,
    ) -> int:
        with self.tx() as con:
            lead_id = self._lead_id(con, lead_slug)
            cur = con.execute(
                """
                INSERT INTO deployments(lead_id, provider, success, live_url, preview_url, external_ref, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead_id,
                    provider,
                    int(success),
                    live_url,
                    preview_url,
                    external_ref,
                    json.dumps(payload or {}, separators=(",", ":"), sort_keys=True),
                ),
            )
            self._emit_event(
                con,
                lead_id,
                "deployment_recorded",
                actor=actor,
                run_id=run_id,
                payload={"provider": provider, "success": success, "live_url": live_url, "external_ref": external_ref},
            )
            return int(cur.lastrowid)

    def record_outreach_draft(
        self,
        lead_slug: str,
        subject: str,
        body_text: str,
        *,
        to_email: Optional[str] = None,
        body_html: Optional[str] = None,
        compliance_footer: Optional[str] = None,
        beat_audit: Optional[dict[str, Any]] = None,
        payload: Optional[dict[str, Any]] = None,
        actor: str = "outreach",
        run_id: Optional[str] = None,
    ) -> int:
        with self.tx() as con:
            lead_id = self._lead_id(con, lead_slug)
            cur = con.execute(
                """
                INSERT INTO outreach(
                    lead_id, to_email, subject, body_text, body_html, compliance_footer, beat_audit_json, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead_id,
                    to_email,
                    subject,
                    body_text,
                    body_html,
                    compliance_footer,
                    json.dumps(beat_audit or {}, separators=(",", ":"), sort_keys=True),
                    json.dumps(payload or {}, separators=(",", ":"), sort_keys=True),
                ),
            )
            oid = int(cur.lastrowid)
            self._emit_event(
                con,
                lead_id,
                "outreach_drafted",
                actor=actor,
                run_id=run_id,
                payload={"outreach_id": oid, "to_email": to_email, "subject": subject},
            )
            return oid

    def mark_outreach_sent(self, outreach_id: int, external_ref: Optional[str], *, actor: str = "mailer", run_id: Optional[str] = None, payload: Optional[dict[str, Any]] = None) -> None:
        with self.tx() as con:
            row = con.execute("SELECT id, lead_id FROM outreach WHERE id = ?", (outreach_id,)).fetchone()
            if not row:
                raise KeyError(f"Outreach not found: {outreach_id}")
            con.execute(
                """
                UPDATE outreach
                   SET sent=1, sent_at=datetime('now'), external_ref=COALESCE(?, external_ref)
                 WHERE id=?
                """,
                (external_ref, outreach_id),
            )
            self._emit_event(
                con,
                int(row["lead_id"]),
                "outreach_sent",
                actor=actor,
                run_id=run_id,
                payload={"outreach_id": outreach_id, "external_ref": external_ref, **(payload or {})},
            )

    def get_latest_outreach(self, lead_slug: str) -> Optional[dict[str, Any]]:
        with self.tx() as con:
            row = con.execute(
                """
                SELECT o.*
                  FROM outreach o
                  JOIN leads l ON l.id = o.lead_id
                 WHERE l.lead_slug = ?
                 ORDER BY o.id DESC
                 LIMIT 1
                """,
                (lead_slug,),
            ).fetchone()
            if not row:
                return None
            out = dict(row)
            out["beat_audit_json"] = json.loads(out["beat_audit_json"] or "{}")
            out["payload_json"] = json.loads(out["payload_json"] or "{}")
            return out

    def record_reply(
        self,
        lead_slug: str,
        *,
        subject: Optional[str] = None,
        body_excerpt: Optional[str] = None,
        intent: Optional[str] = None,
        external_ref: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
        actor: str = "webhook",
        run_id: Optional[str] = None,
    ) -> int:
        with self.tx() as con:
            lead_id = self._lead_id(con, lead_slug)
            cur = con.execute(
                """
                INSERT INTO replies(lead_id, subject, body_excerpt, intent, external_ref, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    lead_id,
                    subject,
                    body_excerpt,
                    intent,
                    external_ref,
                    json.dumps(payload or {}, separators=(",", ":"), sort_keys=True),
                ),
            )
            rid = int(cur.lastrowid)
            self._emit_event(
                con,
                lead_id,
                "reply_recorded",
                actor=actor,
                run_id=run_id,
                payload={"reply_id": rid, "intent": intent, "external_ref": external_ref},
            )
            return rid

    def reserve_webhook_event(self, source: str, external_event_id: str, event_type: str, lead_slug: Optional[str], payload: dict[str, Any]) -> bool:
        with self.tx() as con:
            try:
                con.execute(
                    """
                    INSERT INTO webhook_receipts(source, external_event_id, event_type, lead_slug, payload_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        source,
                        external_event_id,
                        event_type,
                        lead_slug,
                        json.dumps(payload, separators=(",", ":"), sort_keys=True),
                    ),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def finalize_webhook_event(self, source: str, external_event_id: str, *, status: str, error_text: Optional[str] = None) -> None:
        with self.tx() as con:
            con.execute(
                """
                UPDATE webhook_receipts
                   SET status=?, error_text=?, processed_at=datetime('now')
                 WHERE source=? AND external_event_id=?
                """,
                (status, error_text, source, external_event_id),
            )

    def get_lead(self, lead_slug: str) -> dict[str, Any]:
        with self.tx() as con:
            row = con.execute("SELECT * FROM leads WHERE lead_slug = ?", (lead_slug,)).fetchone()
            if not row:
                raise KeyError(f"Lead not found: {lead_slug}")
            return dict(row)

    def funnel_counts(self) -> dict[str, int]:
        with self.tx() as con:
            rows = con.execute("SELECT pipeline_status, COUNT(*) AS n FROM leads GROUP BY pipeline_status").fetchall()
        counts = {s: 0 for s in PIPELINE_STATES}
        for r in rows:
            counts[str(r["pipeline_status"])] = int(r["n"])
        return counts

    def conversion_by_vertical(self) -> list[dict[str, Any]]:
        with self.tx() as con:
            rows = con.execute(
                """
                SELECT
                    vertical,
                    COUNT(*) AS total,
                    SUM(CASE WHEN pipeline_status IN ('qualified','built','approved','deployed','emailed','replied') THEN 1 ELSE 0 END) AS qualified_count,
                    SUM(CASE WHEN pipeline_status IN ('emailed','replied') THEN 1 ELSE 0 END) AS emailed_count,
                    SUM(CASE WHEN pipeline_status = 'replied' THEN 1 ELSE 0 END) AS replied_count,
                    SUM(CASE WHEN deal_status = 'won' THEN 1 ELSE 0 END) AS won_count,
                    AVG(CASE WHEN deal_status='won' THEN deal_value_cents END) AS avg_won_value_cents
                FROM leads
                GROUP BY vertical
                ORDER BY total DESC, vertical ASC
                """
            ).fetchall()

        out: list[dict[str, Any]] = []
        for r in rows:
            total = int(r["total"])
            qualified = int(r["qualified_count"] or 0)
            emailed = int(r["emailed_count"] or 0)
            replied = int(r["replied_count"] or 0)
            won = int(r["won_count"] or 0)
            out.append(
                {
                    "vertical": str(r["vertical"]),
                    "total": total,
                    "qualified_count": qualified,
                    "emailed_count": emailed,
                    "replied_count": replied,
                    "won_count": won,
                    "qualification_rate": round(qualified / total, 4) if total else 0.0,
                    "reply_rate": round(replied / emailed, 4) if emailed else 0.0,
                    "close_rate": round(won / replied, 4) if replied else 0.0,
                    "avg_won_value_cents": int(r["avg_won_value_cents"] or 0),
                }
            )
        return out

    def recent_leads(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.tx() as con:
            rows = con.execute(
                """
                SELECT lead_slug, business_name, vertical, city, state, pipeline_status, deal_status,
                       deal_value_cents, opportunity_score, email, phone, website_url, target,
                       created_at, updated_at
                FROM leads
                ORDER BY datetime(updated_at) DESC, id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [dict(r) for r in rows]

    def lead_timeline(self, lead_slug: str) -> list[dict[str, Any]]:
        with self.tx() as con:
            lid = self._lead_id(con, lead_slug)
            rows = con.execute(
                """
                SELECT event_type, from_status, to_status, actor, run_id, payload_json, created_at
                  FROM lead_events
                 WHERE lead_id = ?
                 ORDER BY id ASC
                """,
                (lid,),
            ).fetchall()
        events = []
        for r in rows:
            d = dict(r)
            d["payload_json"] = json.loads(d["payload_json"] or "{}")
            events.append(d)
        return events

    def economics_summary(self) -> dict[str, Any]:
        with self.tx() as con:
            row = con.execute(
                """
                SELECT
                    COUNT(*) AS total_leads,
                    SUM(CASE WHEN deal_status='won' THEN 1 ELSE 0 END) AS won_deals,
                    SUM(CASE WHEN deal_status='lost' THEN 1 ELSE 0 END) AS lost_deals,
                    SUM(CASE WHEN deal_status='won' THEN deal_value_cents ELSE 0 END) AS won_revenue_cents
                FROM leads
                """
            ).fetchone()
        total = int(row["total_leads"] or 0)
        won = int(row["won_deals"] or 0)
        lost = int(row["lost_deals"] or 0)
        revenue = int(row["won_revenue_cents"] or 0)
        reply_count = self.funnel_counts().get("replied", 0)
        close_rate = round(won / reply_count, 4) if reply_count else 0.0
        return {
            "total_leads": total,
            "won_deals": won,
            "lost_deals": lost,
            "won_revenue_cents": revenue,
            "avg_won_deal_cents": int(revenue / won) if won else 0,
            "reply_to_close_rate": close_rate,
        }

    def beat_compliance_summary(self) -> dict[str, Any]:
        required = ["pattern_break", "cost_of_inaction", "belief_shift", "mechanism", "proof_unit", "offer", "action"]
        with self.tx() as con:
            rows = con.execute("SELECT beat_audit_json FROM outreach").fetchall()
        total = len(rows)
        field_counts = {k: 0 for k in required}
        complete = 0
        for r in rows:
            obj = json.loads(r["beat_audit_json"] or "{}")
            all_present = True
            for k in required:
                v = obj.get(k)
                ok = isinstance(v, str) and bool(v.strip())
                if ok:
                    field_counts[k] += 1
                all_present &= ok
            if all_present:
                complete += 1
        rates = {k: round((field_counts[k] / total), 4) if total else 0.0 for k in required}
        return {"total_outreach_drafts": total, "fully_compliant": complete, "field_presence_rate": rates}

    def apply_webhook_event(self, source: str, payload: dict[str, Any]) -> dict[str, Any]:
        event_id = str(payload["event_id"])
        event_type = str(payload["event_type"])
        lead_slug = payload.get("lead_slug")
        if not self.reserve_webhook_event(source, event_id, event_type, lead_slug, payload):
            return {"duplicate": True, "event_id": event_id}

        try:
            if event_type == "deployment.succeeded":
                self.record_deployment(
                    str(lead_slug),
                    provider=str(payload.get("provider", source)),
                    success=True,
                    live_url=payload.get("live_url"),
                    preview_url=payload.get("preview_url"),
                    external_ref=payload.get("external_ref") or event_id,
                    payload=payload,
                    actor=f"webhook:{source}",
                )
                self.set_status(str(lead_slug), "deployed", actor=f"webhook:{source}", payload={"event_id": event_id})
            elif event_type == "deployment.failed":
                self.record_deployment(
                    str(lead_slug),
                    provider=str(payload.get("provider", source)),
                    success=False,
                    live_url=None,
                    preview_url=payload.get("preview_url"),
                    external_ref=payload.get("external_ref") or event_id,
                    payload=payload,
                    actor=f"webhook:{source}",
                )
            elif event_type == "outreach.sent":
                outreach_id = int(payload["outreach_id"])
                self.mark_outreach_sent(outreach_id, payload.get("external_ref") or event_id, actor=f"webhook:{source}", payload=payload)
                self.set_status(str(lead_slug), "emailed", actor=f"webhook:{source}", payload={"event_id": event_id, "outreach_id": outreach_id})
            elif event_type == "lead.replied":
                self.record_reply(
                    str(lead_slug),
                    subject=payload.get("subject"),
                    body_excerpt=payload.get("body_excerpt"),
                    intent=payload.get("intent"),
                    external_ref=payload.get("external_ref") or event_id,
                    payload=payload,
                    actor=f"webhook:{source}",
                )
                self.set_status(str(lead_slug), "replied", actor=f"webhook:{source}", payload={"event_id": event_id})
            elif event_type == "deal.won":
                self.set_deal_status(
                    str(lead_slug),
                    "won",
                    deal_value_cents=int(payload.get("deal_value_cents") or 0),
                    actor=f"webhook:{source}",
                    payload=payload,
                )
            elif event_type == "deal.lost":
                self.set_deal_status(str(lead_slug), "lost", actor=f"webhook:{source}", payload=payload)
            else:
                raise ValueError(f"Unsupported webhook event_type: {event_type}")
            self.finalize_webhook_event(source, event_id, status="processed")
            return {"ok": True, "event_id": event_id}
        except Exception as exc:
            self.finalize_webhook_event(source, event_id, status="failed", error_text=str(exc))
            raise

    def snapshot(self) -> dict[str, Any]:
        return {
            "funnel": self.funnel_counts(),
            "verticals": self.conversion_by_vertical(),
            "economics": self.economics_summary(),
            "beat_compliance": self.beat_compliance_summary(),
        }


def _cli() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")

    p_snapshot = sub.add_parser("snapshot")
    p_snapshot.add_argument("--db", default=DB_PATH_DEFAULT)

    args = parser.parse_args()
    db = LeadQueueDB(getattr(args, "db", DB_PATH_DEFAULT))
    if args.cmd == "init":
        db.init_db()
        print(f"initialized {db.db_path}")
    elif args.cmd == "snapshot":
        db.init_db()
        print(json.dumps(db.snapshot(), indent=2))


if __name__ == "__main__":
    _cli()
