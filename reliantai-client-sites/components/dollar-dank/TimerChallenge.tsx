"use client";

import { useEffect, useRef, useState } from "react";

type Phase = "idle" | "running" | "done";

const TARGET = 10.0;
const WIN = 0.03;

function fmt(n: number) {
  return n.toFixed(2);
}

export default function TimerChallenge() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [display, setDisplay] = useState("0.00");
  const [won, setWon] = useState(false);
  const start = useRef(0);
  const raf = useRef(0);

  const startLoop = () => {
    const step = () => {
      setDisplay(fmt((performance.now() - start.current) / 1000));
      raf.current = requestAnimationFrame(step);
    };
    raf.current = requestAnimationFrame(step);
  };

  const onTap = () => {
    if (phase === "idle" || phase === "done") {
      setWon(false);
      setPhase("running");
      start.current = performance.now();
      startLoop();
      return;
    }
    cancelAnimationFrame(raf.current);
    const elapsed = (performance.now() - start.current) / 1000;
    setDisplay(fmt(elapsed));
    setWon(Math.abs(elapsed - TARGET) <= WIN);
    setPhase("done");
  };

  useEffect(() => () => cancelAnimationFrame(raf.current), []);

  return (
    <div className="border border-[var(--dd-line)] rounded-[var(--dd-radius)] bg-[var(--dd-surface)] overflow-hidden">
      <div className="px-5 py-4 border-b border-[var(--dd-line)] flex items-center justify-between gap-4">
        <div>
          <p className="dd-label">In-store challenge</p>
          <p className="text-sm mt-1 text-[var(--dd-muted)]">
            Stop the clock at exactly 10.00 seconds
          </p>
        </div>
        <span className="text-xs text-[var(--dd-muted)] tabular-nums hidden sm:block">
          Practice here first
        </span>
      </div>

      <button
        type="button"
        onClick={onTap}
        className="w-full px-6 py-12 sm:py-16 text-center focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--dd-green)] focus-visible:ring-inset"
        aria-label={phase === "running" ? "Stop timer" : "Start timer"}
      >
        <p
          className={`font-mono text-[clamp(3.5rem,16vw,6.5rem)] leading-none tabular-nums tracking-tight transition-colors ${
            phase === "done" && won
              ? "text-[var(--dd-green)]"
              : phase === "running"
                ? "text-white"
                : "text-[#c8c8c8]"
          }`}
        >
          {display}
        </p>
        <p className="mt-4 text-sm text-[var(--dd-muted)]">
          {phase === "idle" && "Tap to start"}
          {phase === "running" && "Tap again to stop"}
          {phase === "done" && "Tap to run it back"}
        </p>
      </button>

      {phase === "done" && (
        <div
          className={`px-5 py-4 border-t text-sm ${
            won
              ? "border-[var(--dd-green)]/30 bg-[var(--dd-green)]/5 text-[var(--dd-text)]"
              : "border-[var(--dd-line)] text-[var(--dd-muted)]"
          }`}
        >
          {won ? (
            <>
              <p className="font-medium">That&apos;s 10.00.</p>
              <p className="mt-1">
                Come do it on camera at the shop. Tag{" "}
                <a
                  href="https://instagram.com/dollardankdispensary"
                  className="text-[var(--dd-green)] hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  @dollardankdispensary
                </a>
                .
              </p>
            </>
          ) : (
            <p>
              Off by {fmt(Math.abs(parseFloat(display) - TARGET))}s — run it again or pull up
              to 6590 SW Freeway and try for real.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
