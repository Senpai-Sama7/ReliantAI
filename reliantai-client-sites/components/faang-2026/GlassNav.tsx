"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

const NAV_LINKS = [
  { label: "Principles", href: "#principles" },
  { label: "Trends", href: "#trends" },
  { label: "Motion", href: "#motion" },
  { label: "Metrics", href: "#metrics" },
] as const;

export default function GlassNav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      className="fixed top-0 left-0 right-0 z-50 px-4 sm:px-6 lg:px-10 pt-4"
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.15 }}
    >
      <nav
        className={`mx-auto max-w-7xl flex items-center justify-between px-5 py-3 transition-all duration-500 ${
          scrolled
            ? "faang-glass shadow-[0_1px_0_0_rgba(255,255,255,0.04)_inset]"
            : "bg-transparent border border-transparent"
        }`}
      >
        <a href="#" className="flex items-center gap-3 group">
          <div className="w-8 h-8 faang-border-strong flex items-center justify-center bg-[var(--faang-surface)]">
            <span
              className="text-[10px] font-bold tracking-[0.2em]"
              style={{ fontFamily: "var(--faang-font-mono)" }}
            >
              F26
            </span>
          </div>
          <div className="hidden sm:block">
            <span
              className="block text-sm font-semibold tracking-tight"
              style={{ fontFamily: "var(--faang-font-display)" }}
            >
              FAANG 2026
            </span>
            <span className="block text-[10px] text-[var(--faang-text-muted)] tracking-wide">
              Design System
            </span>
          </div>
        </a>

        <div className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="px-4 py-2 text-[12px] font-medium text-[var(--faang-text-muted)] hover:text-[var(--faang-text)] transition-colors relative group"
            >
              {link.label}
              <span className="absolute bottom-1 left-4 right-4 h-px bg-[var(--faang-accent)] scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
            </a>
          ))}
        </div>

        <a
          href="#metrics"
          className="px-4 py-2 text-[11px] font-semibold tracking-wide uppercase faang-border bg-[var(--faang-surface)] hover:bg-[var(--faang-surface-elevated)] transition-colors"
        >
          Explore
        </a>
      </nav>
    </motion.header>
  );
}
