"use client";

import { Star, Phone, Shield, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";
import { fadeUp, premiumTransition } from "@/lib/motion";

interface HeroProps {
  content: SiteContent;
}

export default function Hero({ content }: HeroProps) {
  const { business, hero } = content;
  const stars = Array.from({ length: Math.round(business.google_rating) });

  return (
    <section id="hero" className="relative min-h-[85vh] flex items-center pt-12 overflow-hidden bg-slate-950">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 50% 40% at 20% 60%, rgba(29,78,216,0.05) 0%, transparent 70%)",
        }}
        aria-hidden
      />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-24 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_3fr] gap-12 items-center">
          <div className="max-w-xl">
            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0, 0.4)}
              className="inline-flex items-center gap-2 px-3 py-1 bg-red-950/50 border border-red-900/40 rounded-full mb-6"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-red-400" aria-hidden />
              <AlertTriangle className="h-3.5 w-3.5 text-red-400" />
              <span className="text-red-300 text-xs font-semibold tracking-widest uppercase">
                24/7 Emergency Service
              </span>
            </motion.div>

            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.06)}
              className="flex items-center gap-1 mb-5"
            >
              {stars.map((_, i) => (
                <Star key={i} className="h-4 w-4 fill-amber-400 text-amber-400" />
              ))}
              <span className="ml-2 text-slate-400 text-sm">
                {business.google_rating} · {business.review_count} reviews
              </span>
            </motion.div>

            <motion.h1
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.1)}
              className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-[1.08] mb-4 font-display tracking-tight"
            >
              {hero.headline}
            </motion.h1>

            <motion.p
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.18)}
              className="text-lg sm:text-xl text-slate-300 leading-relaxed"
            >
              {hero.subheadline}
            </motion.p>

            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.26)}
              className="mt-8 flex flex-col sm:flex-row items-start gap-3"
            >
              <a
                href={`tel:${business.phone}`}
                className="inline-flex items-center gap-2.5 px-7 py-3 bg-blue-700 text-white font-semibold rounded-md hover:bg-blue-600"
              >
                <Phone className="h-4 w-4" />
                {hero.cta_primary}
              </a>
              <a
                href="#services"
                className="px-7 py-3 border border-slate-600 text-slate-200 font-medium rounded-md hover:border-slate-500"
              >
                {hero.cta_secondary}
              </a>
            </motion.div>

            {hero.trust_bar.length > 0 && (
              <motion.div
                initial="hidden"
                animate="visible"
                variants={fadeUp}
                transition={premiumTransition(0.34)}
                className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-2"
              >
                {hero.trust_bar.map((item, i) => (
                  <div key={i} className="flex items-center gap-2 text-slate-500 text-sm">
                    <Shield className="h-4 w-4 text-blue-500 flex-shrink-0" />
                    <span>{item}</span>
                  </div>
                ))}
              </motion.div>
            )}
          </div>

          <motion.aside
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            transition={premiumTransition(0.2, 0.5)}
            className="hidden lg:flex justify-end"
          >
            <div className="border border-slate-800 bg-slate-900 rounded-lg p-8 w-full max-w-md">
              <p className="text-xs uppercase tracking-[0.2em] text-blue-400 font-semibold mb-4">Response</p>
              <p className="font-display text-4xl font-bold text-white">Under 60 min</p>
              <p className="text-slate-400 text-sm mt-2">Average emergency arrival in {business.city}</p>
              <p className="mt-6 text-slate-300 text-sm leading-relaxed border-t border-slate-800 pt-6">
                Licensed master plumbers on call — nights, weekends, and holidays.
              </p>
            </div>
          </motion.aside>
        </div>
      </div>
    </section>
  );
}
