"use client";

import { motion } from "framer-motion";

const HERO_WORDS = ["Engineered", "for", "the", "next", "decade."];

const stagger = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.08, delayChildren: 0.2 },
  },
};

const wordVariant = {
  hidden: { opacity: 0, y: "110%" },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.85, ease: [0.16, 1, 0.3, 1] as const },
  },
};

export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex flex-col justify-center px-4 sm:px-6 lg:px-10 pt-28 pb-20">
      <div className="mx-auto max-w-7xl w-full">
        {/* Archival label */}
        <motion.div
          initial={{ opacity: 0, x: -12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="flex items-center gap-4 mb-10"
        >
          <span className="archival-index">INDEX — 001</span>
          <div className="h-px flex-1 max-w-[120px] bg-[var(--faang-border)]" />
          <span className="archival-index text-[var(--faang-accent)]">2026 EDITION</span>
        </motion.div>

        {/* Kinetic headline */}
        <motion.h1
          className="text-[clamp(2.75rem,8.5vw,7.5rem)] leading-[0.92] tracking-[-0.03em] font-bold max-w-5xl"
          style={{ fontFamily: "var(--faang-font-display)" }}
          variants={stagger}
          initial="hidden"
          animate="visible"
        >
          {HERO_WORDS.map((word, i) => (
            <span key={i} className="inline-block overflow-hidden mr-[0.2em] last:mr-0">
              <motion.span
                variants={wordVariant}
                className={`inline-block ${
                  word === "decade." ? "text-[var(--faang-accent)]" : ""
                }`}
              >
                {word}
              </motion.span>
            </span>
          ))}
        </motion.h1>

        {/* Subhead */}
        <motion.p
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.9 }}
          className="mt-10 max-w-xl text-lg sm:text-xl text-[var(--faang-text-muted)] leading-relaxed font-light"
        >
          Where Apple&apos;s precision, Google&apos;s systems thinking, and 2026&apos;s tactile
          brutalism converge. Typography as architecture. Motion with purpose. Zero compromise.
        </motion.p>

        {/* CTA row */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.1 }}
          className="mt-12 flex flex-wrap items-center gap-4"
        >
          <a
            href="#principles"
            className="group inline-flex items-center gap-3 px-7 py-4 bg-[var(--faang-text)] text-[var(--faang-bg)] text-sm font-semibold tracking-wide hover:bg-white transition-colors"
          >
            View Principles
            <svg
              className="w-4 h-4 group-hover:translate-x-1 transition-transform"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </a>
          <a
            href="#trends"
            className="inline-flex items-center gap-2 px-7 py-4 faang-border text-sm font-medium text-[var(--faang-text-muted)] hover:text-[var(--faang-text)] hover:border-[var(--faang-border-strong)] transition-all"
          >
            2026 Trends Index
          </a>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.6, duration: 0.8 }}
          className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        >
          <span className="archival-index">SCROLL</span>
          <div className="w-px h-12 bg-gradient-to-b from-[var(--faang-border-strong)] to-transparent animate-pulse" />
        </motion.div>
      </div>
    </section>
  );
}
