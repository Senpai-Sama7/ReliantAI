# Houston HVAC AI Dispatch — Pitch Deck

## 1. Title
- **Product:** Houston HVAC AI Dispatch  
- **Promise:** Turn every HVAC inbound text into a verified dispatch in under 60 seconds.  
- **Stack:** CrewAI + Groq + Twilio + Composio + FastAPI.

## 2. Problem
- HVAC shops miss calls during peak heat/cold, costing ~$16k/month per shop in lost jobs.  
- Dispatch teams burn time manually triaging emergencies, confirming addresses, and texting technicians.  
- Scaling requires new staff or expensive software for a handful of shops.

## 3. Solution
- Multi-agent AI flow handles triage, intake, scheduling, dispatch, and follow-up automatically.  
- Twilio webhook intake + FastAPI API allow shops to keep using existing SMS numbers.  
- Built-in safety escalation (gas/CO/smoke = immediate owner ping) maintains compliance.

## 4. Market Validation
- Houston: 45% Hispanic population, summer temps >100°F, underserved HVAC shops (1–15 trucks).  
- ROI calculator (repo `roi_calculator.py`) shows one client recovers $2,394 net/mo after $611 cost.  
- Pilot plan: 1st client → $1,997 setup + $397/mo retainer → positive cash flow in week 1.

## 5. Product Highlights
- **Crew** runs: triage → intake → scheduling → dispatch → follow-up.  
- **Safety-first**: test suite covers 50 scenarios, streaming logs; escalation gate to owner via Twilio.  
- **Observability**: LangSmith (optional), Twilio logs, SQLite history; Twilio signature validation for security.  
- **Fallbacks**: test mode uses internal triage helper, LangSmith tracing disabled to avoid 403 errors.

## 6. Financials (see `FINANCIAL_PLAN.md`)
- Monthly run cost: ~$511–$1,151 (Groq + Render + Twilio + LangSmith).  
- Cost/run ≈ $10.18; cost/day ≈ $20.37 (based on 2 runs/day).  
- Revenue: $1,997 setup + $397/mo. After reserves, first client yields >$1,783 profit/month.

## 7. Security & Compliance
- `DISPATCH_API_KEY` must be set; default `change-me-in-env` disables API.  
- Twilio routes validated via `RequestValidator`.  
- LIFE_SAFETY escalation SMS always human-verified.

## 8. Ask
- Capital for Groq tokens beyond free tier + Render always-on hosting.  
- Ops to replace placeholder tech phone/Composio data and proof text routing.  
- Sales/marketing push with provided outreach templates + Loom script for follow-up.
