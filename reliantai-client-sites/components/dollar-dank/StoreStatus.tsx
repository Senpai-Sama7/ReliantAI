"use client";

import { useEffect, useState } from "react";

const TZ = "America/Chicago";
const OPEN = 8;
const CLOSE = 2;

function status() {
  const hour = parseInt(
    new Intl.DateTimeFormat("en-US", { timeZone: TZ, hour: "numeric", hour12: false }).format(
      new Date()
    ),
    10
  );
  const time = new Intl.DateTimeFormat("en-US", {
    timeZone: TZ,
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(new Date());

  const isOpen = hour >= OPEN || hour < CLOSE;
  return { isOpen, time };
}

export default function StoreStatus({ inline = false }: { inline?: boolean }) {
  const [s, setS] = useState(status);

  useEffect(() => {
    const id = setInterval(() => setS(status()), 60_000);
    return () => clearInterval(id);
  }, []);

  if (inline) {
    return (
      <span className="inline-flex items-center gap-2 text-sm text-[var(--dd-muted)]">
        <span
          className={`w-1.5 h-1.5 rounded-full ${s.isOpen ? "bg-[var(--dd-green)] dd-open-dot" : "bg-[var(--dd-red)]"}`}
        />
        {s.isOpen ? "Open now" : "Closed"} · Houston {s.time}
      </span>
    );
  }

  return (
    <div className="flex items-center justify-between gap-4 py-4 px-5 border border-[var(--dd-line)] rounded-[var(--dd-radius)] bg-[var(--dd-surface)]">
      <div className="flex items-center gap-3">
        <span
          className={`w-2 h-2 rounded-full shrink-0 ${s.isOpen ? "bg-[var(--dd-green)] dd-open-dot" : "bg-[var(--dd-red)]"}`}
        />
        <div>
          <p className="text-sm font-medium">{s.isOpen ? "Open now" : "Closed for the night"}</p>
          <p className="text-xs text-[var(--dd-muted)] mt-0.5">Houston · {s.time}</p>
        </div>
      </div>
      <p className="text-xs text-[var(--dd-muted)] text-right">
        Daily
        <br />
        <span className="text-[var(--dd-text)] font-medium">8AM – 2AM</span>
      </p>
    </div>
  );
}
