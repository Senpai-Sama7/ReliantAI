"use client";

type Props = {
  confidence: number;
  failureModes: string[];
  epistemicGaps: string[];
};

export function UncertaintyGauge({ confidence, failureModes, epistemicGaps }: Props) {
  const pct   = Math.round(confidence * 100);
  const color = pct >= 90 ? "#16a34a" : pct >= 70 ? "#eab308" : "#dc2626";
  const label = pct >= 90 ? "High" : pct >= 70 ? "Medium" : "Low";

  return (
    <div style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: "0.75rem", marginBottom: "0.75rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <strong style={{ fontSize: 14 }}>Confidence</strong>
        <span style={{ color, fontWeight: 700 }}>{pct}% — {label}</span>
      </div>
      <div style={{ marginTop: 6, height: 6, borderRadius: 999, background: "#e5e7eb", overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, transition: "width 0.4s ease" }} />
      </div>

      {failureModes.length > 0 && (
        <div style={{ marginTop: 10, fontSize: 12 }}>
          <strong>Top failure modes:</strong>
          <ul style={{ margin: "4px 0 0 0", paddingLeft: 16 }}>
            {failureModes.map((m, i) => <li key={i} style={{ color: "#374151" }}>{m}</li>)}
          </ul>
        </div>
      )}

      {epistemicGaps.length > 0 && (
        <div style={{ marginTop: 8, fontSize: 12 }}>
          <strong>Epistemic gaps (what APEX doesn’t know):</strong>
          <ul style={{ margin: "4px 0 0 0", paddingLeft: 16 }}>
            {epistemicGaps.map((g, i) => <li key={i} style={{ color: "#6b7280" }}>{g}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
