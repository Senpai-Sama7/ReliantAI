# ReliantAI Platform Agent Guide

## 🚀 Deployment
- **Deploy platform**: `./scripts/deploy.sh [local|staging|production]`
  - Local: `./scripts/deploy.sh local` (default)
  - Checks prerequisites, builds images, starts infrastructure/services, runs health checks
- **Manual Docker compose**: 
  - Start: `docker compose up -d`
  - Stop: `docker compose down`
  - Logs: `docker compose logs -f [service]`
  - Restart service: `docker compose restart [service]`

## 🔍 Health & Verification
- **Verbose health check**: `./scripts/health_check.py -v`
- **JSON health check**: `./scripts/health_check.py -j`
- **Integration tests**: `./scripts/verify_integration.py`
- **Service health endpoints** (no auth required):
  - Money: `curl http://localhost:8000/health`
  - ComplianceOne: `curl http://localhost:8001/health`
  - FinOps360: `curl http://localhost:8002/health`
  - Orchestrator: `curl http://localhost:9000/health`
  - Integration: `curl http://localhost:8080/health`

## ⚙️ Service Control (via Orchestrator API)
- **Manual scale**: `curl -X POST "http://localhost:9000/services/[name]/scale?target_instances=[n]"`
- **Manual restart**: `curl -X POST http://localhost:9000/services/[name]/restart`
- **Platform status**: `curl http://localhost:9000/status`
- **Dashboard data**: `curl http://localhost:9000/dashboard`

## 🐳 Service Ports
- Money: 8000 (HVAC AI Dispatch)
- ComplianceOne: 8001 (Compliance Management)
- FinOps360: 8002 (Cloud Cost Management)
- Integration: 8080 (Service Mesh)
- Orchestrator: 9000 (Platform Brain + Dashboard)
- PostgreSQL: 5432
- Redis: 6379

## 📁 Environment & Configuration
- **Environment variables**: `.env` (auto-copied from `.env.example` if missing)
- **Required API keys** in `.env`: 
  - `DISPATCH_API_KEY`, `COMPLIANCEONE_API_KEY`, `FINOPS360_API_KEY`
  - `GEMINI_API_KEY`, `TWILIO_SID`, `TWILIO_TOKEN`
- **Database URL**: `DATABASE_URL=postgresql://user:pass@localhost/platform`

## 📊 Dashboard Access
- **Web UI**: Open `dashboard/index.html` in browser
- **Or via URL**: http://localhost:9000/dashboard

## 🧪 Testing Conventions
- **Prerequisites**: Docker and Docker Compose must be installed
- **Ports checked**: 8000, 8001, 8002, 8080, 9000, 5432, 6379 (health checks verify availability)
- **Test order**: Deploy → Health checks → Integration tests
- **Service-specific tests**: Check individual service directories for README/AGENTS.md

## 📚 Service-Specific Guidance
- **Money**: HVAC AI dispatch (CrewAI, Twilio, Billing) - see `Money/`
- **ComplianceOne**: SOC2/GDPR compliance - see `ComplianceOne/`
- **FinOps360**: Cloud cost management - see `FinOps360/`
- **Orchestrator**: AI-powered orchestration - see `orchestrator/`
- **Integration**: Service mesh - see `integration/`
- Other services: Citadel, ClearDesk, B-A-P, Acropolis, BackupIQ, Gen-H, ops-intelligence, apex, reGenesis, CyberArchitect, citadel_ultimate_a_plus, soviergn_ai, DocuMancer

## ⚠️ Gotchas
- First run may take several minutes (building 20+ service images)
- Health check retries services for up to 60 seconds
- Sample data loaded only for local/staging environments
- If ports are occupied, stop conflicting processes or change `docker-compose.yml` host port mappings
- Orchestrator health is required for dashboard and API functionality