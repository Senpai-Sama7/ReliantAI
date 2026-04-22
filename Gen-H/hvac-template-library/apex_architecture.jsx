import { useState, useEffect, useRef } from "react";

const LAYERS = [
  {
    id: "orchestration",
    label: "ORCHESTRATION LAYER",
    sublabel: "Cognitive Command",
    color: "#FF4D00",
    agents: [
      { id: "apex", name: "APEX Commander", role: "Planner / Goal Arbitrator", icon: "◈", desc: "Master orchestrator. Decomposes tasks, assigns agents, arbitrates goal conflicts. Constitutional constraint engine enforces hard limits before any action propagates." },
      { id: "theory-of-mind", name: "Theory-of-Mind Agent", role: "Intent Modeler / Adversary Simulator", icon: "◉", desc: "Models stakeholder intent, competitive behavior, and escalation paths. Informs all downstream agents with adversarial priors before execution." },
      { id: "meta", name: "Metacognition Engine", role: "Self-Awareness / Confidence Gating", icon: "◎", desc: "Maintains real-time capability inventory and confidence thresholds. Gates action propagation — if confidence < threshold, escalates to human or alternate agent." },
    ],
  },
  {
    id: "intelligence",
    label: "PROBABILISTIC INTELLIGENCE LAYER",
    sublabel: "UPS Decision Stack",
    color: "#7C3AED",
    agents: [
      { id: "ups-answer", name: "UPS Answering Agent", role: "Probabilistic Forecaster", icon: "◆", desc: "Produces calibrated probability distributions, quantile intervals, and uncertainty decompositions for every decision node. Never collapses to point estimates." },
      { id: "ups-calibrate", name: "Calibration Auditor", role: "ECE / Coverage Verifier", icon: "◇", desc: "Continuously backtests predictions against outcomes. Computes Expected Calibration Error, applies conformal prediction coverage, and flags miscalibrated agents." },
      { id: "ups-ui", name: "Decision Intelligence UI", role: "Dashboard / Threshold Visualizer", icon: "▣", desc: "Live probabilistic dashboard. Renders uncertainty signals, semantic entropy disagreement across agents, and action thresholds with override controls." },
    ],
  },
  {
    id: "specialists",
    label: "SPECIALIST EXECUTION LAYER",
    sublabel: "Domain Agents",
    color: "#0EA5E9",
    agents: [
      { id: "research", name: "Research Agent", role: "Intelligence Gatherer — Context7 + Web", icon: "⟐", desc: "Pulls live documentation via Context7 MCP. Scours libraries, papers, platform specs. Synthesizes into structured intelligence packets for downstream agents." },
      { id: "creative", name: "Creative / Copy Agent", role: "Behavioral Copywriter", icon: "✦", desc: "Executes copy and creative production. Operates from psychological lever taxonomy: loss aversion, identity signaling, curiosity gaps. Buyer-awareness stage-calibrated." },
      { id: "analytics", name: "Analytics Agent", role: "Market Intelligence / Data Synthesis", icon: "⊕", desc: "Processes market data, audience psychographics, conversion signals. Distinguishes validated data from inference from speculation. Flags load-bearing assumptions." },
      { id: "sales", name: "Sales Architecture Agent", role: "Conversion / Friction Mapper", icon: "⊗", desc: "Maps full buyer decision journey. Identifies friction points at each stage. Designs interventions calibrated to awareness stage. Constructs objection taxonomy." },
    ],
  },
  {
    id: "quality",
    label: "ADVERSARIAL QUALITY LAYER",
    sublabel: "Trust Nothing",
    color: "#EF4444",
    agents: [
      { id: "auditor", name: "Hostile Auditor", role: "Adversarial Verifier", icon: "⚔", desc: "Executes everything. Trusts nothing. Produces PASS/FAIL verdicts with observable execution evidence — not review opinions. Default stance: nothing works until proven." },
      { id: "evolver", name: "Evolver / Self-Critic", role: "Self-Improvement Loop", icon: "↻", desc: "Runs self-reflection + self-criticism cycles post-output. Identifies failure modes, updates agent configurations, and propagates corrections to shared memory." },
      { id: "debate", name: "Debate Agent", role: "Adversarial Synthesizer", icon: "⇌", desc: "Forces competing positions on high-stakes decisions. Pro vs. Risk. Synthesizer produces balanced decision with explicit trade-off documentation." },
    ],
  },
  {
    id: "integration",
    label: "INTEGRATION & AUTOMATION LAYER",
    sublabel: "Connectors + MCP",
    color: "#10B981",
    agents: [
      { id: "context7", name: "Context7 Connector", role: "Live Documentation MCP", icon: "⊞", desc: "Real-time library and framework documentation retrieval. Eliminates hallucinated API calls. All code agents validate against Context7 before generation." },
      { id: "zapier", name: "Zapier Connector", role: "Automation Trigger Bus", icon: "⚡", desc: "Bidirectional automation. Agent decisions trigger Zapier workflows: CRM updates, Slack notifications, email sequences, data pipeline triggers across 5000+ apps." },
      { id: "rube", name: "Rube Connector", role: "Recipe Executor / Workflow Memory", icon: "⟳", desc: "Converts executed workflows into reusable recipes. Schedules recurring agent tasks. Maintains workflow memory so complex multi-step processes never rebuild from zero." },
      { id: "mcp", name: "MCP Tool Bus", role: "Universal Tool Interface", icon: "⬡", desc: "Unified MCP server access: Notion, HubSpot, Figma, Stripe, Sentry, Vercel, Hugging Face, S&P, Moody's. Agents request tools dynamically without hardcoded integrations." },
    ],
  },
];

