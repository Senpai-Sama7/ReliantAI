"use client";

import { useEffect, useRef, useState } from "react";
import type { SiteContent } from "@/types/SiteContent";
import { TRADE_COPY } from "@/lib/trade-copy";

type AccentColor =
  | "steel"
  | "copper"
  | "gold"
  | "ochre"
  | "moss"
  | "blue-400"
  | "amber-400"
  | "orange-400"
  | "amber-700"
  | "violet-600"
  | "emerald-400";

/** Prefer token-driven accents; legacy Tailwind names map to trade CSS vars */
const ACCENT_CLASSES: Record<AccentColor, string> = {
  steel: "text-[var(--trade-accent)]",
  copper: "text-[var(--trade-accent)]",
  gold: "text-[var(--trade-accent)]",
  ochre: "text-[var(--trade-accent)]",
  moss: "text-[var(--trade-accent)]",
  "blue-400": "text-[var(--trade-accent)]",
  "amber-400": "text-[var(--trade-accent)]",
  "orange-400": "text-[var(--trade-accent)]",
  "amber-700": "text-[var(--trade-primary)]",
  "violet-600": "text-[var(--trade-accent)]", // never ship violet identity
  "emerald-400": "text-[var(--trade-accent)]",
};

interface StatsBarProps {
  content: SiteContent;
  accent?: AccentColor;
  light?: boolean;
}

function parseNumericValue(value: string): number | null {
  const numeric = parseFloat(value.replace(/[^0-9.]/g, ""));
  return Number.isNaN(numeric) ? null : numeric;
}

function AnimatedNumber({ value, suffix, inView }: { value: string; suffix: string; inView: boolean }) {
  const numericValue = parseNumericValue(value);
  const isText = numericValue === null;
  const [display, setDisplay] = useState(isText ? value : "0");

  useEffect(() => {
    if (!inView || isText || numericValue === null) return;

    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReduced) {
      const frame = window.requestAnimationFrame(() => {
        setDisplay(
          Number.isInteger(numericValue) ? numericValue.toString() : numericValue.toFixed(1),
        );
      });
      return () => window.cancelAnimationFrame(frame);
    }

    const steps = 30;
    const increment = numericValue / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= numericValue) {
        setDisplay(Number.isInteger(numericValue) ? numericValue.toString() : numericValue.toFixed(1));
        clearInterval(timer);
      } else {
        setDisplay(Number.isInteger(numericValue) ? Math.floor(current).toString() : current.toFixed(1));
      }
    }, 30);
    return () => clearInterval(timer);
  }, [inView, isText, numericValue, value]);

  return (
    <span className="tabular-nums">
      {isText ? value : display}
      {suffix && <span className="ml-0.5">{suffix}</span>}
    </span>
  );
}

function resolveStatValue(
  valueKey: string,
  fallback: string,
  business: SiteContent["business"],
): string {
  if (valueKey === "_always") return fallback;
  if (valueKey === "years_in_business") {
    return business.years_in_business?.toString() || fallback;
  }
  if (valueKey === "google_rating") {
    return business.google_rating?.toString() || fallback;
  }
  if (valueKey === "review_count") {
    return business.review_count > 0 ? business.review_count.toString() : fallback;
  }
  return fallback;
}

export default function StatsBar({ content, accent = "steel", light = false }: StatsBarProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setInView(true);
      },
      { threshold: 0.3 },
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  const { business } = content;
  const trade = content.site_config?.trade || "hvac";
  const tradeStats = TRADE_COPY[trade]?.stats || TRADE_COPY.hvac.stats;

  const values = tradeStats.map((stat) =>
    resolveStatValue(stat.value_key, stat.fallback, business),
  );

  return (
    <div
      ref={ref}
      className={`relative py-20 overflow-hidden ${
        light
          ? "border-b border-stone-200 bg-[var(--trade-elevated)]"
          : "border-b border-white/5 bg-[var(--trade-ink)]"
      }`}
    >
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-12">
          {tradeStats.map((stat, i) => (
            <div key={stat.label} className="text-left md:text-center">
              <div
                className={`text-4xl sm:text-5xl font-display tracking-tight ${ACCENT_CLASSES[accent] || ACCENT_CLASSES.steel}`}
              >
                {stat.value_key === "_always" ? (
                  <span className="text-lg font-sans font-semibold uppercase tracking-wider">
                    {stat.fallback}
                  </span>
                ) : (
                  <AnimatedNumber value={values[i]} suffix={stat.suffix} inView={inView} />
                )}
              </div>
              <p
                className={`mt-3 text-xs font-medium tracking-[0.18em] uppercase ${
                  light ? "text-stone-500" : "text-slate-500"
                }`}
              >
                {stat.label}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
