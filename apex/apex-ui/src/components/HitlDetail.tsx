"use client";

import { useState } from "react";
import type { HitlItem } from "@/hooks/useHitlStream";
import { resumeWorkflow } from "@/lib/api";
import { UncertaintyGauge } from "./UncertaintyGauge";

type Props = {
  item: HitlItem | null;
  onResolved: (threadId: string) => void;
};

export function HitlDetail({ item, onResolved }: Props) {
  const [correction, setCorrection] = useState("");
  const [loading,    setLoading]    = useState<"approve" | "reject" | null>(null);
  const [error,      setError]      = useState<string | null>(null);

  if (!item) {
    return (
      <div style={{ paddingLeft: "1rem" }}>
        <h2 style={{ fontSize: 16, marginTop: 0 }}>Decision details</h2>
        <p style={{ color: "#9ca3af", fontSize: 14 }}>Select a workflow from the left to review it.</p>
      </div>
    );
  }

  async function decide(approved: boolean) {
    if (!item) return;
    setLoading(approved ? "approve" : "reject");
    setError(null);
    try {
      await resumeWorkflow(item.thread_id, { approved, correction: correction || null });
      onResolved(item.thread_id);
      setCorrection("");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(null);
    }
  }

  return (
    <div style={{ paddingLeft: "1rem" }}>
      <h2 style={{ fontSize: 16, marginTop: 0 }}>Decision details</h2>

      <p style={{ fontSize: 11, color: "#9ca3af", margin: "0 0 8px" }}>
        Thread: <code>{item.thread_id}</code>
      </p>

      <section style={{ marginBottom: "1rem" }}>
        <h3 style={{ fontSize: 14, margin: "0 0 4px" }}>Task</h3>
        <p style={{ margin: 0, fontSize: 14, background: "white", border: "1px solid #e5e7eb", borderRadius: 6, padding: "0.5rem 0.75rem" }}>
          {item.task}
        </p>
      </section>

      <section style={{ marginBottom: "1rem" }}>
        <h3 style={{ fontSize: 14, margin: "0 0 4px" }}>Uncertainty analysis</h3>
        <UncertaintyGauge
          confidence={item.confidence}
          failureModes={item.failure_modes}
          epistemicGaps={item.epistemic_gaps}
        />
      </section>

      <section style={{ marginBottom: "1rem" }}>
        <h3 style={{ fontSize: 14, margin: "0 0 4px" }}>Correction (optional)</h3>
        <p style={{ fontSize: 12, color: "#6b7280", margin: "0 0 4px" }}>
          Corrections are stored to episodic memory and used by the Evolver agent as a learning signal.
        </p>
        <textarea
          value={correction}
          onChange={(e) => setCorrection(e.target.value)}
          placeholder="e.g. Only charge accounts overdue >60 days, not >30 days"
          style={{
            width: "100%",
            minHeight: 70,
            padding: 8,
            borderRadius: 6,
            border: "1px solid #d1d5db",
            fontFamily: "inherit",
            fontSize: 13,
            boxSizing: "border-box",
          }}
        />
      </section>

      {error && <p style={{ color: "#dc2626", fontSize: 13 }}>Error: {error}</p>}

      <section style={{ display: "flex", gap: 8 }}>
        <button
          onClick={() => decide(true)}
          disabled={loading !== null}
          style={{
            padding: "0.5rem 1rem",
            borderRadius: 6,
            border: "none",
            background: "#16a34a",
            color: "white",
            cursor: "pointer",
            opacity: loading === "approve" ? 0.6 : 1,
            fontSize: 14,
            fontWeight: 500,
          }}
        >
          {loading === "approve" ? "Approving…" : "✓ Approve"}
        </button>
        <button
          onClick={() => decide(false)}
          disabled={loading !== null}
          style={{
            padding: "0.5rem 1rem",
            borderRadius: 6,
            border: "1px solid #dc2626",
            background: "white",
            color: "#dc2626",
            cursor: "pointer",
            opacity: loading === "reject" ? 0.6 : 1,
            fontSize: 14,
            fontWeight: 500,
          }}
        >
          {loading === "reject" ? "Rejecting…" : "✕ Reject"}
        </button>
      </section>

      {item.auto_approve_eligible && item.auto_approve_at && (
        <p style={{ marginTop: 10, fontSize: 11, color: "#6b7280" }}>
          ⏱ Auto-approval scheduled: {new Date(item.auto_approve_at).toLocaleTimeString()}
        </p>
      )}
    </div>
  );
}
