"use client";

import type { HitlItem } from "@/hooks/useHitlStream";

type Props = {
  items: HitlItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

export function HitlList({ items, selectedId, onSelect }: Props) {
  return (
    <div style={{ borderRight: "1px solid #e5e7eb", paddingRight: "1rem", overflowY: "auto", maxHeight: "80vh" }}>
      <h2 style={{ marginTop: 0, fontSize: 16 }}>Pending decisions</h2>

      {items.length === 0 && (
        <p style={{ color: "#9ca3af", fontSize: 14 }}>No workflows waiting for review.</p>
      )}

      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {items.map((item) => {
          const pct = Math.round(item.confidence * 100);
          const isSelected = item.thread_id === selectedId;
          return (
            <li
              key={item.thread_id}
              onClick={() => onSelect(item.thread_id)}
              style={{
                marginBottom: "0.4rem",
                padding: "0.5rem 0.75rem",
                borderRadius: 6,
                cursor: "pointer",
                border: isSelected ? "1px solid #0ea5e9" : "1px solid #e5e7eb",
                background: isSelected ? "#e0f2fe" : "white",
              }}
            >
              <div style={{ fontSize: 11, color: "#6b7280", marginBottom: 2 }}>
                {item.routing_tier} · {new Date(item.created_at).toLocaleTimeString()}
              </div>
              <div style={{ fontWeight: 500, fontSize: 14, marginBottom: 2 }}>
                {item.task.slice(0, 72)}{item.task.length > 72 ? "…" : ""}
              </div>
              <div style={{ fontSize: 12, color: pct >= 70 ? "#16a34a" : "#dc2626" }}>
                Confidence: {pct}%
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
