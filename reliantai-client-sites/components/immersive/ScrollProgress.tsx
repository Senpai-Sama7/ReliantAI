"use client";

import { useEffect, useState } from "react";

/** Thin top progress rail — signals cinematic scroll story. */
export default function ScrollProgress() {
  const [p, setP] = useState(0);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const onScroll = () => {
      const doc = document.documentElement;
      const max = doc.scrollHeight - window.innerHeight;
      setP(max > 0 ? Math.min(1, window.scrollY / max) : 0);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div
      className="pointer-events-none fixed inset-x-0 top-0 z-[70] h-[2px] bg-transparent"
      aria-hidden
    >
      <div
        className="h-full origin-left bg-[var(--trade-accent)] transition-[width] duration-100"
        style={{ width: `${p * 100}%` }}
      />
    </div>
  );
}
