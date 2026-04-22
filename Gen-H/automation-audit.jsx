import { useState, useEffect, useRef } from "react";

const STEPS = [
  {
    id: "role",
    question: "What's your role?",
    type: "choice",
    options: ["Founder / CEO", "Operations", "Marketing", "Sales", "IT / Engineering"],
  },
  {
    id: "companySize",
    question: "How many people are on your team?",
    type: "choice",
    options: ["1–5", "6–25", "26–100", "100+"],
  },
  {
    id: "painPoint",
    question: "Where does your team lose the most time?",
    type: "choice",
    options: [
      "Manual data entry & reporting",
      "Lead follow-up & outreach",
      "Content creation & distribution",
      "Customer onboarding & support",
    ],
  },
  {
    id: "tools",
    question: "Which tools does your team currently use?",
    type: "multichoice",
    options: ["HubSpot / CRM", "Zapier / Make", "Slack / Teams", "Spreadsheets", "None / Ad-hoc"],
  },
  {
    id: "urgency",
    question: "How urgent is solving this?",
    type: "choice",
    options: ["Critical — bleeding time/money now", "Important — within next quarter", "Exploring — no timeline yet"],
  },
  {
    id: "email",
    question: "Where should we send your full audit report?",
    type: "email",
  },
];

const PALETTE = {
  bg: "#0a0a0f",
  surface: "#12121a",
  border: "#1e1e2e",
  accent: "#e8ff47",
  accentDim: "#b8cc2a",
  text: "#f0f0f5",
  muted: "#5a5a7a",
  highlight: "#1a1a2e",
};

