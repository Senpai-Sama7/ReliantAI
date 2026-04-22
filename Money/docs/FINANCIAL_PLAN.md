# Houston HVAC AI Dispatch — Financial Plan

## Capital Base
- **Development cost**: existing repo serves as capitalized asset. Assign optional internal labor value (e.g., $5k/week) only if accounting for engineering hours.
- **Key infrastructure setup**: Render Starter ($7/month), Groq account (free tier), LangSmith (5k traces free), Twilio number, Composio integration.

## Monthly Operating Budget
| Item | Description | Pilot Estimate |
|---|---|---|
| Hosting | Render Starter always-on + disk persistence | $7 |
| LLM usage | Groq token beyond free tier; pilot ~$500–$1,000 | $500–$1,000 |
| Tracing | LangSmith overage beyond 5k traces | $0–$100 |
| SMS/Webhook | Twilio outbound at ~$0.0075 per SMS (500/mo ≈ $4) | ~$4 |
| Durable storage | Redis/Postgres or Render disk (optional) | $0–$40 |
| **Total range** | Baseline pilot burn | **$511–$1,151** |

## Cost per Run / Day
- Assumes 60 dispatch runs/month (~2/day).  
- Monthly burn ≈ $611 ⇒ **$10.18 per run**, **$20.37 per day**.
- Add Groq token telemetry to refine once real usage starts; adjust when tech routing replaces placeholders.

## Revenue & ROI
- **Setup fee**: $1,997 per client.  
- **Retainer**: $397/mo per client for monitoring.  
- **Net after pilot cost**: one client pays $2,394/mo → ~$1,783 profit after $611 op cost.  
- Payback occurs in ~5 runs (at ~$399 implied value per run).
- Upsell: follow-up agent flags maintenance contracts (30% repair savings), increasing lifetime value.

## Capital Needed for Scaling / Loans
- **Immediate buffer**: $1,065 to cover Groq surge, Render disk, Twilio spend.  
- **12-month plan**: allocate $1,500–$2,000 for Redis math, extra LangSmith traces, and phone number rotation.
- **Ops control**: maintain a $200 petty fund for unexpected Twilio refunds, Groq hotspots, or new integrations (e.g., Composio upgrades).

## Living Controls & Tracking
- Track Groq token usage weekly; set alerts before hitting the paid bucket.  
- LangSmith trace count resets monthly—monitor to avoid surprise charges.  
- SMS volume by campaign: use Twilio logs to confirm dispatch vs. follow-up messages.  
- Replace placeholders (Composio account ID + tech phone) before large client intake so analytic data reflects reality.

## Risks / Missing Items
1. **LLM warmup**: CrewAI first-hit takes ~60–70s even with LiteLLM; consider async warm-up job on deployment to keep latency acceptable.
2. **Real Twilio delivery**: currently mocked; assign phone numbers per technician and capture delivery receipts post-mock run.
3. **Composio wiring**: stub `check_tech_availability` still uses placeholder; schedule real calendar once credentials are in place.
4. **LangSmith or Groq credential rotation**: include refresh plan for API keys and monitor `LANGCHAIN`/Groq billing dashboards.

## Additional Considerations
- **Insurance / Compliance**: Document how `LIFE_SAFETY` escalations work if you plan to pitch investors or underwrite enterprise contracts; highlight the human-in-the-loop gate.
- **Documentation & Pitch Materials**: Use `deployment_guide.md`, `AGENTS.md`, ROI calculator outputs, and Twilio/LangSmith dashboards to assemble pitch decks or loan appendices.
- **Investor-ready metrics**: track monthly recurring revenue per client, dispatch volume, average response time, and net promoter score from follow-up agent interactions.

## Next Steps
1. Replace placeholder Composio/technician data and test live integrations; log any additional third-party costs.
2. Collect actual Groq token consumption per run and update the per-run cost assumptions.
3. Document credentials rotation, escalation process, and rollback plans for investors or lenders.
