#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import threading
from collections import defaultdict
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi import Path as FastAPIPath
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from lead_queue import DB_PATH_DEFAULT, LeadQueueDB

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env", override=False)

DB_PATH = os.getenv("CITADEL_DB_PATH", DB_PATH_DEFAULT)
READ_API_KEY = os.getenv("CITADEL_DASHBOARD_API_KEY", "").strip()
WEBHOOK_SECRET = os.getenv("OPENCLAW_WEBHOOK_SECRET", "").strip()
MAX_SKEW = int(os.getenv("OPENCLAW_WEBHOOK_MAX_SKEW_SECONDS", "300"))
RATE_LIMIT_API = int(os.getenv("CITADEL_RATE_LIMIT_API_RPM", "60"))
RATE_LIMIT_WEBHOOK = int(os.getenv("CITADEL_RATE_LIMIT_WEBHOOK_RPM", "30"))

app = FastAPI(title="Citadel Operator Console", version="1.0.0")

CORS_ORIGINS = [o.strip() for o in os.getenv("CITADEL_CORS_ORIGINS", "").split(",") if o.strip()]
if CORS_ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["X-API-Key", "Content-Type", "X-Citadel-Timestamp", "X-Citadel-Signature"])

_rate_buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
_rate_lock = threading.Lock()
_rate_counter = 0


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _check_rate(ip: str, scope: str, limit: int) -> None:
    if limit <= 0:
        return
    global _rate_counter
    now = time.time()
    cutoff = now - 60
    key = (ip, scope)
    with _rate_lock:
        _rate_counter += 1
        bucket = _rate_buckets[key]
        _rate_buckets[key] = [t for t in bucket if t > cutoff]
        if len(_rate_buckets[key]) >= limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        _rate_buckets[key].append(now)
        if _rate_counter % 100 == 0:
            for k in list(_rate_buckets):
                _rate_buckets[k] = [t for t in _rate_buckets[k] if t > cutoff]
                if not _rate_buckets[k]:
                    del _rate_buckets[k]


def db() -> LeadQueueDB:
    q = LeadQueueDB(DB_PATH)
    q.init_db()
    return q


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    if not READ_API_KEY:
        raise HTTPException(status_code=503, detail="CITADEL_DASHBOARD_API_KEY is not configured")
    if x_api_key != READ_API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")


def verify_webhook_signature(raw_body: bytes, timestamp_header: str, signature_header: str) -> None:
    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    try:
        ts = int(timestamp_header)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid X-Citadel-Timestamp")
    now = int(time.time())
    if abs(now - ts) > MAX_SKEW:
        raise HTTPException(status_code=401, detail="Webhook timestamp outside allowed skew")
    if not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Invalid signature format")
    sent = signature_header.split("=", 1)[1].strip().lower()
    expected = hmac.new(WEBHOOK_SECRET.encode("utf-8"), f"{ts}.".encode("utf-8") + raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sent, expected):
        raise HTTPException(status_code=401, detail="Signature mismatch")


