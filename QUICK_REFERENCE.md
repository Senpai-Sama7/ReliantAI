# ReliantAI Platform - Quick Reference

**Everything you need to know at a glance**

---

## 🚀 Quick Start (3 Commands)

```bash
# 1. Deploy
./scripts/deploy.sh local

# 2. Verify
./scripts/health_check.py -v

# 3. Access Dashboard
open dashboard/index.html
```

---

## 📊 Platform Overview

**20 Real Services**
- Core: Money (8000), ComplianceOne (8001), FinOps360 (8002), Orchestrator (9000)
- Integration: Integration Layer (8080)
- Infrastructure: PostgreSQL (5432), Redis (6379)
- 15 Additional Services: Citadel, ClearDesk, B-A-P, Acropolis, BackupIQ, Gen-H, ops-intelligence, DocuMancer, apex, reGenesis, CyberArchitect, citadel_ultimate_a_plus, soviergn_ai

**Key Features**
- 🤖 AI-powered predictions
- 📈 Auto-scaling (2-10 instances)
- 🔧 Auto-healing
- 🎛️ Real-time dashboard
- 🚀 One-click deployment

---

## 🎯 Essential URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Dashboard | `dashboard/index.html` | Web UI |
| Orchestrator | `http://localhost:9000` | Platform brain |
| Money | `http://localhost:8000` | HVAC dispatch |
| ComplianceOne | `http://localhost:8001` | Compliance mgmt |
| FinOps360 | `http://localhost:8002` | Cloud cost |
| Integration | `http://localhost:8080` | Service mesh |

---

## 🔧 Essential Commands

### Deployment
```bash
./scripts/deploy.sh local      # Local development
./scripts/deploy.sh staging    # Staging environment
./scripts/deploy.sh production # Production environment
```

### Health & Verification
```bash
./scripts/health_check.py -v           # Verbose health check
./scripts/health_check.py -j           # JSON output
./scripts/verify_integration.py       # Test integrations
```

### Docker Operations
```bash
docker-compose up -d                  # Start all services
docker-compose down                   # Stop all services
docker-compose logs -f [service]       # View logs
docker-compose restart [service]      # Restart service
docker-compose ps                     # List running services
```

### Service Control (API)
```bash
# Manual scaling
curl -X POST "http://localhost:9000/services/money/scale?target_instances=5"

# Manual restart
curl -X POST http://localhost:9000/services/money/restart

# Get platform status
curl http://localhost:9000/status

# Get dashboard data
curl http://localhost:9000/dashboard
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [README.md](./README.md) | Quick start guide, overview |
| [USER_MANUAL.md](./USER_MANUAL.md) | Complete usage guide for all services |
| [PLATFORM_GUIDE.md](./PLATFORM_GUIDE.md) | Architecture, features, deployment |
| [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) | Production verification checklist |
| This file | Quick reference |

---

## 🔌 API Quick Reference

### Orchestrator (Port 9000)
```
GET  /health              - Health check
GET  /status              - Platform status
GET  /services            - List services
GET  /dashboard           - Dashboard data
POST /services/{name}/scale     - Manual scale
POST /services/{name}/restart   - Manual restart
WS   /ws                  - WebSocket updates
```

### Money (Port 8000)
```
GET  /health              - Health check
POST /dispatch            - Create dispatch
GET  /dispatches          - List dispatches
GET  /dispatch/{id}/status - Dispatch status
```

### ComplianceOne (Port 8001)
```
GET  /health              - Health check
POST /frameworks          - Create framework
GET  /frameworks          - List frameworks
POST /controls            - Create control
POST /audits              - Start audit
POST /evidence            - Submit evidence
GET  /dashboard           - Compliance dashboard
```

### FinOps360 (Port 8002)
```
GET  /health              - Health check
POST /accounts           - Register account
POST /costs               - Submit cost data
POST /budgets             - Create budget
GET  /budgets/{id}/status - Budget status
POST /recommendations/generate - Generate recommendations
GET  /dashboard           - FinOps dashboard
```

---

## 🔑 Environment Variables

```bash
# Core Services
MONEY_URL=http://localhost:8000
COMPLIANCEONE_URL=http://localhost:8001
FINOPS360_URL=http://localhost:8002
ORCHESTRATOR_URL=http://localhost:9000

# API Keys (generate secure keys)
DISPATCH_API_KEY=your-secure-key
COMPLIANCEONE_API_KEY=your-secure-key
FINOPS360_API_KEY=your-secure-key

