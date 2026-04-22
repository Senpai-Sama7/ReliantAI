# ReliantAI - Unified HVAC Growth System

**A subsidiary service for SEO & Geo-targeted business websites**

**Owner:** Douglas Mitchell | Houston, TX | Serving Businesses Everywhere  
**Contact:** [DouglasMitchell@ReliantAI.org](mailto:DouglasMitchell@ReliantAI.org) | +1-832-947-7028  
**LinkedIn:** [linkedin.com/in/douglas-mitchell-the-architect](https://www.linkedin.com/in/douglas-mitchell-the-architect/)

---

A complete HVAC lead generation and dispatch system with a premium customer-facing website and integrated admin portal.

## System Overview

This unified system combines:

- **Backend**: FastAPI server with CrewAI multi-agent dispatch
- **Frontend**: Vite React SPA with premium dark editorial design
- **Database**: SQLite for dispatch tracking and message logging
- **AI**: Gemini 3.1 Flash for intelligent lead triage and dispatch

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Gemini API key
- Twilio account (for SMS/WhatsApp)

### 1. Clone and Setup

```bash
git clone https://github.com/Senpai-Sama7/Gen-H.git
cd Gen-H
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Start the Server

```bash
.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Access the System

- **Customer Website**: http://localhost:8000/
- **Admin Portal**: http://localhost:8000/admin/login
- **API Documentation**: http://localhost:8000/docs
- **Legacy Admin**: http://localhost:8000/legacy-admin

## Project Structure

```
.
├── main.py                 # FastAPI entry point
├── config.py               # Configuration management
├── database.py             # SQLite database operations
├── hvac_dispatch_crew.py   # CrewAI multi-agent system
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
│
├── frontend/               # React Vite frontend
│   ├── index.html         # Entry HTML
│   ├── package.json       # Node dependencies
│   ├── src/
│   │   ├── App.tsx        # Main app component
│   │   ├── sections/      # Website sections
│   │   │   ├── Hero.tsx
│   │   │   ├── CardStack.tsx
│   │   │   ├── BreathSection.tsx
│   │   │   └── ...
│   │   ├── sections/admin/  # Admin portal
│   │   │   ├── AdminLogin.tsx
│   │   │   └── AdminDashboard.tsx
│   │   ├── services/      # API client
│   │   └── contexts/      # React contexts
│   └── public/            # Static assets (images)
│
├── templates/             # Legacy Jinja2 templates
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## Features

### Customer-Facing Website

- **Premium Dark Editorial Design**: #0B0C0E background, gold accents
- **GSAP Scroll Animations**: Smooth scroll-driven reveals
- **Hero Section**: Full-viewport with Ken Burns effect
- **Card Stack**: Pinned scroll gallery (Attract → Qualify → Convert)
- **Breath Section**: Cinematic metrics display
- **ZigZag Grid**: Process explanation (Clarify → Capture → Run → Optimize)

### Admin Portal

- **Secure Login**: Session-based admin authentication with CSRF-protected login form
- **Dashboard Metrics**: Total, pending, completed, emergency dispatches
- **Dispatch List**: Real-time view with auto-refresh
- **Customer Info**: Phone, issue, urgency, status

### Backend API

- **POST /dispatch**: Create new dispatch
- **GET /dispatches**: List recent dispatches
- **GET /run/{id}**: Get dispatch status
- **POST /sms**: Twilio SMS webhook
- **POST /whatsapp**: Twilio WhatsApp webhook
- **GET /health**: Health check
- **Shared Auth Integration**: Accepts bearer tokens verified by the central auth service
- **Event Bus Integration**: Publishes `dispatch.completed` when dispatch orchestration succeeds

## Environment Variables

Create a `.env` file with:

```env
# Required
GEMINI_API_KEY=your_gemini_key
TWILIO_SID=your_twilio_sid
TWILIO_TOKEN=your_twilio_token
TWILIO_FROM_PHONE=+15551234567
OWNER_PHONE=+15559876543
TECH_PHONE_NUMBER=+15555678901
COMPOSIO_API_KEY=your_composio_key
DISPATCH_API_KEY=your_admin_api_key
AUTH_SERVICE_URL=http://localhost:8080
EVENT_BUS_URL=http://localhost:8081
DEFAULT_TENANT_ID=money-default

# Optional
DATABASE_PATH=dispatch.db
LOG_LEVEL=INFO
ENV=dev
```

## Deployment

### Render.com (Recommended)

1. Push to GitHub
2. Create new Web Service on Render
3. Connect your repository
4. Set environment variables in Render dashboard
5. Deploy!

The `render.yaml` is pre-configured for deployment.

### Manual Deployment

```bash
# Build frontend
cd frontend
npm run build
cd ..

# Start backend (serves frontend automatically)
.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Development

### Backend Development

```bash
# Run with auto-reload
.venv/bin/python -m uvicorn main:app --reload

# Run tests
.venv/bin/python -m pytest tests/ -v

# Run tests with coverage
.venv/bin/python -m pytest tests/ --cov=. --cov-report=term-missing

# Coverage uses .coveragerc to measure the maintained dispatch runtime
# and exclude optional connectors that are verified separately.
```

### Frontend Development

```bash
cd frontend

# Dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Get dispatches (API key)
curl -H "x-api-key: YOUR_KEY" http://localhost:8000/dispatches

# Create dispatch (API key)
curl -X POST -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"customer_message": "AC not working, 95 degrees", "outdoor_temp_f": 95}' \
  http://localhost:8000/dispatch

# Create dispatch (shared bearer token)
curl -X POST -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"customer_message": "AC not cooling", "outdoor_temp_f": 95}' \
  http://localhost:8000/dispatch
```

## Architecture

### Request Flow

1. **Customer** texts/calls via Twilio
2. **FastAPI** receives webhook → saves to database
3. **CrewAI** processes with multi-agent workflow:
   - Triage Agent: Assess urgency
   - Intake Agent: Gather details
   - Scheduler Agent: Find availability
   - Dispatch Agent: Assign technician
   - Followup Agent: Confirm completion
4. **Results** stored in SQLite
5. **Admin** views via React dashboard

### Frontend Architecture

- **React 19** with TypeScript
- **React Router** for SPA navigation
- **GSAP + ScrollTrigger** for animations
- **Lenis** for smooth scrolling
- **Tailwind CSS** for styling
- **Lucide React** for icons

### Backend Architecture

- **FastAPI** for HTTP API
- **SQLite** with WAL mode for persistence
- **CrewAI** for multi-agent orchestration
- **Gemini 3.1 Flash** for LLM inference
- **Twilio** for SMS/WhatsApp

## Security

- `/dispatch`, `/dispatches`, `/run/{id}`, and the dispatch analytics endpoints accept either:
  - `Authorization: Bearer <jwt>` validated against `AUTH_SERVICE_URL`
  - `x-api-key: <DISPATCH_API_KEY>`
  - Admin session cookies for the web dashboard

- API key authentication on all endpoints
- Session-based auth for legacy admin
- CORS configured for same-origin
- Rate limiting on SMS endpoints
- Input validation and sanitization
- SQL injection prevention (parameterized queries)

## License

© 2025 ReliantAI.org | Douglas Mitchell. All rights reserved.

---

**Built with ❤️ in Houston, TX** | Serving HVAC businesses everywhere
