// src/app/page.tsx
"use client";

import { useState } from "react";
import { useHitlStream } from "@/hooks/useHitlStream";
import { HitlList } from "@/components/HitlList";
import { HitlDetail } from "@/components/HitlDetail";
import { CompletedWorkflows } from "@/components/CompletedWorkflows";

export default function Home() {
  const { connected, items, removeItem } = useHitlStream();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selectedItem =
    items.find((i) => i.thread_id === selectedId) || null;

  return (
    <main style={{ padding: "1.5rem", maxWidth: 1200, margin: "0 auto" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: "1.25rem",
          borderBottom: "2px solid #111827",
          paddingBottom: "0.75rem",
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: "1.5rem" }}>APEX HITL Dashboard</h1>
          <p style={{ margin: 0, fontSize: 13, color: "#6b7280" }}>
            Human-in-the-loop control for T3 / T4 decisions
          </p>
        </div>
        <div style={{ fontSize: 12, color: connected ? "#16a34a" : "#dc2626" }}>
          ● {connected ? "Stream connected" : "Stream disconnected"}
        </div>
      </header>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1.1fr) minmax(0, 2fr)",
          gap: "1rem",
        }}
      >
        <HitlList
          items={items}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
        <HitlDetail item={selectedItem} onResolved={removeItem} />
      </section>

      <CompletedWorkflows />
    </main>
  );
}