# External Services
GEMINI_API_KEY=your-gemini-key
TWILIO_SID=your-twilio-sid
TWILIO_TOKEN=your-twilio-token

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/reliantai
```

---

## 🎛️ Dashboard Features

### Top Metrics
- Platform health score (0-100%)
- Active services count
- Total instances
- AI predictions status

### Controls
- Auto-scale toggle
- Auto-heal toggle
- AI predictions toggle

### Service Cards
- Service name and URL
- Health status (animated)
- Instance count
- Manual scale/restart buttons

### Event Logs
- Real-time event stream
- Scaling events
- Healing events
- AI predictions

---

## 🤖 Autonomous Features

### Auto-Scaling Triggers
- Response time > 1s → Scale up
- CPU > 75% → Scale up
- Error rate > 5% → Scale up
- CPU < 20% → Scale down

### Auto-Healing
- 30-second health checks
- 3 failures → auto-restart
- Graceful degradation

### AI Predictions
- 30-minute forecast window
- CPU/memory prediction
- Optimal instance count

---

## 🐛 Troubleshooting

### Services Not Starting
```bash
# Check logs
docker-compose logs [service]

# Restart service
docker-compose restart [service]

# Rebuild service
docker-compose up -d --build [service]
```

### Database Issues
```bash
# Check PostgreSQL
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Port Conflicts
```bash
# Check what's using port
lsof -i :8000

# Change port in docker-compose.yml
```

### Health Check Failures
```bash
# Run verbose check
./scripts/health_check.py -v

# Check orchestrator
curl http://localhost:9000/status
```

---

## 📈 Monitoring

### Metrics Collected
- Response time (ms)
- CPU usage (%)
- Memory usage (%)
- Error rate (%)
- Request rate (req/s)
- Instance count

### View Metrics
```bash
curl http://localhost:9000/metrics
curl "http://localhost:9000/metrics?service=money&hours=1"
```

---

## 🔒 Security

### API Authentication
All services use `X-API-Key` header:
```bash
-H "X-API-Key: your-service-api-key"
```

### Best Practices
- Generate strong, unique API keys
- Never commit .env files
- Use HTTPS in production
- Restrict health endpoints
- Implement rate limiting

---

## 📁 Project Structure

```
ReliantAI/
├── Money/                  # HVAC AI Dispatch
├── ComplianceOne/          # Compliance Management (NEW)
├── FinOps360/              # Cloud Cost Management (NEW)
├── orchestrator/           # Autonomous Orchestrator (NEW)
├── dashboard/              # Web Dashboard (NEW)
├── integration/            # Service Integration Layer
├── scripts/                # Automation Scripts
│   ├── deploy.sh          # One-click deployment
│   ├── health_check.py    # Health verification
│   └── verify_integration.py
├── docker-compose.yml      # Full platform definition
├── .env                    # Environment configuration
├── README.md              # Quick start guide
├── USER_MANUAL.md         # Complete usage guide
├── PLATFORM_GUIDE.md      # Architecture details
├── PRODUCTION_CHECKLIST.md # Production checklist
└── QUICK_REFERENCE.md      # This file
```

---

## 🎯 Use Cases

### HVAC Business Owner
```bash
./scripts/deploy.sh local
# Access Money service at localhost:8000
# Manage dispatches, billing, customers
```

### Compliance Officer
```bash
# Access ComplianceOne at localhost:8001
# Setup SOC2/GDPR frameworks
# Track audits and evidence
```

### Cloud Engineer
```bash
# Access FinOps360 at localhost:8002
# Monitor AWS/Azure/GCP costs
# Get optimization recommendations
```

### Platform Admin
```bash
# Access Orchestrator at localhost:9000
# Monitor all services
# View AI predictions
# Manual scaling/healing
```

---

## ✅ Verification Checklist

### Before Deployment
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] .env file configured
- [ ] API keys generated
- [ ] Ports available

### After Deployment
- [ ] All services start
- [ ] Health checks pass
- [ ] Dashboard connects
- [ ] APIs respond
- [ ] Auto-scaling active
- [ ] Auto-healing active

---

## 📞 Quick Help

### Commands Reference
```bash
# Deploy
./scripts/deploy.sh [environment]

# Health
./scripts/health_check.py -v

# Test
./scripts/verify_integration.py

# Logs
docker-compose logs -f [service]

# Scale
curl -X POST "http://localhost:9000/services/money/scale?target_instances=5"

# Restart
curl -X POST http://localhost:9000/services/money/restart
```

### Documentation
- Quick start: README.md
- Complete guide: USER_MANUAL.md
- Architecture: PLATFORM_GUIDE.md
- Production: PRODUCTION_CHECKLIST.md

---

## 🎉 Platform Status

✅ **20 Services** - All functional  
✅ **Autonomous** - AI-powered orchestration  
✅ **Self-Healing** - Automatic recovery  
✅ **Auto-Scaling** - Dynamic resource allocation  
✅ **Production Ready** - Fully tested and verified  

---

**Built for the future of enterprise automation.**
