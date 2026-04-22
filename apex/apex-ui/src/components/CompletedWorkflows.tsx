// src/components/CompletedWorkflows.tsx
"use client";

import { useEffect, useState } from "react";

type CompletedItem = {
  trace_id:    string;
  sender:      string;
  tier:        string;
  action_taken: string | null;
  confidence:  number;
  created_at:  string;
};

const API_BASE =
  process.env.NEXT_PUBLIC_AGENT_API_URL || "http://localhost:8001";

export function CompletedWorkflows() {
  const [items, setItems]   = useState<CompletedItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/workflow/completed`)
      .then((r) => r.json())
      .then((d) => setItems(d.completed || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section style={{ marginTop: "2rem" }}>
      <h2>Completed decisions</h2>
      {loading && <p style={{ color: "#6b7280" }}>Loading…</p>}
      {!loading && items.length === 0 && (
        <p style={{ color: "#6b7280" }}>No completed decisions yet.</p>
      )}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        {items.length > 0 && (
          <thead>
            <tr style={{ borderBottom: "2px solid #e5e7eb", textAlign: "left" }}>
              <th style={{ padding: "6px 8px" }}>Timestamp</th>
              <th style={{ padding: "6px 8px" }}>Tier</th>
              <th style={{ padding: "6px 8px" }}>Sender</th>
              <th style={{ padding: "6px 8px" }}>Confidence</th>
              <th style={{ padding: "6px 8px" }}>Action</th>
              <th style={{ padding: "6px 8px" }}>Trace</th>
            </tr>
          </thead>
        )}
        <tbody>
          {items.map((item) => (
            <tr
              key={item.trace_id + item.created_at}
              style={{ borderBottom: "1px solid #f3f4f6" }}
            >
              <td style={{ padding: "6px 8px", color: "#6b7280" }}>
                {new Date(item.created_at).toLocaleString()}
              </td>
              <td style={{ padding: "6px 8px" }}>
                <TierBadge tier={item.tier} />
              </td>
              <td style={{ padding: "6px 8px" }}>{item.sender}</td>
              <td style={{ padding: "6px 8px" }}>
                {item.confidence != null
                  ? `${Math.round(item.confidence * 100)}%`
                  : "—"}
              </td>
              <td style={{ padding: "6px 8px" }}>{item.action_taken || "—"}</td>
              <td style={{ padding: "6px 8px" }}>
                <code style={{ fontSize: 11 }}>
                  {item.trace_id.slice(0, 8)}…
                </code>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function TierBadge({ tier }: { tier: string }) {
  const colors: Record<string, string> = {
    T1Reflexive:    "#16a34a",
    T2Deliberative: "#2563eb",
    T3Contested:    "#d97706",
    T4Unknown:      "#dc2626",
    HITL:           "#7c3aed",
  };
  return (
    <span
      style={{
        background: colors[tier] || "#6b7280",
        color: "white",
        borderRadius: 4,
        padding: "2px 6px",
        fontSize: 11,
      }}
    >
      {tier}
    </span>
  );
}
