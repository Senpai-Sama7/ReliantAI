# 📖 Houston HVAC AI Dispatch — Operational Facility Guide (v1.1)

## 🏢 Executive Summary for Shop Owners

This system is your **24/7 Digital Dispatcher**. It monitors your business lines, identifies high-priority emergencies (like gas leaks or 100°F AC failures), and automatically coordinates with your technicians via SMS.

- **No New Apps:** Customers interact via standard SMS or WhatsApp.
- **Instant Response:** Customers get an acknowledgment in under 1 second.
- **Smart Triage:** Differentiates between a "Tune-up" and a "Thermal Emergency."
- **Revenue Protection:** Captures leads that would otherwise go to competitors during busy peaks.

---

## 🛰️ 1. The Command Hub (Admin Dashboard)

The heart of your operation is the **Industrial Command Hub**.

1. **Access:** Open your browser to `http://127.0.0.1:8888/admin`.
2. **Master Sequence Hub:** Watch incoming customer signals as they happen.
3. **Telemetry Mesh:** Track real-time Houston weather conditions and their impact on your dispatch priority.
4. **ROI Tracking:** View your "Recovered Asset Value" — a real-time calculation of revenue saved by the AI.

---

## 🚀 2. Quick Start for Managers

If you are setting this up for the first time:

1. **Credentials:** You must provide your API keys in the `.env` file (Gemini, Twilio, Composio).
2. **Technician Link:** Enter your technicians' phone numbers in the configuration so they receive the dispatch alerts.
3. **The Launch:** Run the server using the command:
   ```bash
   .venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8888
   ```
4. **New hardware?** Run `./setup_kubuntu.sh /path/to/destination` (from the repository root) to copy the project, install Python 3.11, recreate the `.venv`, and execute the tests before you start serving requests on a new Kubuntu/Linux machine or external drive.
4. **The Warm-up:** The system will take ~10 seconds on the very first start to "warm up" its neural brain. After that, it is instant.

---

## 🛠️ 3. How Triage Works

The AI uses a **Houston-Specific Logic Gate** to categorize every message:

- **🚨 LIFE_SAFETY:** Detected gas smells, carbon monoxide alarms, or smoke.
  - _Action:_ Immediate alert to the Shop Owner and a directive to the customer to call 911.
- **🔥 EMERGENCY:** No AC when it is over 95°F outside, or no heat when it is below 42°F.
  - _Action:_ Immediate technician dispatch request.
- **⚠️ URGENT:** Leaking water, weird noises, or partial cooling loss.
  - _Action:_ Same-day dispatch scheduling.
- **📅 ROUTINE:** Tune-ups, filter changes, or annual inspections.
  - _Action:_ Next available business day scheduling.

---

## 📈 4. Financial & Performance Monitoring

- **ROI Matrix:** Run `python tools/roi_calculator.py` at any time to see your monthly revenue impact based on real Houston market rates ($350 average dispatch value).
- **Log Audit:** Every message is saved in `dispatch.db`. You can view the full history in the **Master Sequence Hub** on the Dashboard.
- **LangSmith Tracing:** If enabled, you can "watch the AI think" in real-time through the LangSmith professional portal.

---

## ⚠️ 5. Safety Protocols

- **Human-in-the-loop:** The AI is designed to assist, not replace, professional judgment.
- **Escalation:** Any message the AI cannot confidently categorize is automatically escalated to the `OWNER_PHONE` for manual review.
- **Security:** The dashboard is protected and should only be accessed via secure company networks.

---

## ❓ 6. Common Questions

**Q: What if the internet goes out?**  
A: The system requires a connection to reach the Gemini (AI) and Twilio (SMS) gateways. If the link is severed, incoming messages will queue at Twilio and process once the connection is restored.

**Q: Can I change the emergency temperature thresholds?**  
A: Yes. These are located in `config.py` under `EMERGENCY_HEAT_THRESHOLD_F` (default 95°F).

**Q: How do I test it without spending money?**  
A: Use the **Smoke Test** script: `.venv/bin/python tools/smoke_test_neural.py`. This runs the full AI logic but simulates the SMS sends for free.

---

### Command & Control

- **System Version:** v1.4.0 (Industrial Gold)
- **Support:** PharaohDoug AI Agency // HOU-TX-USA
- **Last Security Audit:** March 2026

_Proprietary Operational Manual for Houston Dispatch Operations._