export default function AutomationAudit() {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({});
  const [selected, setSelected] = useState([]);
  const [emailVal, setEmailVal] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [visible, setVisible] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    setVisible(false);
    const t = setTimeout(() => setVisible(true), 60);
    setSelected([]);
    setEmailVal("");
    return () => clearTimeout(t);
  }, [step]);

  useEffect(() => {
    if (STEPS[step]?.type === "email" && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 200);
    }
  }, [step]);

  const current = STEPS[step];
  const progress = step / STEPS.length;

  function handleChoice(opt) {
    const next = { ...answers, [current.id]: opt };
    setAnswers(next);
    setTimeout(() => setStep(step + 1), 180);
  }

  function toggleMulti(opt) {
    setSelected((prev) =>
      prev.includes(opt) ? prev.filter((x) => x !== opt) : [...prev, opt]
    );
  }

  function handleMultiNext() {
    const next = { ...answers, [current.id]: selected };
    setAnswers(next);
    setStep(step + 1);
  }

  async function handleEmailSubmit() {
    if (!emailVal || !emailVal.includes("@")) return;
    const finalAnswers = { ...answers, email: emailVal };
    setAnswers(finalAnswers);
    setLoading(true);
    setError(null);

    try {
      const prompt = `You are an automation consultant. Based on this intake survey, generate a highly specific Automation Opportunity Audit.

Survey data:
- Role: ${finalAnswers.role}
- Team size: ${finalAnswers.companySize}
- Biggest time drain: ${finalAnswers.painPoint}
- Current tools: ${Array.isArray(finalAnswers.tools) ? finalAnswers.tools.join(", ") : finalAnswers.tools}
- Urgency: ${finalAnswers.urgency}

Respond ONLY with a valid JSON object, no markdown, no backticks, no preamble:
{
  "score": <number 0-100, automation readiness score>,
  "headline": "<one sharp sentence about their biggest opportunity>",
  "topOpportunities": [
    {"title": "<opportunity name>", "impact": "<High|Medium>", "effort": "<Low|Medium|High>", "description": "<2 sentence specific description>"},
    {"title": "...", "impact": "...", "effort": "...", "description": "..."},
    {"title": "...", "impact": "...", "effort": "...", "description": "..."}
  ],
  "quickWin": "<one specific action they can take this week, tool-specific>",
  "estimatedHoursSaved": <number per week>,
  "verdict": "<2-3 sentence honest assessment of where they stand>"
}`;

      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          messages: [{ role: "user", content: prompt }],
        }),
      });

      const data = await response.json();
      const raw = data.content?.find((b) => b.type === "text")?.text || "";
      const cleaned = raw.replace(/```json|```/g, "").trim();
      const parsed = JSON.parse(cleaned);
      setResult(parsed);
    } catch (e) {
      setError("Something went wrong generating your audit. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const impactColor = (v) => (v === "High" ? PALETTE.accent : "#7eb8f7");
  const effortColor = (v) =>
    v === "Low" ? "#7ef7a0" : v === "Medium" ? "#f7d97e" : "#f77e7e";

  if (result) {
    return (
      <div style={styles.root}>
        <GridBg />
        <div style={{ ...styles.card, maxWidth: 680, animation: "fadeUp 0.5s ease forwards" }}>
          <div style={styles.scoreRow}>
            <div style={styles.scoreBadge}>
              <span style={styles.scoreNum}>{result.score}</span>
              <span style={styles.scoreLabel}>/ 100</span>
            </div>
            <div>
              <div style={styles.tag}>AUTOMATION READINESS SCORE</div>
              <p style={styles.headline}>{result.headline}</p>
            </div>
          </div>

          <div style={styles.divider} />

          <p style={{ ...styles.muted, marginBottom: 24 }}>{result.verdict}</p>

          <div style={styles.sectionLabel}>TOP OPPORTUNITIES</div>
          <div style={styles.oppGrid}>
            {result.topOpportunities.map((opp, i) => (
              <div key={i} style={styles.oppCard}>
                <div style={styles.oppHeader}>
                  <span style={styles.oppTitle}>{opp.title}</span>
                  <div style={styles.badgeRow}>
                    <span style={{ ...styles.badge, color: impactColor(opp.impact), borderColor: impactColor(opp.impact) }}>
                      {opp.impact} Impact
                    </span>
                    <span style={{ ...styles.badge, color: effortColor(opp.effort), borderColor: effortColor(opp.effort) }}>
                      {opp.effort} Effort
                    </span>
                  </div>
                </div>
                <p style={styles.oppDesc}>{opp.description}</p>
              </div>
            ))}
          </div>

          <div style={styles.winBox}>
            <div style={styles.winLabel}>⚡ THIS WEEK'S QUICK WIN</div>
            <p style={styles.winText}>{result.quickWin}</p>
            <div style={styles.hoursRow}>
              <span style={styles.hoursNum}>{result.estimatedHoursSaved}</span>
              <span style={styles.hoursSub}>hours saved/week estimated</span>
            </div>
          </div>

          <p style={{ ...styles.muted, fontSize: 12, marginTop: 24, textAlign: "center" }}>
            Full report sent to your inbox · Powered by Houston Oil Airs
          </p>
        </div>
        <style>{keyframes}</style>
      </div>
    );
  }

  return (
    <div style={styles.root}>
      <GridBg />
      <div style={styles.card}>
        {/* Header */}
        <div style={styles.header}>
          <div style={styles.logo}>⬡ AUTOMATION AUDIT</div>
          <div style={styles.progressTrack}>
            <div style={{ ...styles.progressFill, width: `${progress * 100}%` }} />
          </div>
        </div>

        {loading ? (
          <div style={styles.loadingBox}>
            <div style={styles.spinner} />
            <p style={styles.loadingText}>Analyzing your automation profile…</p>
          </div>
        ) : (
          <div
            style={{
              opacity: visible ? 1 : 0,
              transform: visible ? "translateY(0)" : "translateY(16px)",
              transition: "opacity 0.3s ease, transform 0.3s ease",
            }}
          >
            <div style={styles.stepCount}>
              {step + 1} / {STEPS.length}
            </div>
            <h2 style={styles.question}>{current.question}</h2>

            {(current.type === "choice") && (
              <div style={styles.optionList}>
                {current.options.map((opt) => (
                  <button key={opt} style={styles.optionBtn} onClick={() => handleChoice(opt)}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = PALETTE.accent; e.currentTarget.style.color = PALETTE.accent; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = PALETTE.border; e.currentTarget.style.color = PALETTE.text; }}>
                    {opt}
                  </button>
                ))}
              </div>
            )}

            {current.type === "multichoice" && (
              <div>
                <div style={styles.optionList}>
                  {current.options.map((opt) => {
                    const active = selected.includes(opt);
                    return (
                      <button key={opt}
                        style={{ ...styles.optionBtn, borderColor: active ? PALETTE.accent : PALETTE.border, color: active ? PALETTE.accent : PALETTE.text, background: active ? "rgba(232,255,71,0.06)" : "transparent" }}
                        onClick={() => toggleMulti(opt)}>
                        {active ? "✓ " : ""}{opt}
                      </button>
                    );
                  })}
                </div>
                {selected.length > 0 && (
                  <button style={styles.nextBtn} onClick={handleMultiNext}>
                    Continue →
                  </button>
                )}
              </div>
            )}

            {current.type === "email" && (
              <div style={styles.emailBox}>
                <input
                  ref={inputRef}
                  type="email"
                  placeholder="your@email.com"
                  value={emailVal}
                  onChange={(e) => setEmailVal(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleEmailSubmit()}
                  style={styles.emailInput}
                />
                <button
                  style={{ ...styles.nextBtn, opacity: emailVal.includes("@") ? 1 : 0.4 }}
                  onClick={handleEmailSubmit}
                  disabled={!emailVal.includes("@")}>
                  Generate My Audit →
                </button>
                {error && <p style={{ color: "#f77e7e", marginTop: 12, fontSize: 13 }}>{error}</p>}
              </div>
            )}
          </div>
        )}
      </div>
      <style>{keyframes}</style>
    </div>
  );
}

