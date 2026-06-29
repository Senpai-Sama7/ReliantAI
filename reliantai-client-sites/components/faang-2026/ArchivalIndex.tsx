"use client";

import { motion } from "framer-motion";

const TRENDS_2026 = [
  {
    num: "01",
    name: "Tactile Brutalism",
    status: "ACTIVE",
    detail: "1px borders, 0px radius, engineered wireframe aesthetic replacing soft UI shadows.",
  },
  {
    num: "02",
    name: "Kinetic Typography",
    status: "ACTIVE",
    detail: "Scroll-driven text architecture. Headlines as heroes, not labels.",
  },
  {
    num: "03",
    name: "Glassmorphism 2.0",
    status: "SELECTIVE",
    detail: "Frosted layers on nav, modals, tooltips — never as a global theme.",
  },
  {
    num: "04",
    name: "Bento Grids",
    status: "ACTIVE",
    detail: "Asymmetric information density. Structured chaos at FAANG scale.",
  },
  {
    num: "05",
    name: "Archival Index",
    status: "EMERGING",
    detail: "Museum-catalog typography. Numbered systems, tabular precision.",
  },
  {
    num: "06",
    name: "Motion Narrative",
    status: "ACTIVE",
    detail: "Scroll-linked storytelling. Motion explains — it never distracts.",
  },
  {
    num: "07",
    name: "Machine Experience",
    status: "CRITICAL",
    detail: "Semantic HTML, lightweight CSS, structured data for AI agents.",
  },
  {
    num: "08",
    name: "Organic Layouts",
    status: "EMERGING",
    detail: "Anti-grid fluidity breaking rigid templates without losing hierarchy.",
  },
] as const;

export default function ArchivalIndex() {
  return (
    <section id="trends" className="relative px-4 sm:px-6 lg:px-10 py-28 border-t border-[var(--faang-border)]">
      <div className="mx-auto max-w-7xl">
        <div className="grid lg:grid-cols-[280px_1fr] gap-12 lg:gap-20">
          {/* Sticky sidebar */}
          <div className="lg:sticky lg:top-32 lg:self-start">
            <span className="archival-index block mb-3">INDEX — 003</span>
            <h2
              className="text-3xl sm:text-4xl font-bold tracking-tight mb-4"
              style={{ fontFamily: "var(--faang-font-display)" }}
            >
              2026 Trends
              <br />
              Catalog
            </h2>
            <p className="text-sm text-[var(--faang-text-muted)] leading-relaxed">
              Curated from production systems at scale. Each trend verified against
              performance, accessibility, and conversion metrics.
            </p>
            <div className="mt-8 p-4 faang-border bg-[var(--faang-surface)]">
              <span className="archival-index block mb-2">LAST UPDATED</span>
              <time
                dateTime="2026-06-12"
                className="text-sm font-medium tabular-nums"
                style={{ fontFamily: "var(--faang-font-mono)" }}
              >
                2026.06.12
              </time>
            </div>
          </div>

          {/* Index table */}
          <div className="faang-border divide-y divide-[var(--faang-border)]">
            {TRENDS_2026.map((trend, i) => (
              <motion.div
                key={trend.num}
                initial={{ opacity: 0, x: 16 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ duration: 0.4, delay: i * 0.05 }}
                className="group grid grid-cols-[auto_1fr_auto] sm:grid-cols-[60px_200px_1fr_auto] gap-4 sm:gap-6 p-5 sm:p-6 hover:bg-[var(--faang-surface)] transition-colors"
              >
                <span
                  className="archival-index text-[var(--faang-accent)] pt-0.5"
                >
                  {trend.num}
                </span>
                <h3
                  className="font-semibold text-[var(--faang-text)] group-hover:text-[var(--faang-accent)] transition-colors kinetic-word"
                  style={{ fontFamily: "var(--faang-font-display)" }}
                >
                  {trend.name}
                </h3>
                <p className="col-span-2 sm:col-span-1 text-sm text-[var(--faang-text-muted)] leading-relaxed">
                  {trend.detail}
                </p>
                <span
                  className={`archival-index justify-self-end px-2 py-1 faang-border ${
                    trend.status === "CRITICAL"
                      ? "text-[var(--faang-accent-warm)]"
                      : trend.status === "ACTIVE"
                        ? "text-[var(--faang-accent-green)]"
                        : "text-[var(--faang-text-muted)]"
                  }`}
                >
                  {trend.status}
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
