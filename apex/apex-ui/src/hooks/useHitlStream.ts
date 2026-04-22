"use client";

import { useEffect, useMemo, useState } from "react";
import { useEventSource } from "./useEventSource";
import { listPendingHitl } from "@/lib/api";

export type HitlItem = {
  thread_id: string;
  task: string;
  routing_tier: string;
  confidence: number;
  failure_modes: string[];
  epistemic_gaps: string[];
  auto_approve_eligible: boolean;
  auto_approve_at: string | null;
  created_at: string;
};

// Relative URL — proxied through Next.js server, works in both dev and Docker
const STREAM_URL = "/api/proxy/hitl-stream";

function toItem(raw: Record<string, unknown>, fallback?: HitlItem): HitlItem {
  const parseList = (v: unknown): string[] => {
    if (Array.isArray(v)) return v as string[];
    if (typeof v === "string") {
      try { return JSON.parse(v) as string[]; } catch { return []; }
    }
    return [];
  };
  return {
    thread_id:             String(raw.thread_id || ""),
    task:                  String(raw.task || fallback?.task || ""),
    routing_tier:          String(raw.routing_tier || fallback?.routing_tier || "unknown"),
    confidence:            Number(raw.confidence ?? fallback?.confidence ?? 0),
    failure_modes:         parseList(raw.failure_modes) || fallback?.failure_modes || [],
    epistemic_gaps:        parseList(raw.epistemic_gaps) || fallback?.epistemic_gaps || [],
    auto_approve_eligible: raw.auto_approve_eligible === true || raw.auto_approve_eligible === "True",
    auto_approve_at:       (raw.auto_approve_at as string | null) ?? fallback?.auto_approve_at ?? null,
    created_at:            String(raw.created_at || fallback?.created_at || new Date().toISOString()),
  };
}

export function useHitlStream() {
  const { events, connected } = useEventSource<Record<string, unknown>>(STREAM_URL);
  const [items, setItems] = useState<Record<string, HitlItem>>({});

  // Seed from REST on mount to pick up any already-pending decisions
  useEffect(() => {
    listPendingHitl()
      .then((pending) => {
        const map: Record<string, HitlItem> = {};
        for (const raw of pending) {
          const r = raw as Record<string, unknown>;
          const id = String(r.thread_id || "");
          if (id) map[id] = toItem(r);
        }
        setItems(map);
      })
      .catch(() => { /* dashboard still renders */ });
  }, []);

  // Merge live SSE events
  useEffect(() => {
    if (!events.length) return;
    setItems((prev) => {
      const copy = { ...prev };
      for (const ev of events) {
        const id = String(ev.thread_id || "");
        if (!id) continue;
        copy[id] = toItem(ev, copy[id]);
      }
      return copy;
    });
  }, [events]);

  const list = useMemo(
    () => Object.values(items).sort((a, b) => a.created_at.localeCompare(b.created_at)),
    [items]
  );

  const removeItem = (threadId: string) =>
    setItems((prev) => { const c = { ...prev }; delete c[threadId]; return c; });

  return { connected, items: list, removeItem };
}