function GridBg() {
  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 0,
      backgroundImage: `linear-gradient(rgba(232,255,71,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(232,255,71,0.03) 1px, transparent 1px)`,
      backgroundSize: "48px 48px",
      pointerEvents: "none",
    }} />
  );
}

const styles = {
  root: {
    minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
    background: PALETTE.bg, fontFamily: "'DM Mono', 'Courier New', monospace",
    padding: "24px 16px", position: "relative",
  },
  card: {
    position: "relative", zIndex: 1, width: "100%", maxWidth: 520,
    background: PALETTE.surface, border: `1px solid ${PALETTE.border}`,
    borderRadius: 2, padding: "40px 44px",
    boxShadow: `0 0 0 1px ${PALETTE.border}, 0 32px 64px rgba(0,0,0,0.6), 0 0 80px rgba(232,255,71,0.04)`,
  },
  header: { marginBottom: 40 },
  logo: { color: PALETTE.accent, fontSize: 11, letterSpacing: "0.2em", fontWeight: 600, marginBottom: 16 },
  progressTrack: { height: 2, background: PALETTE.border, borderRadius: 1 },
  progressFill: { height: "100%", background: PALETTE.accent, borderRadius: 1, transition: "width 0.4s ease" },
  stepCount: { color: PALETTE.muted, fontSize: 11, letterSpacing: "0.15em", marginBottom: 12 },
  question: { color: PALETTE.text, fontSize: 22, fontWeight: 400, lineHeight: 1.4, margin: "0 0 32px", fontFamily: "'DM Sans', sans-serif" },
  optionList: { display: "flex", flexDirection: "column", gap: 10 },
  optionBtn: {
    background: "transparent", border: `1px solid ${PALETTE.border}`, color: PALETTE.text,
    padding: "14px 18px", borderRadius: 2, cursor: "pointer", textAlign: "left",
    fontSize: 14, fontFamily: "inherit", transition: "all 0.15s ease", letterSpacing: "0.01em",
  },
  nextBtn: {
    marginTop: 20, width: "100%", background: PALETTE.accent, color: "#0a0a0f",
    border: "none", padding: "14px", borderRadius: 2, cursor: "pointer",
    fontSize: 13, fontWeight: 700, letterSpacing: "0.08em", fontFamily: "inherit",
    transition: "opacity 0.2s",
  },
  emailBox: { display: "flex", flexDirection: "column", gap: 0 },
  emailInput: {
    background: PALETTE.highlight, border: `1px solid ${PALETTE.border}`, color: PALETTE.text,
    padding: "14px 18px", borderRadius: 2, fontSize: 15, fontFamily: "inherit",
    outline: "none", marginBottom: 12,
  },
  loadingBox: { textAlign: "center", padding: "40px 0" },
  spinner: {
    width: 32, height: 32, border: `2px solid ${PALETTE.border}`,
    borderTop: `2px solid ${PALETTE.accent}`, borderRadius: "50%",
    animation: "spin 0.8s linear infinite", margin: "0 auto 20px",
  },
  loadingText: { color: PALETTE.muted, fontSize: 13, letterSpacing: "0.08em" },
  // Result styles
  scoreRow: { display: "flex", alignItems: "flex-start", gap: 24, marginBottom: 24 },
  scoreBadge: {
    flexShrink: 0, width: 90, height: 90, border: `2px solid ${PALETTE.accent}`,
    borderRadius: 2, display: "flex", alignItems: "center", justifyContent: "center",
    flexDirection: "column", background: "rgba(232,255,71,0.05)",
  },
  scoreNum: { color: PALETTE.accent, fontSize: 32, fontWeight: 700, lineHeight: 1 },
  scoreLabel: { color: PALETTE.muted, fontSize: 11 },
  tag: { color: PALETTE.accent, fontSize: 10, letterSpacing: "0.2em", marginBottom: 8 },
  headline: { color: PALETTE.text, fontSize: 17, fontWeight: 400, lineHeight: 1.5, margin: 0, fontFamily: "'DM Sans', sans-serif" },
  divider: { height: 1, background: PALETTE.border, margin: "0 0 20px" },
  muted: { color: PALETTE.muted, fontSize: 14, lineHeight: 1.6, margin: 0 },
  sectionLabel: { color: PALETTE.muted, fontSize: 10, letterSpacing: "0.2em", marginBottom: 14 },
  oppGrid: { display: "flex", flexDirection: "column", gap: 12, marginBottom: 24 },
  oppCard: { background: PALETTE.highlight, border: `1px solid ${PALETTE.border}`, borderRadius: 2, padding: "16px 18px" },
  oppHeader: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8, gap: 12, flexWrap: "wrap" },
  oppTitle: { color: PALETTE.text, fontSize: 14, fontWeight: 600 },
  badgeRow: { display: "flex", gap: 6, flexShrink: 0 },
  badge: { fontSize: 10, letterSpacing: "0.1em", border: "1px solid", padding: "2px 7px", borderRadius: 2 },
  oppDesc: { color: PALETTE.muted, fontSize: 13, lineHeight: 1.55, margin: 0 },
  winBox: {
    background: "rgba(232,255,71,0.04)", border: `1px solid rgba(232,255,71,0.2)`,
    borderRadius: 2, padding: "20px 22px",
  },
  winLabel: { color: PALETTE.accent, fontSize: 10, letterSpacing: "0.2em", marginBottom: 10 },
  winText: { color: PALETTE.text, fontSize: 14, lineHeight: 1.6, margin: "0 0 16px" },
  hoursRow: { display: "flex", alignItems: "baseline", gap: 8 },
  hoursNum: { color: PALETTE.accent, fontSize: 28, fontWeight: 700 },
  hoursSub: { color: PALETTE.muted, fontSize: 12 },
};

const keyframes = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;600&display=swap');
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes fadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
`;
