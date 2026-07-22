"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";

interface CraftFAQProps {
  content: SiteContent;
  copy: TradeCopy;
  light?: boolean;
}

export default function CraftFAQ({ content, copy, light = false }: CraftFAQProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const title = light ? "text-[var(--trade-ink)]" : "text-white";
  const body = light ? "text-stone-600" : "text-slate-400";
  const sectionBg = light ? "bg-[var(--trade-surface)]" : "bg-[var(--trade-ink)]";
  const card = light ? "bg-white border-stone-200" : "bg-[var(--trade-surface)] border-white/10";

  return (
    <section className={`relative craft-section ${sectionBg}`}>
      <div className="craft-container relative max-w-3xl mx-auto">
        <h2 className={`craft-display mb-8 sm:mb-12 ${title}`}>{copy.faq_title}</h2>

        <dl className="space-y-2.5 sm:space-y-3">
          {content.faq.map((item, i) => {
            const isOpen = openIndex === i;
            return (
              <div
                key={i}
                className={`border rounded-lg overflow-hidden ${card} ${
                  isOpen
                    ? "border-[color-mix(in_oklab,var(--trade-accent)_40%,transparent)]"
                    : ""
                }`}
              >
                <dt>
                  <button
                    type="button"
                    onClick={() => setOpenIndex(isOpen ? null : i)}
                    className={`w-full flex items-center justify-between gap-3 px-4 sm:px-6 py-4 text-left font-medium min-h-12 ${title} hover:text-[var(--trade-accent)]`}
                    aria-expanded={isOpen}
                  >
                    <span className="pr-2 text-sm sm:text-base text-balance">{item.question}</span>
                    <ChevronDown
                      className={`h-5 w-5 flex-shrink-0 text-slate-500 transition-transform duration-150 ${
                        isOpen ? "rotate-180" : ""
                      }`}
                      aria-hidden
                    />
                  </button>
                </dt>
                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.dd
                      key="content"
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
                      className="overflow-hidden"
                    >
                      <p className={`px-4 sm:px-6 pb-4 text-sm leading-relaxed ${body}`}>
                        {item.answer}
                      </p>
                    </motion.dd>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </dl>
      </div>
    </section>
  );
}
