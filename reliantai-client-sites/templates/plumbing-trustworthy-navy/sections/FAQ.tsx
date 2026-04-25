"use client";

import { useState } from "react";
import { ChevronDown, HelpCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { TRADE_COPY } from "@/lib/trade-copy";
import type { SiteContent } from "@/types/SiteContent";

interface FAQProps {
  content: SiteContent;
}

export default function FAQ({ content }: FAQProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const copy = TRADE_COPY[content.site_config.trade as keyof typeof TRADE_COPY] ?? TRADE_COPY.plumbing;

  return (
    <section id="faq" className="py-24 bg-slate-950">
      <div className="max-w-3xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <HelpCircle className="h-8 w-8 text-blue-400 mx-auto mb-4" />
          <h2 className="text-3xl sm:text-4xl font-bold text-white font-display">
            {copy.faq_title}
          </h2>
        </div>

        <dl className="space-y-3">
          {content.faq.map((item, i) => {
            const isOpen = openIndex === i;
            const chevronClasses = isOpen
              ? "h-5 w-5 flex-shrink-0 text-blue-400 transition-transform duration-200 rotate-180"
              : "h-5 w-5 flex-shrink-0 text-slate-500 transition-transform duration-200";

            return (
              <div
                key={i}
                className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700/80 transition-colors"
              >
                <dt>
                  <button
                    onClick={() => setOpenIndex(isOpen ? null : i)}
                    className="w-full flex items-center justify-between px-6 py-5 text-left text-white font-medium hover:text-blue-200 transition-colors"
                  >
                    <span className="pr-4">{item.question}</span>
                    <ChevronDown className={chevronClasses} />
                  </button>
                </dt>
                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.dd
                      key="content"
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2, ease: "easeInOut" }}
                      className="overflow-hidden"
                    >
                      <div className="px-6 pb-5 text-slate-400 text-sm leading-relaxed">
                        {item.answer}
                      </div>
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