const A2A_FLOWS = [
  { from: "apex", to: "theory-of-mind", label: "Intent Query" },
  { from: "apex", to: "ups-answer", label: "Decision Request" },
  { from: "apex", to: "research", label: "Task Dispatch" },
  { from: "apex", to: "creative", label: "Task Dispatch" },
  { from: "apex", to: "analytics", label: "Task Dispatch" },
  { from: "apex", to: "sales", label: "Task Dispatch" },
  { from: "ups-answer", to: "ups-calibrate", label: "Prediction Audit" },
  { from: "ups-calibrate", to: "ups-ui", label: "Calibration Signal" },
  { from: "meta", to: "apex", label: "Confidence Gate" },
  { from: "auditor", to: "evolver", label: "Failure Evidence" },
  { from: "evolver", to: "apex", label: "Config Update" },
  { from: "debate", to: "apex", label: "Synthesized Decision" },
  { from: "research", to: "context7", label: "Doc Fetch" },
  { from: "analytics", to: "zapier", label: "CRM Trigger" },
  { from: "apex", to: "rube", label: "Recipe Save" },
  { from: "sales", to: "mcp", label: "HubSpot Write" },
];

export default function APEXArchitecture() {
  const [selected, setSelected] = useState(null);
  const [activeFlow, setActiveFlow] = useState(null);
  const [pulse, setPulse] = useState(0);
  const [tab, setTab] = useState("architecture");

  useEffect(() => {
    const t = setInterval(() => setPulse(p => (p + 1) % 100), 80);
    return () => clearInterval(t);
  }, []);

  const allAgents = LAYERS.flatMap(l => l.agents.map(a => ({ ...a, layerColor: l.color, layerId: l.id })));
  const selectedAgent = allAgents.find(a => a.id === selected);

  return (
    <div style={{
      background: "#080810",
      minHeight: "100vh",
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      color: "#E2E8F0",
      padding: "0",
      overflow: "hidden auto"
    }}>
      {/* Header */}
      <div style={{
        background: "linear-gradient(135deg, #0D0D1A 0%, #080810 100%)",
        borderBottom: "1px solid #1E1E3A",
        padding: "24px 40px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        zIndex: 100,
        backdropFilter: "blur(20px)"
      }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{
              width: 10, height: 10, borderRadius: "50%",
              background: "#10B981",
              boxShadow: "0 0 12px #10B981",
              animation: "pulse 2s infinite"
            }} />
            <span style={{ fontSize: 11, color: "#10B981", letterSpacing: 4, fontWeight: 700 }}>SYSTEM ONLINE</span>
          </div>
          <h1 style={{
            fontSize: 28,
            fontWeight: 900,
            margin: "6px 0 0",
            letterSpacing: -1,
            background: "linear-gradient(90deg, #FF4D00, #7C3AED, #0EA5E9)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent"
          }}>APEX — Autonomous Probabilistic Execution System</h1>
          <p style={{ margin: "4px 0 0", fontSize: 11, color: "#64748B", letterSpacing: 2 }}>
            MULTI-AGENT COORDINATION ARCHITECTURE · A2A PROTOCOL · MCP TOOL BUS
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {["architecture", "a2a-flows", "integration-map"].map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              padding: "8px 16px",
              background: tab === t ? "#FF4D00" : "transparent",
              border: `1px solid ${tab === t ? "#FF4D00" : "#1E1E3A"}`,
              borderRadius: 4,
              color: tab === t ? "white" : "#64748B",
              fontSize: 10,
              letterSpacing: 2,
              cursor: "pointer",
              fontFamily: "inherit",
              textTransform: "uppercase",
              transition: "all 0.2s"
            }}>{t.replace("-", " ")}</button>
          ))}
        </div>
      </div>

      <div style={{ padding: "32px 40px", display: "flex", gap: 24 }}>
        {/* Main Content */}
        <div style={{ flex: 1 }}>
          {tab === "architecture" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {LAYERS.map(layer => (
                <div key={layer.id} style={{
                  border: `1px solid ${layer.color}22`,
                  borderRadius: 8,
                  overflow: "hidden",
                  background: `linear-gradient(135deg, ${layer.color}08 0%, transparent 100%)`
                }}>
                  <div style={{
                    padding: "10px 20px",
                    background: `${layer.color}15`,
                    borderBottom: `1px solid ${layer.color}30`,
                    display: "flex",
                    alignItems: "center",
                    gap: 12
                  }}>
                    <div style={{ width: 3, height: 18, background: layer.color, borderRadius: 2 }} />
                    <div>
                      <span style={{ fontSize: 10, letterSpacing: 4, color: layer.color, fontWeight: 700 }}>{layer.label}</span>
                      <span style={{ fontSize: 10, color: "#475569", marginLeft: 12 }}>— {layer.sublabel}</span>
                    </div>
                  </div>
                  <div style={{
                    display: "grid",
                    gridTemplateColumns: `repeat(${layer.agents.length <= 3 ? layer.agents.length : 4}, 1fr)`,
                    gap: 1,
                    padding: 1,
                    background: "#0A0A18"
                  }}>
                    {layer.agents.map(agent => (
                      <div key={agent.id}
                        onClick={() => setSelected(selected === agent.id ? null : agent.id)}
                        style={{
                          padding: "16px 18px",
                          background: selected === agent.id ? `${layer.color}20` : "#0D0D1C",
                          cursor: "pointer",
                          transition: "all 0.2s",
                          borderLeft: selected === agent.id ? `3px solid ${layer.color}` : "3px solid transparent",
                          position: "relative"
                        }}>
                        <div style={{ fontSize: 20, marginBottom: 6, color: layer.color }}>{agent.icon}</div>
                        <div style={{ fontSize: 12, fontWeight: 700, color: "#E2E8F0", marginBottom: 3 }}>{agent.name}</div>
                        <div style={{ fontSize: 9, color: layer.color, letterSpacing: 2, textTransform: "uppercase" }}>{agent.role}</div>
                        {selected === agent.id && (
                          <div style={{
                            marginTop: 10,
                            fontSize: 10,
                            color: "#94A3B8",
                            lineHeight: 1.6,
                            borderTop: `1px solid ${layer.color}30`,
                            paddingTop: 10
                          }}>{agent.desc}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {tab === "a2a-flows" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{
                padding: "16px 20px",
                background: "#0D0D1C",
                border: "1px solid #1E1E3A",
                borderRadius: 8,
                marginBottom: 8
              }}>
                <div style={{ fontSize: 10, color: "#64748B", letterSpacing: 3, marginBottom: 8 }}>A2A PROTOCOL — AGENT-TO-AGENT MESSAGE BUS</div>
                <p style={{ fontSize: 11, color: "#94A3B8", lineHeight: 1.7, margin: 0 }}>
                  Every agent communicates via typed message packets with UUID routing, priority classification,
                  and parent-message threading. The A2A bus enforces contract schemas — no agent can send
                  malformed payloads. Dead-letter queue captures failures for the Evolver's correction loop.
                </p>
              </div>
              {A2A_FLOWS.map((flow, i) => {
                const fromAgent = allAgents.find(a => a.id === flow.from);
                const toAgent = allAgents.find(a => a.id === flow.to);
                return (
                  <div key={i} style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: "12px 16px",
                    background: "#0D0D1C",
                    border: "1px solid #1E1E3A",
                    borderRadius: 6,
                    transition: "all 0.2s",
                    cursor: "default"
                  }}>
                    <div style={{
                      padding: "4px 10px",
                      background: `${fromAgent?.layerColor}20`,
                      border: `1px solid ${fromAgent?.layerColor}40`,
                      borderRadius: 4,
                      fontSize: 10,
                      color: fromAgent?.layerColor,
                      fontWeight: 700,
                      minWidth: 140,
                      textAlign: "center"
                    }}>{fromAgent?.icon} {fromAgent?.name}</div>
                    <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 8 }}>
                      <div style={{ flex: 1, height: 1, background: "#1E1E3A", position: "relative" }}>
                        <div style={{
                          position: "absolute",
                          top: -8,
                          left: "50%",
                          transform: "translateX(-50%)",
                          fontSize: 9,
                          color: "#475569",
                          letterSpacing: 2,
                          whiteSpace: "nowrap",
                          background: "#080810",
                          padding: "2px 8px"
                        }}>{flow.label}</div>
                      </div>
                      <span style={{ color: "#FF4D00", fontSize: 14 }}>→</span>
                    </div>
                    <div style={{
                      padding: "4px 10px",
                      background: `${toAgent?.layerColor}20`,
                      border: `1px solid ${toAgent?.layerColor}40`,
                      borderRadius: 4,
                      fontSize: 10,
                      color: toAgent?.layerColor,
                      fontWeight: 700,
                      minWidth: 140,
                      textAlign: "center"
                    }}>{toAgent?.icon} {toAgent?.name}</div>
                  </div>
                );
              })}
            </div>
          )}

          {tab === "integration-map" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              {[
                {
                  name: "Context7", color: "#10B981", icon: "⊞",
                  what: "Live MCP documentation server",
                  how: "All code-generating agents ping Context7 before output. Eliminates hallucinated API signatures. Research Agent uses it as primary intelligence source.",
                  triggers: ["Code generation pre-flight", "Library version validation", "Framework spec lookup"],
                  output: "Validated, current documentation packets injected into agent context"
                },
                {
                  name: "Zapier", color: "#FF9500", icon: "⚡",
                  what: "5000+ app automation trigger bus",
                  how: "APEX Commander publishes decision events to Zapier webhooks. Analytics Agent triggers CRM writes. Sales Agent fires email sequences on conversion events.",
                  triggers: ["Lead qualified → HubSpot contact created", "Decision logged → Slack alert", "Campaign live → Analytics dashboard update"],
                  output: "Cross-platform action propagation from agent decisions to external systems"
                },
                {
                  name: "Rube", color: "#7C3AED", icon: "⟳",
                  what: "Workflow recipe engine + persistent memory",
                  how: "Every executed multi-step workflow gets converted to a Rube Recipe. Scheduled tasks run autonomously. Workflow memory prevents rebuilding complex sequences from zero.",
                  triggers: ["Weekly market intelligence digest", "Daily calibration audit", "Recurring content production pipeline"],
                  output: "Reusable, scheduled, self-executing workflow recipes with audit trail"
                },
                {
                  name: "MCP Tool Bus", color: "#0EA5E9", icon: "⬡",
                  what: "Universal MCP server interface",
                  how: "Agents request tools dynamically via MCP protocol. No hardcoded integrations. APEX routes tool calls to: Notion (knowledge), HubSpot (sales), Figma (design), Stripe (payments), Sentry (monitoring), Vercel (deploy), Moody's/S&P (finance).",
                  triggers: ["Notion page creation", "Stripe payment event", "Sentry error escalation", "Figma design handoff"],
                  output: "Any agent can use any tool without pre-configuration — pure dynamic capability"
                }
              ].map(connector => (
                <div key={connector.name} style={{
                  background: "#0D0D1C",
                  border: `1px solid ${connector.color}30`,
                  borderRadius: 8,
                  padding: 24,
                  borderTop: `3px solid ${connector.color}`
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                    <span style={{ fontSize: 24, color: connector.color }}>{connector.icon}</span>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: "#E2E8F0" }}>{connector.name}</div>
                      <div style={{ fontSize: 10, color: connector.color, letterSpacing: 2 }}>{connector.what}</div>
                    </div>
                  </div>
                  <p style={{ fontSize: 11, color: "#94A3B8", lineHeight: 1.7, margin: "0 0 14px" }}>{connector.how}</p>
                  <div style={{ marginBottom: 10 }}>
                    <div style={{ fontSize: 9, color: "#475569", letterSpacing: 3, marginBottom: 6 }}>TRIGGER EXAMPLES</div>
                    {connector.triggers.map((t, i) => (
                      <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 6, marginBottom: 4 }}>
                        <span style={{ color: connector.color, fontSize: 10, marginTop: 1 }}>▸</span>
                        <span style={{ fontSize: 10, color: "#64748B" }}>{t}</span>
                      </div>
                    ))}
                  </div>
                  <div style={{
                    padding: "8px 12px",
                    background: `${connector.color}10`,
                    border: `1px solid ${connector.color}20`,
                    borderRadius: 4,
                    fontSize: 10,
                    color: connector.color,
                    fontStyle: "italic"
                  }}>↳ {connector.output}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div style={{ width: 280, flexShrink: 0, display: "flex", flexDirection: "column", gap: 16 }}>
          {/* System Vitals */}
          <div style={{ background: "#0D0D1C", border: "1px solid #1E1E3A", borderRadius: 8, padding: 20 }}>
            <div style={{ fontSize: 9, color: "#475569", letterSpacing: 3, marginBottom: 14 }}>SYSTEM VITALS</div>
            {[
              { label: "Active Agents", value: "13", color: "#10B981" },
              { label: "A2A Flows", value: `${A2A_FLOWS.length}`, color: "#0EA5E9" },
              { label: "Connectors Live", value: "4", color: "#7C3AED" },
              { label: "MCP Servers", value: "15+", color: "#FF4D00" },
              { label: "Layers", value: "5", color: "#FF9500" },
            ].map(v => (
              <div key={v.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <span style={{ fontSize: 10, color: "#64748B" }}>{v.label}</span>
                <span style={{ fontSize: 14, fontWeight: 700, color: v.color }}>{v.value}</span>
              </div>
            ))}
          </div>

          {/* Operational Modes */}
          <div style={{ background: "#0D0D1C", border: "1px solid #1E1E3A", borderRadius: 8, padding: 20 }}>
            <div style={{ fontSize: 9, color: "#475569", letterSpacing: 3, marginBottom: 14 }}>OPERATIVE MODES</div>
            {[
              { mode: "ANALYTICAL", color: "#0EA5E9", active: true },
              { mode: "CREATIVE", color: "#10B981", active: true },
              { mode: "STRATEGIC", color: "#7C3AED", active: true },
              { mode: "PERSUASIVE", color: "#FF4D00", active: true },
              { mode: "ADVERSARIAL", color: "#EF4444", active: true },
            ].map(m => (
              <div key={m.mode} style={{
                display: "flex", alignItems: "center", gap: 8, marginBottom: 8,
                padding: "6px 10px",
                background: m.active ? `${m.color}15` : "transparent",
                borderRadius: 4,
                border: `1px solid ${m.active ? m.color + "40" : "transparent"}`
              }}>
                <div style={{ width: 6, height: 6, borderRadius: "50%", background: m.active ? m.color : "#1E1E3A" }} />
                <span style={{ fontSize: 9, letterSpacing: 3, color: m.active ? m.color : "#475569", fontWeight: 700 }}>{m.mode}</span>
              </div>
            ))}
          </div>

          {/* Quality Stack */}
          <div style={{ background: "#0D0D1C", border: "1px solid #1E1E3A", borderRadius: 8, padding: 20 }}>
            <div style={{ fontSize: 9, color: "#475569", letterSpacing: 3, marginBottom: 14 }}>QUALITY ENFORCEMENT</div>
            {[
              "No generic positioning outputs",
              "No false urgency / dark patterns",
              "No demographic-only profiling",
              "No unstress-tested strategy",
              "No unverified numerical claims",
              "Confidence gates block low-certainty actions",
              "Hostile Auditor runs on all outputs",
              "Evolver closes every correction loop",
            ].map((rule, i) => (
              <div key={i} style={{ display: "flex", gap: 8, marginBottom: 7, alignItems: "flex-start" }}>
                <span style={{ color: "#EF4444", fontSize: 10, marginTop: 1 }}>✕</span>
                <span style={{ fontSize: 10, color: "#64748B", lineHeight: 1.5 }}>{rule}</span>
              </div>
            ))}
          </div>

          {/* A2A Protocol Schema */}
          <div style={{ background: "#0D0D1C", border: "1px solid #1E1E3A", borderRadius: 8, padding: 20 }}>
            <div style={{ fontSize: 9, color: "#475569", letterSpacing: 3, marginBottom: 14 }}>A2A MESSAGE SCHEMA</div>
            <pre style={{
              fontSize: 9,
              color: "#94A3B8",
              margin: 0,
              lineHeight: 1.7,
              background: "#080810",
              padding: 12,
              borderRadius: 4,
              overflowX: "auto"
            }}>{`{
  msg_id: "uuid-v4",
  ts: "ISO-8601",
  from: "agent-id",
  to: "agent-id|*",
  type: "request|response
        |notify|error",
  priority: "critical|high
             |medium|low",
  context: {
    task_id: "uuid",
    parent: "uuid",
    confidence: 0.87
  },
  payload: {
    type: "decision|data
           |audit|correction",
    content: {...},
    uncertainty: {
      aleatoric: 0.12,
      epistemic: 0.05
    }
  }
}`}</pre>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}
