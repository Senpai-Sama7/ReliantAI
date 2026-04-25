"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";

interface TradeCopy {
  services_title: string;
  services_subtitle: string;
  about_title: string;
  about_trust_title: string;
  reviews_title: string;
  faq_title: string;
  urgency_message: string;
  estimate_heading: string;
  estimate_subtext: string;
  trust_badges: string[];
  stats: { label: string; value_key: string; suffix: string; fallback: string }[];
}

interface FAQProps {
  content: SiteContent;
  copy: TradeCopy;
}

export default function FAQ({ content, copy }: FAQProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="relative py-24 bg-slate-950">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 right-0 w-72 h-72 rounded-full bg-blue-600/3 blur-3xl" />
      </div>
      <div className="relative max-w-3xl mx-auto px-4 sm:px-6">
        <h2 className="text-3xl sm:text-4xl font-bold text-white text-center mb-14 font-display">
          {copy.faq_title}
        </h2>

        <dl className="space-y-3">
          {content.faq.map((item, i) => {
            const isOpen = openIndex === i;
            return (
              <div
                key={i}
                className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden"
              >
                <dt>
                  <button
                    onClick={() => setOpenIndex(isOpen ? null : i)}
                    className="w-full flex items-center justify-between px-6 py-4 text-left text-white font-medium hover:text-blue-300 transition-colors"
                  >
                    <span className="pr-4">{item.question}</span>
                    <ChevronDown
                      className={`h-5 w-5 flex-shrink-0 text-slate-500 transition-transform duration-200 ${
                        isOpen ? "rotate-180" : ""
                      }`}
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
                      transition={{ duration: 0.25, ease: "easeInOut" }}
                      className="overflow-hidden"
                    >
                      <p className="px-6 pb-4 text-slate-400 text-sm leading-relaxed">
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
