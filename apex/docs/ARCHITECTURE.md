# APEX Architecture Reference

## Design Principle

Most multi-agent systems fail because they treat agents as parallel workers. APEX is structured as a cognitive stack — each layer's output constrains the operating envelope of the layer below it. Speed without intelligence is the failure mode being solved.

---

## The A2A Protocol

Every message in APEX carries confidence and decomposed uncertainty in the context block. This means every agent in the graph knows not just what it received, but how certain the sender was.

```
A2AMessage
├── message_id    (UUID — unique per message)
├── trace_id      (UUID — groups all messages in one task)
├── sender        (string — agent name)
├── recipient     (Agent | Layer | Broadcast)
├── payload       (arbitrary task data)
├── context
│   ├── confidence       (0.0–1.0)
│   ├── uncertainty
│   │   ├── aleatoric    (irreducible data noise)
│   │   └── epistemic    (model uncertainty — reducible)
│   ├── stakes           (low | medium | high | irreversible)
│   └── domain_novelty   (0.0–1.0)
└── timestamp
```

---

## Confidence-Gated Routing (apex-core)

The Rust bus evaluates every message's context block before any agent logic runs:

```
domain_novelty > 0.85          → T4 Unknown      → human escalation
stakes = high | irreversible   → T3 Contested    → full pipeline + HITL
confidence < 0.65              → T3 Contested    → full pipeline + HITL
confidence > 0.92 + low stakes → T1 Reflexive    → skip to Layer 3
otherwise                      → T2 Deliberative → full L1–L3 pipeline
```

This prevents the failure mode where agents execute with false certainty.

---

## Layer 1 — Orchestration

### Theory of Mind
Runs first on every task. Produces an adversarial prior: hidden objectives, failure modes, adversarial scenarios, stakeholder perspectives, and epistemic gaps. Every downstream agent receives this before acting.

### Data Model Plan
Defines the data contract for the task: entities, data flows, required sources, output schema, validation rules, and breaking assumptions. Layer 3 specialists must honor this contract.

### Metacognition Engine
Gates what APEX can actually dispatch. If internal confidence thresholds aren't met, tasks don't propagate — preventing execution with false certainty.

### APEX Commander
Decomposes the task into a dispatch plan for Layer 3, constrained by the adversarial prior, data model plan, and metacognition gate output.

---

## Layer 2 — UPS Probabilistic Intelligence

### Calibration Auditor
Backtests continuously using Expected Calibration Error (ECE) and conformal prediction coverage. Miscalibrated agents are flagged back to the Layer 4 Evolver.

### Uncertainty Decomposition
Predictions are never collapsed to point estimates. Every decision node outputs a full probability distribution with separated aleatoric (irreducible) and epistemic (model-level) uncertainty.

### Decision Gate
Enforces action thresholds. Below-threshold signals trigger escalation before action — not after failure.

---

## Layer 3 — Specialist Execution

| Agent | Primary Tool | Design Constraint |
|-------|-------------|-------------------|
| Research | Context7 MCP (pre-flight) | Zero hallucinated API calls |
| Creative | Psychological lever taxonomy | Schwartz buyer-awareness calibration |
| Analytics | Evidence hierarchy enforcement | Validated data → inference → speculation |
| Sales | Decision journey mapping | Friction points by stage, not generic objections |

---

## Layer 4 — Adversarial Quality

### Hostile Auditor
Finds the weakest points in any Layer 3 output before it reaches action.

### Debate Agent
Runs on high-stakes decisions only. Forces competing positions before synthesis. Activated on T3 Contested routing.

### Evolver
Writes its own remediation playbook from Hostile Auditor findings and human corrections stored in episodic memory. Correction loop includes damping: max 3 iterations, minimum delta threshold, automatic HITL escalation on non-convergence.

---

## Layer 5 — Integration

### Context7
Pre-flight validation for all code-generating agents. Agents request documentation dynamically at runtime — not from training-time knowledge. Eliminates entire categories of hallucination.

### Zapier (Outbound Action Bus)
APEX decisions become real-world events (CRM updates, email sequences, Slack alerts) without any agent needing direct system knowledge. Decision and execution are cleanly separated.

### MCP Tool Bus
15+ MCP servers connected via A2A protocol. Agents request tools dynamically at runtime — no hardcoded integrations.

---

## Memory Architecture

| Layer | Storage | Retention | Purpose |
|-------|---------|-----------|----------|
| Working | In-process | Task lifetime | Current task context |
| Episodic | pgvector (PostgreSQL) | Permanent | Past decisions + outcomes + human corrections |
| Semantic | PostgreSQL | Slow update | Domain knowledge, doctrine |
| Procedural | PostgreSQL | Versioned | Rube Recipes, proven workflow patterns |

---

## Observability Spine

Langfuse is attached to the compiled LangGraph workflow once. Every node invocation in every workflow run is auto-traced — no per-node callback code. Every trace captures:
- Prompt version and model snapshot
- Token usage, latency, cost
- Confidence and uncertainty values
- Human correction events

---

## Circuit Breakers

Every external integration has a circuit breaker registered in apex-core:

```
Closed   → normal, requests pass through
Open     → tripped after 3 failures, fail fast for 30s
HalfOpen → one probe request allowed; success → Closed, failure → Open
```

When open: agents fall back to cached data or HITL rather than failing silently.

---

## Security Baseline

- All credentials from environment variables — never hardcoded
- Prompt injection detection at every A2A message ingestion point
- Least-privilege per agent (Research ≠ Stripe write access)
- Append-only audit log enforced at database rule level
- CI scans every push for hardcoded API key patterns
