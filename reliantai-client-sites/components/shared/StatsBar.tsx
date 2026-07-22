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
  "violet-600": "text-[var(--trade-accent)]",
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
    const final = Number.isInteger(numericValue) ? numericValue.toString() : numericValue.toFixed(1);
    if (prefersReduced) {
      // Defer to next frame to avoid sync setState-in-effect lint noise
      const id = requestAnimationFrame(() => setDisplay(final));
      return () => cancelAnimationFrame(id);
    }

    const steps = 28;
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
    }, 28);
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
      { threshold: 0.25 },
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
      className={`relative border-b overflow-hidden ${
        light
          ? "border-stone-200 bg-[var(--trade-elevated)]"
          : "border-white/5 bg-[var(--trade-ink)]"
      }`}
    >
      <div className="craft-container py-10 sm:py-14 lg:py-16">
        {/* Mobile: 2×2 with breathing room. Desktop: 4-up. */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-x-4 gap-y-8 sm:gap-x-8 sm:gap-y-10 lg:gap-12">
          {tradeStats.map((stat, i) => (
            <div key={stat.label} className="min-w-0">
              <div
                className={`font-display tracking-tight truncate ${
                  ACCENT_CLASSES[accent] || ACCENT_CLASSES.steel
                } ${
                  stat.value_key === "_always"
                    ? "text-sm sm:text-base font-sans font-semibold uppercase tracking-[0.14em]"
                    : "text-3xl sm:text-4xl lg:text-5xl"
                }`}
              >
                {stat.value_key === "_always" ? (
                  <span>{stat.fallback}</span>
                ) : (
                  <AnimatedNumber value={values[i]} suffix={stat.suffix} inView={inView} />
                )}
              </div>
              <p
                className={`mt-2 text-[0.6875rem] sm:text-xs font-medium tracking-[0.14em] uppercase leading-snug ${
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
