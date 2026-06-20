"""
Prospect Engine — scored lead pipeline with outreach templates and tracking.

Stores prospects in SQLite with scoring, generates personalized outreach,
and tracks pipeline stages. Integrates with the agents-cli for autonomous
prospecting runs.
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Prospect:
    """A scored sales prospect."""
    id: int | None = None
    company_name: str = ""
    website: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    trade: str = ""          # hvac, plumbing, electrical, freight, saas
    city: str = ""
    state: str = ""
    score: float = 0.0       # 0-100
    stage: str = "new"       # new, contacted, qualified, negotiation, closed_won, closed_lost, nurture
    pain_points: str = ""    # JSON list of pain points
    outreach_template: str = ""
    notes: str = ""
    estimated_value: float = 0.0
    created_at: str = ""
    updated_at: str = ""
    last_contact: str = ""


@dataclass
class OutreachTemplate:
    """A reusable outreach template per vertical/stage."""
    id: int | None = None
    name: str = ""
    vertical: str = ""       # hvac, freight, saas
    channel: str = ""        # sms, email
    stage: str = ""          # first_contact, followup_1, followup_2, followup_3
    subject: str = ""        # For email
    body: str = ""
    max_length: int = 160    # SMS limit


class ProspectEngine:
    """
    SQLite-backed prospect pipeline.

    Operations:
    - add_prospect: Insert a new scored lead
    - score_prospect: Calculate fit score (0-100) from attributes
    - get_prospects: Filter by stage, score, trade
    - get_hot_prospects: Score >= 80
    - get_warm_prospects: Score 60-79
    - get_cold_prospects: Score 40-59
    - advance_stage: Move prospect to next pipeline stage
    - generate_outreach: Pick template + personalize for prospect
    - get_pipeline_summary: Counts and values per stage
    - get_templates: List outreach templates for vertical/channel
    """

    # Scoring weights
    SCORE_WEIGHTS = {
        "no_website": 30,         # No website = prime target
        "has_reviews_no_site": 20, # Reviews but no good website
        "high_rating": 15,         # 4.5+ stars = successful business
        "operational": 10,         # Active business
        "funded": 10,              # Has funding = can pay
        "growing": 10,             # Hiring/growth signals
        "ai_relevance": 10,        # In AI-hot vertical
        "geography": 5,            # In priority market
        "contact_available": 5,    # Have direct contact
    }

    # Stage progression
    STAGES = ["new", "contacted", "qualified", "negotiation", "closed_won", "closed_lost", "nurture"]

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.environ.get(
            "PROSPECT_DB", os.path.expanduser("~/.local/share/reliantai/prospects.db")
        )
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        self._seed_templates()

    def _get_conn(self):
        """Get a new SQLite connection. Caller is responsible for closing."""
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prospects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL DEFAULT '',
                    website TEXT NOT NULL DEFAULT '',
                    contact_name TEXT NOT NULL DEFAULT '',
                    contact_email TEXT NOT NULL DEFAULT '',
                    contact_phone TEXT NOT NULL DEFAULT '',
                    trade TEXT NOT NULL DEFAULT '',
                    city TEXT NOT NULL DEFAULT '',
                    state TEXT NOT NULL DEFAULT '',
                    score REAL NOT NULL DEFAULT 0,
                    stage TEXT NOT NULL DEFAULT 'new',
                    pain_points TEXT NOT NULL DEFAULT '[]',
                    outreach_template TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    estimated_value REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT '',
                    last_contact TEXT NOT NULL DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS outreach_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    vertical TEXT NOT NULL DEFAULT '',
                    channel TEXT NOT NULL DEFAULT 'sms',
                    stage TEXT NOT NULL DEFAULT 'first_contact',
                    subject TEXT NOT NULL DEFAULT '',
                    body TEXT NOT NULL DEFAULT '',
                    max_length INTEGER NOT NULL DEFAULT 160
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS outreach_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prospect_id INTEGER NOT NULL,
                    template_id INTEGER,
                    channel TEXT NOT NULL DEFAULT 'sms',
                    body TEXT NOT NULL DEFAULT '',
                    sent_at TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'draft',
                    FOREIGN KEY (prospect_id) REFERENCES prospects(id)
                )
            """)
            conn.commit()

    def _seed_templates(self):
        """Seed default outreach templates if none exist."""
        with sqlite3.connect(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM outreach_templates").fetchone()[0]
            if count > 0:
                return

            templates = [
                # HVAC first contact
                ("hvac_sms_1", "hvac", "sms", "first_contact", "",
                 "Hi {company}! We built a free {trade} website for {city}. See it: {url}", 160),
                ("hvac_email_1", "hvac", "email", "first_contact",
                 "{company} — Your free website is ready",
                 "Hi {contact_name},\n\nWe built a free website for {company} in {city}.\n\n{url}\n\nCheck it out and let me know if you'd like to make it yours.\n\n— Douglas Mitchell\nReliantAI", 0),

                # HVAC followups
                ("hvac_sms_2", "hvac", "sms", "followup_1", "",
                 "Hey {company} — just checking if you saw your free site: {url}. Want me to add anything?", 160),
                ("hvac_sms_3", "hvac", "sms", "followup_2", "",
                 "{company}, your site is still live: {url}. Happy to add reviews, services, or take it down.", 160),
                ("hvac_sms_4", "hvac", "sms", "followup_3", "",
                 "Last follow-up, {company}. Your site: {url}. Just reply if you want it!", 160),

                # Freight/Logistics
                ("freight_email_1", "freight", "email", "first_contact",
                 "AI document processing for {company}",
                 "Hi {contact_name},\n\nI saw {company} is in {city} and thought you might benefit from what we've built for freight/logistics companies.\n\nWe automate BOL processing, invoice validation, and customs docs — typically saving 60-80% of manual data entry time.\n\nWorth a 15-min call?\n\n— Douglas Mitchell\nReliantAI", 0),

                # SaaS
                ("saas_email_1", "saas", "email", "first_contact",
                 "AI agent development for {company}",
                 "Hi {contact_name},\n\nNoticed {company} is building in the AI space. We specialize in shipping production AI agent systems — multi-agent orchestration, workflow automation, and integration.\n\nIf you need AI agent development help, I'd love to chat.\n\n— Douglas Mitchell\nReliantAI", 0),
            ]

            for t in templates:
                conn.execute(
                    "INSERT INTO outreach_templates (name, vertical, channel, stage, subject, body, max_length) VALUES (?,?,?,?,?,?,?)",
                    t
                )
            conn.commit()

    def score_prospect(self, prospect: Prospect) -> float:
        """Calculate fit score (0-100) from prospect attributes."""
        score = 0.0

        # No website = prime target
        if not prospect.website or len(prospect.website) < 5:
            score += self.SCORE_WEIGHTS["no_website"]

        # Has reviews but no website
        pain_points = prospect.pain_points or ""
        if "has_reviews" in pain_points:
            score += self.SCORE_WEIGHTS["has_reviews_no_site"]

        # High rating businesses
        if "high_rating" in pain_points:
            score += self.SCORE_WEIGHTS["high_rating"]

        # Funded companies can pay
        if "funded" in pain_points:
            score += self.SCORE_WEIGHTS["funded"]

        # Growing companies (hiring/revenue signals)
        if "growing" in pain_points:
            score += self.SCORE_WEIGHTS["growing"]

        # AI-hot verticals
        hot_trades = {"hvac", "plumbing", "electrical", "freight", "saas", "logistics"}
        if prospect.trade.lower() in hot_trades:
            score += self.SCORE_WEIGHTS["ai_relevance"]

        # Priority geographies
        priority_states = {"TX", "FL", "CA", "AZ", "NY", "NC", "GA", "CO", "WA", "TN"}
        if prospect.state.upper() in priority_states:
            score += self.SCORE_WEIGHTS["geography"]

        # Contact available
        if prospect.contact_email or prospect.contact_phone:
            score += self.SCORE_WEIGHTS["contact_available"]

        # Operational
        if "operational" in pain_points:
            score += self.SCORE_WEIGHTS["operational"]

        return min(score, 100.0)

    def add_prospect(self, prospect: Prospect) -> int:
        """Insert a prospect. Returns the new ID."""
        now = datetime.now(timezone.utc).isoformat()
        prospect.score = self.score_prospect(prospect)
        prospect.created_at = now
        prospect.updated_at = now

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """INSERT INTO prospects
                   (company_name, website, contact_name, contact_email, contact_phone,
                    trade, city, state, score, stage, pain_points, outreach_template,
                    notes, estimated_value, created_at, updated_at, last_contact)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (prospect.company_name, prospect.website, prospect.contact_name,
                 prospect.contact_email, prospect.contact_phone, prospect.trade,
                 prospect.city, prospect.state, prospect.score, prospect.stage,
                 prospect.pain_points, prospect.outreach_template, prospect.notes,
                 prospect.estimated_value, prospect.created_at, prospect.updated_at,
                 prospect.last_contact),
            )
            conn.commit()
            return cur.lastrowid

    def get_prospects(self, stage: str | None = None, trade: str | None = None,
                      min_score: float = 0, limit: int = 50) -> list[Prospect]:
        """Filter prospects by stage, trade, min score."""
        query = "SELECT * FROM prospects WHERE score >= ?"
        params: list[Any] = [min_score]

        if stage:
            query += " AND stage = ?"
            params.append(stage)
        if trade:
            query += " AND trade = ?"
            params.append(trade)

        query += " ORDER BY score DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_prospect(r) for r in rows]

    def get_hot_prospects(self) -> list[Prospect]:
        return self.get_prospects(min_score=80)

    def get_warm_prospects(self) -> list[Prospect]:
        return self.get_prospects(min_score=60, limit=100)

    def get_cold_prospects(self) -> list[Prospect]:
        return self.get_prospects(min_score=40, limit=100)

    def advance_stage(self, prospect_id: int, new_stage: str | None = None) -> None:
        """Move prospect to next stage or specified stage."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT stage FROM prospects WHERE id = ?", (prospect_id,)).fetchone()
            if not row:
                return

            current = row[0]
            if new_stage:
                next_stage = new_stage
            else:
                idx = self.STAGES.index(current) if current in self.STAGES else 0
                next_stage = self.STAGES[min(idx + 1, len(self.STAGES) - 1)]

            conn.execute(
                "UPDATE prospects SET stage = ?, updated_at = ? WHERE id = ?",
                (next_stage, datetime.now(timezone.utc).isoformat(), prospect_id),
            )
            conn.commit()

    def generate_outreach(self, prospect_id: int, stage: str = "first_contact") -> str | None:
        """Generate personalized outreach for a prospect."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            p = conn.execute("SELECT * FROM prospects WHERE id = ?", (prospect_id,)).fetchone()
            if not p:
                return None

            template = conn.execute(
                "SELECT * FROM outreach_templates WHERE vertical = ? AND stage = ? LIMIT 1",
                (p["trade"], stage),
            ).fetchone()

        if not template:
            return None

        body = template["body"]
        # Personalize
        preview_url = f"https://preview.reliantai.org/{p['city'].lower().replace(' ', '-')}-{p['trade']}"
        replacements = {
            "{company}": p["company_name"] or "there",
            "{contact_name}": p["contact_name"] or "there",
            "{trade}": p["trade"] or "services",
            "{city}": p["city"] or "your area",
            "{url}": preview_url,
        }
        for key, val in replacements.items():
            body = body.replace(key, val)

        # Enforce length limit
        max_len = template["max_length"]
        if max_len > 0 and len(body) > max_len:
            body = body[:max_len - 3] + "..."

        # Log the outreach
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO outreach_log (prospect_id, template_id, channel, body, sent_at, status) VALUES (?,?,?,?,?,?)",
                (prospect_id, template["id"], template["channel"], body, now, "draft"),
            )
            conn.execute(
                "UPDATE prospects SET last_contact = ?, outreach_template = ?, updated_at = ? WHERE id = ?",
                (now, template["name"], now, prospect_id),
            )
            conn.commit()

        return body

    def get_templates(self, vertical: str | None = None, channel: str | None = None) -> list[dict]:
        query = "SELECT * FROM outreach_templates WHERE 1=1"
        params: list[Any] = []
        if vertical:
            query += " AND vertical = ?"
            params.append(vertical)
        if channel:
            query += " AND channel = ?"
            params.append(channel)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_pipeline_summary(self) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            stages = {}
            for stage in self.STAGES:
                row = conn.execute(
                    "SELECT COUNT(*), COALESCE(SUM(estimated_value), 0) FROM prospects WHERE stage = ?",
                    (stage,),
                ).fetchone()
                stages[stage] = {"count": row[0], "value": row[1]}

            total = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(estimated_value), 0), COALESCE(AVG(score), 0) FROM prospects"
            ).fetchone()

        return {
            "total_prospects": total[0],
            "total_value": total[1],
            "avg_score": round(total[2], 1),
            "by_stage": stages,
        }

    def _row_to_prospect(self, row: sqlite3.Row) -> Prospect:
        return Prospect(
            id=row["id"],
            company_name=row["company_name"],
            website=row["website"],
            contact_name=row["contact_name"],
            contact_email=row["contact_email"],
            contact_phone=row["contact_phone"],
            trade=row["trade"],
            city=row["city"],
            state=row["state"],
            score=row["score"],
            stage=row["stage"],
            pain_points=row["pain_points"],
            outreach_template=row["outreach_template"],
            notes=row["notes"],
            estimated_value=row["estimated_value"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_contact=row["last_contact"],
        )

    def seed_demo_prospects(self) -> list[int]:
        """Seed demo prospects for testing. Returns list of IDs."""
        demos = [
            Prospect(company_name="Apex HVAC Solutions", trade="hvac", city="Houston", state="TX",
                     pain_points='["no_website","high_rating","operational","has_reviews"]',
                     estimated_value=25000, contact_email="owner@apexhvac.example"),
            Prospect(company_name="Bill Joplin's Air Conditioning", trade="hvac", city="Dallas", state="TX",
                     pain_points='["no_website","high_rating","operational","has_reviews"]',
                     estimated_value=35000, contact_email="billjoplin@example"),
            Prospect(company_name="Pacific Heating & Cooling", trade="hvac", city="Phoenix", state="AZ",
                     pain_points='["no_website","high_rating","operational","funded"]',
                     estimated_value=40000, contact_email="info@pacifichvac.example"),
            Prospect(company_name="Vital Comfort HVAC", trade="hvac", city="Austin", state="TX",
                     pain_points='["no_website","operational"]',
                     estimated_value=20000),
            Prospect(company_name="ATS Air Systems", trade="hvac", city="Denver", state="CO",
                     pain_points='["no_website","operational"]',
                     estimated_value=22000),
            Prospect(company_name="FreightFlow Logistics", trade="freight", city="Atlanta", state="GA",
                     pain_points='["operational","funded","ai_relevance"]',
                     estimated_value=75000, contact_email="ops@freightflow.example"),
            Prospect(company_name="SwiftShip Brokers", trade="freight", city="Charlotte", state="NC",
                     pain_points='["operational"]',
                     estimated_value=55000),
            Prospect(company_name="CloudScale SaaS", trade="saas", city="San Francisco", state="CA",
                     pain_points='["funded","growing","ai_relevance"]',
                     estimated_value=85000, contact_email="team@cloudscale.example"),
            Prospect(company_name="DataPipe Analytics", trade="saas", city="New York", state="NY",
                     pain_points='["operational","ai_relevance"]',
                     estimated_value=65000),
            Prospect(company_name="Local Plumbing Co", trade="plumbing", city="Nashville", state="TN",
                     pain_points='["no_website","operational"]',
                     estimated_value=18000),
        ]
        ids = []
        for p in demos:
            ids.append(self.add_prospect(p))
        return ids
