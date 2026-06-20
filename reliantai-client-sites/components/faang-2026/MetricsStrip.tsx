"use client";

import Link from "next/link";
import { motion } from "framer-motion";

const METRICS = [
  { value: "< 1.2s", label: "LCP Target", sub: "Core Web Vitals" },
  { value: "0 JS", label: "Hero Animation", sub: "CSS scroll-driven" },
  { value: "100%", label: "Reduced Motion", sub: "prefers-reduced-motion" },
  { value: "AAA", label: "Contrast Ratio", sub: "WCAG 2.2" },
] as const;

export default function MetricsStrip() {
  return (
    <section id="metrics" className="relative px-4 sm:px-6 lg:px-10 py-28 border-t border-[var(--faang-border)]">
      <div className="mx-auto max-w-7xl">
        <div className="faang-glass p-8 sm:p-12 lg:p-16">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-10 mb-12">
            <div>
              <span className="archival-index block mb-3">INDEX — 005</span>
              <h2
                className="text-3xl sm:text-4xl font-bold tracking-tight"
                style={{ fontFamily: "var(--faang-font-display)" }}
              >
                Performance is design
              </h2>
            </div>
            <p className="max-w-md text-sm text-[var(--faang-text-muted)] leading-relaxed">
              In 2026, the fastest interface wins. Machine experience optimization,
              semantic structure, and CSS-first motion — shipped at FAANG scale.
            </p>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-[var(--faang-border)]">
            {METRICS.map((m, i) => (
              <motion.div
                key={m.label}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="bg-[var(--faang-surface-elevated)] p-6 sm:p-8 text-center"
              >
                <div
                  className="text-3xl sm:text-4xl font-bold tabular-nums text-[var(--faang-accent)]"
                  style={{ fontFamily: "var(--faang-font-display)" }}
                >
                  {m.value}
                </div>
                <div className="mt-2 text-sm font-medium">{m.label}</div>
                <div className="mt-1 archival-index">{m.sub}</div>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.4 }}
            className="mt-12 flex flex-col sm:flex-row items-center justify-between gap-6 pt-10 border-t border-[var(--faang-border)]"
          >
            <p
              className="text-xl sm:text-2xl font-bold tracking-tight"
              style={{ fontFamily: "var(--faang-font-display)" }}
            >
              Ready to ship at FAANG scale?
            </p>
            <Link
              href="/showcase"
              className="inline-flex items-center gap-2 px-8 py-4 bg-[var(--faang-accent)] text-white text-sm font-semibold hover:bg-[#0070e0] transition-colors whitespace-nowrap"
            >
              View Template Studio
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </Link>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
