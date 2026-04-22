from __future__ import annotations

import importlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from lead_queue import LeadQueueDB


HTML_PAGE = b"""<!doctype html>
<html>
<head>
<title>Acme Plumbing | Houston TX</title>
<meta name="description" content="Houston plumbing repair and water heater service.">
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
<h1>Acme Plumbing</h1>
<p>Serving Houston, TX and Humble.</p>
<p>Call (713) 555-0101 or email hello@example.com</p>
<a href="/contact">Contact</a>
<a href="https://maps.google.com/?q=Acme+Plumbing+Houston">Google Maps</a>
<button>Request a Quote</button>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"LocalBusiness","name":"Acme Plumbing","aggregateRating":{"ratingValue":"4.7","ratingCount":"42"}}
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE)

    def log_message(self, format, *args):
        return


def test_full_local_pipeline(monkeypatch, tmp_path: Path) -> None:
    # Isolated runtime paths
    workspace = tmp_path / "workspace"
    market = tmp_path / "market"
    workspace.mkdir()
    market.mkdir()
    (market / "market_weights.json").write_text(json.dumps({
        "weights": {
            "plumbing": {"establishments": 1234, "density_weight": 0.8}
        }
    }), encoding="utf-8")

    db_path = str(workspace / "state" / "lead_queue.db")
    monkeypatch.setenv("CITADEL_DB_PATH", db_path)
    monkeypatch.setenv("EMAIL_BACKEND", "local_outbox")
    monkeypatch.setenv("DEPLOY_BACKEND", "local_fs")
    monkeypatch.setenv("DEPLOY_ENABLED", "true")
    monkeypatch.setenv("BRAND_FROM_EMAIL", "douglas-d-mitchell@outlook.com")
    monkeypatch.setenv("BRAND_OPTOUT_EMAIL", "optout@reliantai.org")
    monkeypatch.setenv("BRAND_POSTAL_ADDRESS", "Humble, TX")

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        import orchestrator
        importlib.reload(orchestrator)
        monkeypatch.setattr(orchestrator, "WORKSPACE_DIR", workspace)
        monkeypatch.setattr(orchestrator, "MARKET_DIR", market)

        result = orchestrator.run_pipeline(
            f"http://127.0.0.1:{server.server_port}/",
            dry_run=False,
            approve=True,
            send_email=True,
        )
        assert result["status"] == "emailed"
        assert result["qualified"]["vertical"] == "plumbing"
        assert result["deployment"]["provider"] == "local_fs"
        assert (workspace / "outbox").exists()
        assert any(p.suffix == ".eml" for p in (workspace / "outbox").iterdir())

        db = LeadQueueDB(db_path)
        funnel = db.funnel_counts()
        assert funnel["emailed"] == 1
        leads = db.recent_leads()
        assert leads[0]["business_name"] == "Acme Plumbing"
    finally:
        server.shutdown()
        thread.join(timeout=2)
