"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";

const CHAPTERS = [
  {
    phase: "ATTENTION",
    title: "Win the first 3 seconds",
    body: "Kinetic typography creates a visual handshake. Users know they're somewhere engineered, not templated.",
  },
  {
    phase: "COMPREHENSION",
    title: "Motion that explains",
    body: "Scroll-linked reveals guide the eye through hierarchy. Every animation has a job — direct attention, confirm action, reduce hesitation.",
  },
  {
    phase: "TRUST",
    title: "Accessibility as infrastructure",
    body: "prefers-reduced-motion, WCAG AAA contrast, semantic structure. FAANG teams ship inclusive by default, not as an afterthought.",
  },
] as const;

export default function MotionNarrative() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });

  const lineHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  return (
    <section id="motion" ref={containerRef} className="relative px-4 sm:px-6 lg:px-10 py-28">
      <div className="mx-auto max-w-7xl">
        <span className="archival-index block mb-3 text-center">INDEX — 004</span>
        <h2
          className="text-3xl sm:text-5xl font-bold tracking-tight text-center mb-20"
          style={{ fontFamily: "var(--faang-font-display)" }}
        >
          Motion Narrative
        </h2>

        <div className="relative max-w-3xl mx-auto">
          {/* Progress line */}
          <div className="absolute left-4 sm:left-6 top-0 bottom-0 w-px bg-[var(--faang-border)]">
            <motion.div
              className="w-full bg-[var(--faang-accent)] origin-top"
              style={{ height: lineHeight }}
            />
          </div>

          <div className="space-y-24 sm:space-y-32">
            {CHAPTERS.map((chapter, i) => (
              <motion.div
                key={chapter.phase}
                initial={{ opacity: 0, x: 32 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.6, delay: i * 0.1 }}
                className="relative pl-14 sm:pl-20"
              >
                <div className="absolute left-2.5 sm:left-4 top-1 w-3 h-3 faang-border-strong bg-[var(--faang-bg)] ring-4 ring-[var(--faang-bg)]" />
                <span className="archival-index text-[var(--faang-accent-warm)] block mb-3">
                  {chapter.phase}
                </span>
                <h3
                  className="text-2xl sm:text-3xl font-bold tracking-tight mb-4"
                  style={{ fontFamily: "var(--faang-font-display)" }}
                >
                  {chapter.title}
                </h3>
                <p className="text-[var(--faang-text-muted)] leading-relaxed max-w-lg">
                  {chapter.body}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
