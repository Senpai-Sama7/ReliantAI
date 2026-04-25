"use client";

import { useEffect, useRef, useState } from "react";
import type { SiteContent } from "@/types/SiteContent";

interface StatDef {
  label: string;
  suffix: string;
}

const TRADE_STATS: Record<string, StatDef[]> = {
  hvac: [
    { label: "Years in Business", suffix: "+" },
    { label: "Homes Serviced", suffix: "+" },
    { label: "Google Rating", suffix: "★" },
    { label: "Same-Day Service", suffix: "" },
  ],
  plumbing: [
    { label: "Years in Business", suffix: "+" },
    { label: "Jobs Completed", suffix: "+" },
    { label: "Google Rating", suffix: "★" },
    { label: "24/7 Emergency", suffix: "" },
  ],
  electrical: [
    { label: "Years in Business", suffix: "+" },
    { label: "Homes Powered", suffix: "+" },
    { label: "Google Rating", suffix: "★" },
    { label: "Same-Day Available", suffix: "" },
  ],
  roofing: [
    { label: "Years in Business", suffix: "+" },
    { label: "Roofs Protected", suffix: "+" },
    { label: "Google Rating", suffix: "★" },
    { label: "Free Inspections", suffix: "" },
  ],
  painting: [
    { label: "Years in Business", suffix: "+" },
    { label: "Homes Transformed", suffix: "+" },
    { label: "Google Rating", suffix: "★" },
    { label: "Free Consultation", suffix: "" },
  ],
  landscaping: [
    { label: "Years in Business", suffix: "+" },
    { label: "Yards Maintained", suffix: "+" },
    { label: "Google Rating", suffix: "★" },
    { label: "Free Estimates", suffix: "" },
  ],
};

type AccentColor = "blue-400" | "amber-400" | "orange-400" | "violet-600" | "emerald-400";

const ACCENT_CLASSES: Record<AccentColor, string> = {
  "blue-400": "text-blue-400",
  "amber-400": "text-amber-400",
  "orange-400": "text-orange-400",
  "violet-600": "text-violet-600",
  "emerald-400": "text-emerald-400",
};

interface StatsBarProps {
  content: SiteContent;
  accent?: AccentColor;
  light?: boolean;
}

function AnimatedNumber({ value, suffix, inView }: { value: string; suffix: string; inView: boolean }) {
  const [display, setDisplay] = useState("0");

  useEffect(() => {
    if (!inView) return;
    const numeric = parseFloat(value.replace(/[^0-9.]/g, ""));
    if (isNaN(numeric)) {
      setDisplay(value);
      return;
    }
    const steps = 30;
    const increment = numeric / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= numeric) {
        setDisplay(Number.isInteger(numeric) ? numeric.toString() : numeric.toFixed(1));
        clearInterval(timer);
      } else {
        setDisplay(Number.isInteger(numeric) ? Math.floor(current).toString() : current.toFixed(1));
      }
    }, 30);
    return () => clearInterval(timer);
  }, [inView, value]);

  const isText = isNaN(parseFloat(value.replace(/[^0-9.]/g, "")));
  return (
    <span className="tabular-nums">
      {isText ? value : display}
      {suffix && <span className="ml-0.5">{suffix}</span>}
    </span>
  );
}

export default function StatsBar({ content, accent = "blue-400", light = false }: StatsBarProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setInView(true); },
      { threshold: 0.3 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  const { business } = content;
  const trade = content.site_config?.trade || "hvac";
  const tradeStats = TRADE_STATS[trade] || TRADE_STATS.hvac;

  const values = [
    business.years_in_business?.toString() || "10",
    business.review_count > 1000 ? "5000" : business.review_count > 100 ? "1000" : "500",
    business.google_rating?.toString() || "4.9",
    "",
  ];

  return (
    <div
      ref={ref}
      className={`relative py-20 overflow-hidden ${
        light
          ? "border-b border-stone-200 bg-white"
          : "border-b border-slate-800/50 bg-transparent"
      }`}
    >
      {!light && (
        <div className="absolute inset-0 pointer-events-none opacity-25"
          style={{
            background: "radial-gradient(ellipse 120% 120% at 50% 50%, var(--stat-glow, rgba(96,165,250,0.10)) 0%, transparent 70%)",
          }}
        />
      )}
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-12">
          {tradeStats.map((stat, i) => (
            <div key={i} className="text-center">
              <div className={`text-4xl sm:text-5xl font-bold tracking-tight ${ACCENT_CLASSES[accent] || ACCENT_CLASSES["blue-400"]}`}>
                {values[i] ? (
                  <AnimatedNumber value={values[i]} suffix={stat.suffix} inView={inView} />
                ) : (
                  <span className="text-lg">{stat.label}</span>
                )}
              </div>
              {values[i] && (
                <p className={`mt-3 text-sm font-medium tracking-wide uppercase ${
                  light ? "text-stone-500" : "text-slate-500"
                }`}>
                  {stat.label}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}