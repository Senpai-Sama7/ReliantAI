# OpenClaw Integration Implementation Notes

## Validated OpenClaw Capabilities (Mar 1, 2026)
- OpenClaw runs locally, exposes a CLI/gateway (`openclaw start`), automations (cron, wakeups, scheduled runbooks), and a browser automation stack with Canvas/Chrome control, which means it can orchestrate multi-step flows without pushing data offsite. citeturn0search5turn0search3
- It pairs with hundreds of messaging channels (WhatsApp, Telegram, Discord, Slack, iMessage, etc.), so our Twilio endpoints can coexist with OpenClaw’s multichannel control plane or be wrapped in its webhook automation. citeturn0search5
- OpenClaw skills are modular plugins with a marketplace (ClawHub) that now includes learning, scheduling, and persistence enhancements, allowing it to call HTTP endpoints, run shell scripts, and maintain state across sessions. citeturn0search1turn0search3
- The platform emphasizes self-hosted execution with system access (file read/write, shell, cron jobs) and built-in observability (gateway status dashboard, session history), which we will pair with our SQLite logs and current CLI scripts. citeturn0search5
- Security guidance from recent research warns OpenClaw should operate in isolated environments with credential rotation due to the powerful skill marketplace and persistent system access. citeturn0news12turn0news13

## Implementation Strategy
1. **Gateway & Credential Hardening:** Wrap `openclaw start` in a helper so we capture startup logs and ensure it terminates gracefully when the HVAC AI node is down. The helper will enforce the same credential checks (`TECH_PHONE_NUMBER`, `COMPOSIO_API_KEY`, `DISPATCH_API_KEY`) before allowing OpenClaw to trigger downstream tasks, mirroring the existing `config.py` guardrails.
2. **Orchestration Tasks:** Expose the existing flows as OpenClaw automations:
   - `triage_dispatch`: call `python test_suite.py` (dry-run) followed by `python roi_calculator.py`, then trigger `POST /dispatch` via `curl` or the local API to demonstrate the CrewAI path. This leverages OpenClaw’s automation engine (cron/wakeups/webhooks) to camera roll sequential tasks. citeturn0search5
   - `dispatch_monitor`: poll `/run/{id}` and `/dispatches` using OpenClaw’s HTTP/Webhook skill modules (available via ClawHub). The same automation can log results into `hvac_dispatch.log`.
3. **Error Handling & Observability:** Feed SQLite error conditions and Twilio status into OpenClaw’s log ingestion (the gateway monitors session logs and can trigger alerts). Build recurring cron jobs or wakeup tasks that scan `hvac_dispatch.log` for `ERROR` entries and call Twilio owner numbers via OpenClaw’s messaging integrations to surface incidents. citeturn0search5
4. **QA Gates:** Define OpenClaw skills to run `python test_suite.py`, `pytest test_component_security.py`, and `python audit_component_tests.py` after every code change, using `openclaw run` or schedule steps. These outputs feed into OpenClaw’s session dashboard so we can flag failures before outreach sequences.
5. **Outreach Sequence:** Create a ClawHub skill tailored to our pitch/pricing docs that composes status summaries (`OPENCLAW_INTEGRATION_PLAN.md`, `FINANCIAL_PLAN.md`, `PITCH_DECK.md`) and sends templated messages through WhatsApp or Slack using OpenClaw’s messaging stack (already supports these channels). citeturn0search5
6. **Credential & Cost Awareness:** Let OpenClaw maintain a secure vault (its local config directory) for the eight critical secrets. Document rotation schedules and detection routines—OpenClaw can run cron tasks checking for default or stale secrets before running high-impact skills.

## Next Steps for Implementation
1. Build `openclaw_integration.py` (see companion module) that houses helpers for running the gateway, invoking scripts, and articulating retries/backoffs.  
2. Draft OpenClaw automations (skills/wakeups) that map to each documented task, ensuring they reference our CLI scripts and endpoints.  
3. Secure the skill deployment by running OpenClaw inside an isolated VM or container, per Microsoft’s safety advisory, and keep Canary credentials separate. citeturn0news12  
4. Validate the entire pipeline with mock credentials before connecting real Twilio/Groq/LangSmith keys, then update `deployment_guide.md` with the OpenClaw-specific runbook.
