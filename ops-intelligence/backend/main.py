"""
Ops Intelligence — FastAPI backend
Port: 8095

Endpoints (all under /api/):
  /api/incidents       — Incident Commander (6-phase protocol)
  /api/debt            — Technical Debt Quantifier (ROI-based)
  /api/costs           — FinOps Auditor (cloud cost tracking)
  /api/pipelines       — Data Pipeline Architect (health monitoring)
  /api/performance     — Performance Surgeon (bottleneck registry)
  /api/migrations      — Migration Strategist (zero-downtime tracker)
  /api/api-governance  — API Contract Enforcer (governance portal)
  /health              — liveness probe
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import incidents, debt, costs, pipelines, performance, migrations, api_governance, revenue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("ops_intelligence")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Ops Intelligence database...")
    init_db()
    logger.info("Database ready. Starting server.")
    yield
    logger.info("Ops Intelligence shutting down.")


app = FastAPI(
    title="ReliantAI Ops Intelligence",
    description="Unified operations platform: incidents, debt, costs, pipelines, performance, migrations, API governance.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all 7 domain routers
app.include_router(incidents.router, prefix="/api")
app.include_router(debt.router, prefix="/api")
app.include_router(costs.router, prefix="/api")
app.include_router(pipelines.router, prefix="/api")
app.include_router(performance.router, prefix="/api")
app.include_router(migrations.router, prefix="/api")
app.include_router(api_governance.router, prefix="/api")
app.include_router(revenue.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "service": "ops-intelligence", "version": "1.0.0"}


@app.get("/api/summary")
def global_summary():
    """Cross-domain health summary for the dashboard header."""
    from database import (
        list_incidents, list_debt_items, cost_summary,
        list_pipelines, list_performance_items,
        list_migrations, list_api_contracts,
    )
    active_incidents = list_incidents("active")
    sev1 = [i for i in active_incidents if i["severity"] == "SEV-1"]
    open_debt = [d for d in list_debt_items() if d["status"] != "resolved"]
    cs = cost_summary()
    pipelines_data = list_pipelines()
    failed_pipes = [p for p in pipelines_data if p["status"] == "failed"]
    open_perf = list_performance_items("open")
    active_migs = [m for m in list_migrations() if m["phase"] != "completed"]
    risky_migs = [m for m in active_migs if m["risk_level"] in ("high", "critical")]
    contracts = list_api_contracts()
    breaking = [c for c in contracts if c["breaking_changes"] > 0]

    return {
        "incidents": {"active": len(active_incidents), "sev1": len(sev1)},
        "debt": {
            "open_items": len(open_debt),
            "annual_interest": round(sum(d["interest_per_year"] for d in open_debt), 2),
        },
        "costs": {
            "monthly_total": cs["total_monthly_cost"],
            "savings_available": cs["total_savings_opportunity"],
        },
        "pipelines": {"total": len(pipelines_data), "failed": len(failed_pipes)},
        "performance": {"open_issues": len(open_perf)},
        "migrations": {"active": len(active_migs), "high_risk": len(risky_migs)},
        "api_governance": {"contracts": len(contracts), "breaking": len(breaking)},
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8095"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
