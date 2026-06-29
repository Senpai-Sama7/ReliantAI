"use client";

import { motion } from "framer-motion";

const PRINCIPLES = [
  {
    id: "AAPL",
    company: "Apple",
    title: "Precision at scale",
    description:
      "Generous negative space, viewport-scaled typography, and motion that feels physical — not decorative.",
    metric: "98",
    metricLabel: "Lighthouse",
    span: "col-span-1 row-span-2",
    accent: "#f5f5f7",
  },
  {
    id: "GOOG",
    company: "Google",
    title: "Bento information density",
    description:
      "Structured grids that scale from mobile to enterprise. Every cell earns its place.",
    metric: "16",
    metricLabel: "Token layers",
    span: "col-span-1 row-span-1",
    accent: "#4285f4",
  },
  {
    id: "META",
    company: "Meta",
    title: "Product narrative",
    description:
      "Scroll-driven storytelling that converts curiosity into comprehension.",
    metric: "3.2s",
    metricLabel: "Time to value",
    span: "col-span-1 row-span-1",
    accent: "#0668e1",
  },
  {
    id: "NFLX",
    company: "Netflix",
    title: "Cinematic dark mode",
    description:
      "Depth without clutter. Content-forward hierarchy with theatrical restraint.",
    metric: "4K",
    metricLabel: "Visual fidelity",
    span: "col-span-1 row-span-1",
    accent: "#e50914",
  },
  {
    id: "AMZN",
    company: "Amazon",
    title: "Conversion clarity",
    description:
      "Every interaction removes friction. Accessibility is not optional — it's revenue.",
    metric: "AAA",
    metricLabel: "WCAG target",
    span: "col-span-1 row-span-1",
    accent: "#ff9900",
  },
] as const;

const container = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.07 },
  },
};

const card = {
  hidden: { opacity: 0, y: 28 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] as const },
  },
};

export default function BentoGrid() {
  return (
    <section id="principles" className="relative px-4 sm:px-6 lg:px-10 py-28">
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6 mb-14">
          <div>
            <span className="archival-index block mb-3">INDEX — 002</span>
            <h2
              className="text-3xl sm:text-5xl font-bold tracking-tight"
              style={{ fontFamily: "var(--faang-font-display)" }}
            >
              FAANG Principles
            </h2>
          </div>
          <p className="max-w-sm text-[var(--faang-text-muted)] text-sm leading-relaxed">
            Five companies. One bar. Each principle distilled into a shippable design pattern for 2026.
          </p>
        </div>

        <motion.div
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-px bg-[var(--faang-border)]"
          variants={container}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-80px" }}
        >
          {PRINCIPLES.map((p) => (
            <motion.article
              key={p.id}
              variants={card}
              className={`group relative bg-[var(--faang-surface)] p-6 sm:p-8 flex flex-col justify-between min-h-[220px] hover:bg-[var(--faang-surface-elevated)] transition-colors ${
                p.span.includes("row-span-2") ? "lg:row-span-2 lg:min-h-[460px]" : ""
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-6">
                  <span
                    className="archival-index"
                    style={{ color: p.accent }}
                  >
                    {p.id}
                  </span>
                  <span className="text-[11px] font-medium text-[var(--faang-text-muted)]">
                    {p.company}
                  </span>
                </div>
                <h3
                  className="text-xl sm:text-2xl font-bold tracking-tight mb-3 group-hover:text-[var(--faang-accent)] transition-colors"
                  style={{ fontFamily: "var(--faang-font-display)" }}
                >
                  {p.title}
                </h3>
                <p className="text-sm text-[var(--faang-text-muted)] leading-relaxed">
                  {p.description}
                </p>
              </div>

              <div className="mt-8 pt-6 border-t border-[var(--faang-border)] flex items-end justify-between">
                <div>
                  <span
                    className="text-3xl font-bold tabular-nums"
                    style={{ fontFamily: "var(--faang-font-display)" }}
                  >
                    {p.metric}
                  </span>
                  <span className="block text-[10px] uppercase tracking-widest text-[var(--faang-text-muted)] mt-1">
                    {p.metricLabel}
                  </span>
                </div>
                <div
                  className="w-2 h-2"
                  style={{ backgroundColor: p.accent }}
                />
              </div>
            </motion.article>
          ))}

          {/* Summary cell */}
          <motion.div
            variants={card}
            className="bg-[var(--faang-bg)] p-6 sm:p-8 flex flex-col justify-center items-center text-center min-h-[220px] faang-border border-dashed"
          >
            <span className="archival-index mb-4">SYNTHESIS</span>
            <p
              className="text-lg font-semibold max-w-[200px]"
              style={{ fontFamily: "var(--faang-font-display)" }}
            >
              Ship once. Scale everywhere.
            </p>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