@app.get("/health")
def health() -> JSONResponse:
    try:
        db().funnel_counts()
        return JSONResponse({"status": "ok"})
    except Exception:
        return JSONResponse({"status": "degraded", "error": "db_unreachable"}, status_code=503)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    protected = "enabled" if READ_API_KEY else "misconfigured"
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Citadel Operator Console</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin:0; background:#f8fafc; color:#0f172a; }}
    .wrap {{ width:min(1120px, calc(100% - 24px)); margin:0 auto; }}
    header {{ padding:16px 0; border-bottom:1px solid #e2e8f0; background:#fff; position:sticky; top:0; }}
    h1 {{ margin:0; font-size:20px; }}
    .sub {{ color:#475569; margin-top:4px; font-size:12px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; margin-top:12px; }}
    .card {{ background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:12px; box-shadow:0 6px 18px rgba(2,6,23,.03); }}
    .metric {{ font-size:22px; font-weight:700; margin-top:6px; }}
    table {{ width:100%; border-collapse:collapse; margin-top:12px; background:#fff; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden; }}
    th, td {{ padding:10px; border-bottom:1px solid #e2e8f0; text-align:left; font-size:13px; vertical-align:top; }}
    th {{ background:#f1f5f9; font-weight:600; }}
    .layout {{ display:grid; grid-template-columns:2fr 1fr; gap:12px; margin-top:12px; }}
    @media (max-width: 920px) {{ .layout {{ grid-template-columns:1fr; }} }}
    button {{ border:1px solid #cbd5e1; border-radius:8px; padding:8px 10px; background:#fff; cursor:pointer; }}
    input {{ border:1px solid #cbd5e1; border-radius:8px; padding:8px; width:100%; }}
    pre {{ margin:0; white-space:pre-wrap; word-break:break-word; }}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <h1>Citadel Operator Console</h1>
      <div class="sub">Read API key protection: {protected}. Webhook signing: {'configured' if WEBHOOK_SECRET else 'missing'}.</div>
    </div>
  </header>
  <main class="wrap" style="padding:12px 0 24px">
    <div style="display:flex; gap:8px; align-items:center;">
      <input id="apiKey" placeholder="Optional X-API-Key">
      <button onclick="refresh()">Refresh</button>
    </div>
    <div id="metrics" class="grid"></div>
    <div class="layout">
      <div>
        <table id="leadTable"><thead></thead><tbody></tbody></table>
      </div>
      <div>
        <div class="card">
          <div style="font-weight:600">Lead timeline</div>
          <input id="leadSlug" placeholder="lead-slug" style="margin-top:8px">
          <button onclick="loadTimeline()" style="margin-top:8px">Load Timeline</button>
          <pre id="timeline" style="margin-top:10px; font-size:12px;"></pre>
        </div>
        <div class="card" style="margin-top:12px;">
          <div style="font-weight:600">Vertical performance</div>
          <pre id="verticals" style="margin-top:8px; font-size:12px;"></pre>
        </div>
      </div>
    </div>
  </main>
  <script>
    function headers() {{
      const key = document.getElementById('apiKey').value.trim();
      return key ? {{'X-API-Key': key}} : {{}};
    }}
    async function getJson(path) {{
      const r = await fetch(path, {{headers: headers()}});
      const t = await r.text();
      if (!r.ok) throw new Error(`${{r.status}} ${{t}}`);
      return JSON.parse(t);
    }}
    function metricCard(label, value) {{
      return `<div class="card"><div>${{label}}</div><div class="metric">${{value}}</div></div>`;
    }}
    async function refresh() {{
      try {{
        const [funnel, economics, leads, verticals, beats] = await Promise.all([
          getJson('/api/funnel'),
          getJson('/api/economics'),
          getJson('/api/leads?limit=20'),
          getJson('/api/verticals'),
          getJson('/api/beat-compliance')
        ]);
        const m = document.getElementById('metrics');
        m.innerHTML = [
          metricCard('Scouted', funnel.scouted || 0),
          metricCard('Qualified', funnel.qualified || 0),
          metricCard('Built', funnel.built || 0),
          metricCard('Approved', funnel.approved || 0),
          metricCard('Deployed', funnel.deployed || 0),
          metricCard('Emailed', funnel.emailed || 0),
          metricCard('Replied', funnel.replied || 0),
          metricCard('Won Revenue', '$' + ((economics.won_revenue_cents||0)/100).toFixed(2)),
          metricCard('Beat Compliance', `${{beats.fully_compliant || 0}}/${{beats.total_outreach_drafts || 0}}`)
        ].join('');

        const thead = document.querySelector('#leadTable thead');
        const tbody = document.querySelector('#leadTable tbody');
        thead.innerHTML = '<tr><th>Lead</th><th>Status</th><th>Score</th><th>Contact</th><th>Updated</th></tr>';
        tbody.innerHTML = (leads || []).map(l => `<tr>
          <td><div><strong>${{l.business_name}}</strong></div><div style="color:#64748b">${{l.lead_slug}}</div><div style="color:#64748b">${{l.vertical}} • ${{l.city}}, ${{l.state}}</div></td>
          <td>${{l.pipeline_status}} / ${{l.deal_status}}</td>
          <td>${{l.opportunity_score}}</td>
          <td>${{l.email || ''}}<br>${{l.phone || ''}}</td>
          <td>${{l.updated_at}}</td>
        </tr>`).join('');
        document.getElementById('verticals').textContent = JSON.stringify(verticals, null, 2);
      }} catch (e) {{
        alert(String(e));
      }}
    }}
    async function loadTimeline() {{
      const slug = document.getElementById('leadSlug').value.trim();
      if (!slug) return;
      try {{
        const data = await getJson('/api/lead/' + encodeURIComponent(slug) + '/timeline');
        document.getElementById('timeline').textContent = JSON.stringify(data, null, 2);
      }} catch (e) {{
        alert(String(e));
      }}
    }}
    refresh();
  </script>
</body>
</html>"""


@app.get("/api/funnel")
def api_funnel(request: Request, _: None = Depends(require_api_key)) -> JSONResponse:
    _check_rate(_client_ip(request), "api", RATE_LIMIT_API)
    return JSONResponse(db().funnel_counts())


@app.get("/api/verticals")
def api_verticals(request: Request, _: None = Depends(require_api_key)) -> JSONResponse:
    _check_rate(_client_ip(request), "api", RATE_LIMIT_API)
    return JSONResponse(db().conversion_by_vertical())


@app.get("/api/leads")
def api_leads(request: Request, limit: int = 50, _: None = Depends(require_api_key)) -> JSONResponse:
    _check_rate(_client_ip(request), "api", RATE_LIMIT_API)
    return JSONResponse(db().recent_leads(limit=min(max(limit, 1), 200)))


@app.get("/api/economics")
def api_economics(request: Request, _: None = Depends(require_api_key)) -> JSONResponse:
    _check_rate(_client_ip(request), "api", RATE_LIMIT_API)
    return JSONResponse(db().economics_summary())


@app.get("/api/beat-compliance")
def api_beat_compliance(request: Request, _: None = Depends(require_api_key)) -> JSONResponse:
    _check_rate(_client_ip(request), "api", RATE_LIMIT_API)
    return JSONResponse(db().beat_compliance_summary())


@app.get("/api/lead/{lead_slug}/timeline")
def api_timeline(request: Request, lead_slug: str = FastAPIPath(pattern=r"^[a-z0-9-]{5,120}$"), _: None = Depends(require_api_key)) -> JSONResponse:
    _check_rate(_client_ip(request), "api", RATE_LIMIT_API)
    try:
        return JSONResponse(db().lead_timeline(lead_slug))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/webhooks/openclaw")
async def webhook_openclaw(
    request: Request,
    x_citadel_timestamp: str = Header(default=""),
    x_citadel_signature: str = Header(default=""),
) -> JSONResponse:
    _check_rate(_client_ip(request), "webhook", RATE_LIMIT_WEBHOOK)
    raw = await request.body()
    if len(raw) > 65536:
        raise HTTPException(status_code=413, detail="Request body too large")
    verify_webhook_signature(raw, x_citadel_timestamp, x_citadel_signature)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="JSON body must be an object")

    for key in ("event_id", "event_type"):
        if key not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field: {key}")

    event_type = str(payload["event_type"])
    if event_type not in {"deployment.succeeded", "deployment.failed", "outreach.sent", "lead.replied", "deal.won", "deal.lost"}:
        raise HTTPException(status_code=400, detail=f"Unsupported event_type: {event_type}")

    if event_type not in {"outreach.sent"} and "lead_slug" not in payload:
        raise HTTPException(status_code=400, detail="Missing field: lead_slug")
    if event_type == "outreach.sent":
        for key in ("lead_slug", "outreach_id"):
            if key not in payload:
                raise HTTPException(status_code=400, detail=f"Missing field: {key}")

    try:
        result = db().apply_webhook_event("openclaw", payload)
        return JSONResponse(result)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
