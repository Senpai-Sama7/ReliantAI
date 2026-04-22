"use client";

import { useEffect, useRef, useState } from "react";

export function useEventSource<T = unknown>(url: string | null) {
  const [events, setEvents] = useState<T[]>([]);
  const [connected, setConnected] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!url) return;

    const es = new EventSource(url);
    sourceRef.current = es;

    es.onopen  = () => setConnected(true);
    es.onerror = () => setConnected(false);
    es.onmessage = (ev) => {
      try {
        const parsed = JSON.parse(ev.data as string);
        // Skip internal heartbeat/connect events
        if ((parsed as Record<string, unknown>).type === "connected") return;
        setEvents((prev) => [...prev, parsed as T]);
      } catch {
        // Ignore non-JSON frames
      }
    };

    return () => {
      es.close();
      setConnected(false);
    };
  }, [url]);

  return { events, connected };
}
