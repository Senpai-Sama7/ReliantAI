"use client";

import { Star, Phone, Shield, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";
import { fadeUp, premiumTransition } from "@/lib/motion";

export default function Hero({ content }: { content: SiteContent }) {
  const { business, hero } = content;
  const stars = Array.from({ length: Math.round(business.google_rating) });

  return (
    <section className="relative min-h-[85vh] flex items-center overflow-hidden bg-slate-950">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 50% 45% at 78% 30%, rgba(234,88,12,0.06) 0%, transparent 70%)",
        }}
        aria-hidden
      />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_3fr] gap-12 items-center">
          <div className="max-w-xl">
            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0, 0.4)}
              className="inline-flex items-center gap-2 px-3 py-1 bg-orange-950/40 border border-orange-900/30 rounded-full text-orange-300 text-xs font-semibold tracking-wider uppercase mb-6"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-orange-400" aria-hidden />
              Free inspections — same day
            </motion.div>

            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.06)}
              className="flex items-center gap-1.5 mb-5"
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
              className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-[1.08] tracking-tight"
            >
              {hero.headline}
            </motion.h1>

            <motion.p
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.18)}
              className="mt-5 text-lg sm:text-xl text-slate-300 leading-relaxed"
            >
              {hero.subheadline}
            </motion.p>

            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.26)}
              className="mt-8 flex flex-col sm:flex-row gap-3"
            >
              <a
                href={`tel:${business.phone}`}
                className="inline-flex items-center justify-center gap-2 px-7 py-3 bg-orange-600 text-white font-semibold rounded-md hover:bg-orange-500"
              >
                <Phone className="h-4 w-4" />
                {hero.cta_primary}
              </a>
              <a
                href="#services"
                className="inline-flex items-center justify-center gap-2 px-7 py-3 border border-slate-600 text-slate-200 font-medium rounded-md hover:border-orange-500/50 hover:text-orange-100"
              >
                {hero.cta_secondary}
                <ArrowRight className="h-4 w-4" />
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
                    <Shield className="h-4 w-4 text-orange-500/70" />
                    {item}
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
            className="hidden lg:flex flex-col gap-4 max-w-sm ml-auto w-full"
          >
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
              <div className="flex items-center gap-4">
                <span className="font-display text-5xl font-bold text-white tabular-nums">
                  {business.google_rating}
                </span>
                <div>
                  <div className="flex gap-0.5">
                    {stars.map((_, i) => (
                      <Star key={i} className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                    ))}
                  </div>
                  <p className="text-slate-500 text-xs mt-1">{business.review_count} Google reviews</p>
                </div>
              </div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 flex items-center gap-4">
              <span className="font-display text-4xl font-bold text-orange-400 tabular-nums">
                {business.years_in_business || 10}+
              </span>
              <p className="text-slate-400 text-sm">Years serving {business.city}</p>
            </div>
            <div className="bg-orange-600 text-white text-center text-sm font-semibold px-6 py-3.5 rounded-md">
              Free inspection today
            </div>
          </motion.aside>
        </div>
      </div>
    </section>
  );
}
