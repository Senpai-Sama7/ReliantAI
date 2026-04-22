"""
FinOps360 - Financial Operations & Cloud Cost Management Service
Real, working implementation for cloud cost tracking, budgeting, and optimization
"""

import os
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException, Header, BackgroundTasks, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import sys
import os
# Resolve workspace shared code
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shared")))
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

app = FastAPI(title="FinOps360", version="1.0.0")

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
        db_url = os.environ.get("DATABASE_URL", "postgresql://localhost/finops360")
        _db_pool = psycopg2.pool.ThreadedConnectionPool(1, 10, db_url)
    return _db_pool

def init_db():
    """Initialize database tables"""
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cloud_accounts (
                    id SERIAL PRIMARY KEY,
                    provider TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    account_name TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(provider, account_id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cost_data (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER REFERENCES cloud_accounts(id),
                    service_name TEXT NOT NULL,
                    resource_id TEXT,
                    region TEXT,
                    cost_amount DECIMAL(12, 4) NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    usage_date DATE NOT NULL,
                    tags JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    account_id INTEGER REFERENCES cloud_accounts(id),
                    monthly_limit DECIMAL(12, 2) NOT NULL,
                    current_spend DECIMAL(12, 2) DEFAULT 0,
                    alert_threshold INTEGER DEFAULT 80,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cost_alerts (
                    id SERIAL PRIMARY KEY,
                    budget_id INTEGER REFERENCES budgets(id),
                    alert_type TEXT,
                    message TEXT,
                    severity TEXT,
                    is_acknowledged BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cost_optimization_recommendations (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER REFERENCES cloud_accounts(id),
                    resource_id TEXT,
                    service_name TEXT,
                    recommendation_type TEXT,
                    potential_savings DECIMAL(12, 2),
                    description TEXT,
                    is_implemented BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS resource_utilization (
                    id SERIAL PRIMARY KEY,
                    account_id INTEGER REFERENCES cloud_accounts(id),
                    resource_id TEXT NOT NULL,
                    service_name TEXT,
                    metric_name TEXT,
                    metric_value DECIMAL(10, 4),
                    recorded_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Insert sample accounts if none exist
            cur.execute("SELECT COUNT(*) FROM cloud_accounts")
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO cloud_accounts (provider, account_id, account_name) VALUES
                    ('aws', '123456789012', 'Production AWS'),
                    ('azure', 'prod-sub-001', 'Production Azure'),
                    ('gcp', 'my-project-123456', 'Production GCP')
                """)
        conn.commit()
    finally:
        pool.putconn(conn)

# Models
class AccountCreate(BaseModel):
    provider: str = Field(..., regex="^(aws|azure|gcp)$")
    account_id: str
    account_name: str

class CostDataSubmit(BaseModel):
    account_id: int
    service_name: str
    resource_id: Optional[str] = None
    region: Optional[str] = None
    cost_amount: float
    currency: str = "USD"
    usage_date: str
    tags: Dict[str, Any] = Field(default_factory=dict)

class BudgetCreate(BaseModel):
    name: str
    account_id: int
    monthly_limit: float
    alert_threshold: int = 80

class AlertAcknowledge(BaseModel):
    alert_id: int

# API Key validation is now handled by shared security middleware
# dependency 'verify_api_key' imported from shared.security_middleware

# Routes
@app.on_event("startup")
async def startup():
    init_db()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "finops360", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/accounts")
async def create_account(data: AccountCreate, api_key: str = Depends(verify_api_key)):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO cloud_accounts (provider, account_id, account_name) VALUES (%s, %s, %s) RETURNING id",
                (data.provider, data.account_id, data.account_name)
            )
            account_id = cur.fetchone()[0]
        conn.commit()
        return {"id": account_id, "created": True}
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Account already exists")
    finally:
        pool.putconn(conn)

@app.get("/accounts")
async def list_accounts():
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM cloud_accounts WHERE is_active = TRUE ORDER BY provider, account_name")
            accounts = cur.fetchall()
        return {"accounts": [dict(row) for row in accounts]}
    finally:
        pool.putconn(conn)

@app.post("/costs")
async def submit_cost(data: CostDataSubmit, api_key: str = Depends(verify_api_key)):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO cost_data 
                   (account_id, service_name, resource_id, region, cost_amount, currency, usage_date, tags) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (data.account_id, data.service_name, data.resource_id, data.region, 
                 data.cost_amount, data.currency, data.usage_date, json.dumps(data.tags))
            )
            cost_id = cur.fetchone()[0]
        conn.commit()
        return {"id": cost_id, "submitted": True}
    finally:
        pool.putconn(conn)

@app.get("/costs")
async def get_costs(
    account_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: str = "service"
):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if group_by == "service" and account_id:
                cur.execute("""
                    SELECT service_name, SUM(cost_amount) as total_cost
                    FROM cost_data
                    WHERE account_id = %s AND usage_date BETWEEN %s AND %s
                    GROUP BY service_name
                    ORDER BY total_cost DESC
                """, (account_id, start_date or '2024-01-01', end_date or datetime.now().strftime('%Y-%m-%d')))
                results = [dict(row) for row in cur.fetchall()]
            elif group_by == "daily" and account_id:
                cur.execute("""
                    SELECT usage_date, SUM(cost_amount) as daily_cost
                    FROM cost_data
                    WHERE account_id = %s AND usage_date BETWEEN %s AND %s
                    GROUP BY usage_date
                    ORDER BY usage_date
                """, (account_id, start_date or '2024-01-01', end_date or datetime.now().strftime('%Y-%m-%d')))
                results = [dict(row) for row in cur.fetchall()]
            else:
                cur.execute("""
                    SELECT * FROM cost_data
                    WHERE usage_date BETWEEN %s AND %s
                    ORDER BY usage_date DESC
                    LIMIT 100
                """, (start_date or '2024-01-01', end_date or datetime.now().strftime('%Y-%m-%d')))
                results = [dict(row) for row in cur.fetchall()]
        return {"costs": results}
    finally:
        pool.putconn(conn)

@app.post("/budgets")
async def create_budget(data: BudgetCreate, api_key: str = Depends(verify_api_key)):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO budgets (name, account_id, monthly_limit, alert_threshold) VALUES (%s, %s, %s, %s) RETURNING id",
                (data.name, data.account_id, data.monthly_limit, data.alert_threshold)
            )
            budget_id = cur.fetchone()[0]
        conn.commit()
        return {"id": budget_id, "created": True}
    finally:
        pool.putconn(conn)

@app.get("/budgets")
async def list_budgets():
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT b.*, ca.provider, ca.account_name
                FROM budgets b
                JOIN cloud_accounts ca ON b.account_id = ca.id
                WHERE b.is_active = TRUE
                ORDER BY b.created_at DESC
            """)
            budgets = cur.fetchall()
        return {"budgets": [dict(row) for row in budgets]}
    finally:
        pool.putconn(conn)

@app.get("/budgets/{budget_id}/status")
async def get_budget_status(budget_id: int):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get budget details
            cur.execute("SELECT * FROM budgets WHERE id = %s", (budget_id,))
            budget = dict(cur.fetchone())
            
            # Calculate current month spend
            cur.execute("""
                SELECT COALESCE(SUM(cost_amount), 0) as month_spend
                FROM cost_data
                WHERE account_id = %s 
                AND usage_date >= DATE_TRUNC('month', CURRENT_DATE)
            """, (budget["account_id"],))
            month_spend = cur.fetchone()[0]
            
            # Update current spend
            cur.execute(
                "UPDATE budgets SET current_spend = %s WHERE id = %s",
                (month_spend, budget_id)
            )
            conn.commit()
            
            utilization_pct = (month_spend / budget["monthly_limit"]) * 100 if budget["monthly_limit"] > 0 else 0
            
            return {
                "budget_id": budget_id,
                "name": budget["name"],
                "monthly_limit": float(budget["monthly_limit"]),
                "current_spend": float(month_spend),
                "remaining": float(budget["monthly_limit"] - month_spend),
                "utilization_percent": round(utilization_pct, 2),
                "alert_threshold": budget["alert_threshold"],
                "alert_triggered": utilization_pct >= budget["alert_threshold"]
            }
    finally:
        pool.putconn(conn)

@app.post("/recommendations/generate")
async def generate_recommendations(account_id: int, api_key: str = Depends(verify_api_key)):
    """Generate cost optimization recommendations based on utilization data"""
    pool = get_db_pool()
    conn = pool.getconn()
    recommendations = []
    
    try:
        with conn.cursor() as cur:
            # Check for idle resources (low utilization)
            cur.execute("""
                SELECT resource_id, service_name, AVG(metric_value) as avg_utilization
                FROM resource_utilization
                WHERE account_id = %s AND recorded_at > NOW() - INTERVAL '7 days'
                GROUP BY resource_id, service_name
                HAVING AVG(metric_value) < 20
            """, (account_id,))
            
            for row in cur.fetchall():
                rec = {
                    "account_id": account_id,
                    "resource_id": row["resource_id"],
                    "service_name": row["service_name"],
                    "recommendation_type": "rightsize",
                    "potential_savings": 50.00,  # Placeholder calculation
                    "description": f"Resource has {row['avg_utilization']:.1f}% average utilization - consider downsizing"
                }
                cur.execute(
                    """INSERT INTO cost_optimization_recommendations 
                       (account_id, resource_id, service_name, recommendation_type, potential_savings, description)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (rec["account_id"], rec["resource_id"], rec["service_name"],
                     rec["recommendation_type"], rec["potential_savings"], rec["description"])
                )
                recommendations.append(rec)
            
            conn.commit()
        return {"recommendations": recommendations, "generated": len(recommendations)}
    finally:
        pool.putconn(conn)

@app.get("/recommendations")
async def list_recommendations(account_id: Optional[int] = None, is_implemented: Optional[bool] = None):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = "SELECT * FROM cost_optimization_recommendations WHERE 1=1"
            params = []
            if account_id:
                query += " AND account_id = %s"
                params.append(account_id)
            if is_implemented is not None:
                query += " AND is_implemented = %s"
                params.append(is_implemented)
            query += " ORDER BY potential_savings DESC"
            
            cur.execute(query, params)
            recommendations = [dict(row) for row in cur.fetchall()]
        return {"recommendations": recommendations}
    finally:
        pool.putconn(conn)

@app.post("/recommendations/{rec_id}/implement")
async def implement_recommendation(rec_id: int, api_key: str = Depends(verify_api_key)):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE cost_optimization_recommendations SET is_implemented = TRUE WHERE id = %s",
                (rec_id,)
            )
        conn.commit()
        return {"id": rec_id, "implemented": True}
    finally:
        pool.putconn(conn)

@app.get("/alerts")
async def get_alerts(is_acknowledged: Optional[bool] = False):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT a.*, b.name as budget_name
                FROM cost_alerts a
                JOIN budgets b ON a.budget_id = b.id
                WHERE a.is_acknowledged = %s
                ORDER BY a.created_at DESC
            """, (is_acknowledged,))
            alerts = [dict(row) for row in cur.fetchall()]
        return {"alerts": alerts}
    finally:
        pool.putconn(conn)

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, api_key: str = Depends(verify_api_key)):
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE cost_alerts SET is_acknowledged = TRUE WHERE id = %s",
                (alert_id,)
            )
        conn.commit()
        return {"id": alert_id, "acknowledged": True}
    finally:
        pool.putconn(conn)

@app.get("/dashboard")
async def finops_dashboard():
    """Real-time FinOps dashboard data"""
    pool = get_db_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            # Total spend this month
            cur.execute("""
                SELECT COALESCE(SUM(cost_amount), 0) as month_spend
                FROM cost_data
                WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE)
            """)
            month_spend = float(cur.fetchone()[0])
            
            # Total spend last month for comparison
            cur.execute("""
                SELECT COALESCE(SUM(cost_amount), 0) as last_month_spend
                FROM cost_data
                WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
                AND usage_date < DATE_TRUNC('month', CURRENT_DATE)
            """)
            last_month_spend = float(cur.fetchone()[0])
            
            # Account count
            cur.execute("SELECT COUNT(*) FROM cloud_accounts WHERE is_active = TRUE")
            account_count = cur.fetchone()[0]
            
            # Active budgets
            cur.execute("SELECT COUNT(*) FROM budgets WHERE is_active = TRUE")
            budget_count = cur.fetchone()[0]
            
            # Open recommendations
            cur.execute("""
                SELECT COUNT(*), COALESCE(SUM(potential_savings), 0)
                FROM cost_optimization_recommendations
                WHERE is_implemented = FALSE
            """)
            row = cur.fetchone()
            open_recs = row[0]
            potential_savings = float(row[1])
        
        # Top services by cost - uses RealDictCursor for dict(row)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT service_name, SUM(cost_amount) as total
                FROM cost_data
                WHERE usage_date >= DATE_TRUNC('month', CURRENT_DATE)
                GROUP BY service_name
                ORDER BY total DESC
                LIMIT 5
            """)
            top_services = [dict(row) for row in cur.fetchall()]
            
            # Unacknowledged alerts
            cur.execute("SELECT COUNT(*) FROM cost_alerts WHERE is_acknowledged = FALSE")
            open_alerts = cur.fetchone()[0]
        
        change_pct = ((month_spend - last_month_spend) / last_month_spend * 100) if last_month_spend > 0 else 0
        
        return {
            "summary": {
                "month_spend": month_spend,
                "last_month_spend": last_month_spend,
                "change_percent": round(change_pct, 2),
                "accounts": account_count,
                "budgets": budget_count,
                "open_recommendations": open_recs,
                "potential_savings": potential_savings,
                "open_alerts": open_alerts
            },
            "top_services": top_services,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    finally:
        pool.putconn(conn)

# Background task to check budgets and generate alerts
async def check_budget_alerts():
    """Periodic task to check budget thresholds and create alerts"""
    import logging
    logger = logging.getLogger(__name__)
    
    while True:
        try:
            pool = get_db_pool()
            conn = pool.getconn()
            try:
                with conn.cursor() as cur:
                    # Get all active budgets
                    cur.execute("""
                        SELECT b.id, b.name, b.monthly_limit, b.alert_threshold, b.account_id,
                               COALESCE(SUM(c.cost_amount), 0) as current_spend
                        FROM budgets b
                        LEFT JOIN cost_data c ON b.account_id = c.account_id
                            AND c.usage_date >= DATE_TRUNC('month', CURRENT_DATE)
                        WHERE b.is_active = TRUE
                        GROUP BY b.id, b.name, b.monthly_limit, b.alert_threshold, b.account_id
                    """)
                    
                    for row in cur.fetchall():
                        utilization = (row["current_spend"] / row["monthly_limit"]) * 100 if row["monthly_limit"] > 0 else 0
                        
                        if utilization >= row["alert_threshold"]:
                            # Check if alert already exists for this budget
                            cur.execute("""
                                SELECT COUNT(*) FROM cost_alerts
                                WHERE budget_id = %s AND alert_type = 'threshold' 
                                AND created_at > DATE_TRUNC('month', CURRENT_DATE)
                            """, (row["id"],))
                            
                            if cur.fetchone()[0] == 0:
                                # Create new alert
                                cur.execute(
                                    """INSERT INTO cost_alerts (budget_id, alert_type, message, severity)
                                       VALUES (%s, %s, %s, %s)""",
                                    (row["id"], "threshold", 
                                     f"Budget '{row['name']}' has reached {utilization:.1f}% of limit",
                                     "warning" if utilization < 100 else "critical")
                                )
                    
                    conn.commit()
            finally:
                pool.putconn(conn)
        except Exception as e:
            logger.error(f"Budget alert check error: {e}", exc_info=True)
            # Sleep longer on error to avoid tight error loops
            await asyncio.sleep(300)  # Wait 5 minutes before retry
            continue
        
        await asyncio.sleep(3600)  # Check every hour

@app.on_event("startup")
async def startup_tasks():
    asyncio.create_task(check_budget_alerts())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
