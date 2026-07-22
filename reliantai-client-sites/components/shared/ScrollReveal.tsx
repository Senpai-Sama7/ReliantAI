/**
 * Shared scroll-reveal for T1 editorial templates.
 * CSS scroll-driven when supported; IntersectionObserver fallback.
 * Respects prefers-reduced-motion.
 */
"use client";

import { useEffect, useRef, type ReactNode, type CSSProperties, type ElementType } from "react";

interface ScrollRevealProps {
  children: ReactNode;
  className?: string;
  as?: ElementType;
  delayMs?: number;
  style?: CSSProperties;
}

export default function ScrollReveal({
  children,
  className = "",
  as: Tag = "div",
  delayMs = 0,
  style,
}: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      el.classList.add("is-visible");
      return;
    }

    const supportsTimeline =
      typeof CSS !== "undefined" && typeof CSS.supports === "function"
        ? CSS.supports("animation-timeline", "view()")
        : false;

    if (supportsTimeline) {
      el.classList.add("is-visible");
      return;
    }

    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add("is-visible");
          io.disconnect();
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <Tag
      ref={ref}
      className={`reveal ${className}`.trim()}
      style={{
        ...(delayMs ? { transitionDelay: `${delayMs}ms`, animationDelay: `${delayMs}ms` } : {}),
        ...style,
      }}
    >
      {children}
    </Tag>
  );
}
