"use client";

import { Star, Phone, Shield } from "lucide-react";
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
    <section className="relative min-h-[85vh] flex items-center pt-12 overflow-hidden bg-slate-950">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 55% 45% at 72% 38%, rgba(37,99,235,0.06) 0%, transparent 70%)",
        }}
        aria-hidden
      />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_3fr] gap-12 lg:gap-16 items-center">
          <div className="max-w-xl">
            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0, 0.4)}
              className="flex items-center gap-1 mb-6"
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
              transition={premiumTransition(0.08)}
              className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-[1.08] mb-4 font-display tracking-tight"
            >
              {hero.headline}
            </motion.h1>

            <motion.p
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.16)}
              className="text-lg sm:text-xl text-slate-300 max-w-lg leading-relaxed"
            >
              {hero.subheadline}
            </motion.p>

            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.24)}
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
                className="px-7 py-3 border border-slate-600 text-slate-200 font-medium rounded-md hover:border-slate-500 hover:text-white"
              >
                {hero.cta_secondary}
              </a>
            </motion.div>

            {hero.trust_bar.length > 0 && (
              <motion.div
                initial="hidden"
                animate="visible"
                variants={fadeUp}
                transition={premiumTransition(0.32)}
                className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-2"
              >
                {hero.trust_bar.map((item, i) => (
                  <div key={i} className="flex items-center gap-2 text-slate-500 text-xs uppercase tracking-wider font-medium">
                    <Shield className="h-3.5 w-3.5 text-blue-500/80" />
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
            transition={premiumTransition(0.2, 0.55)}
            className="hidden lg:block lg:pl-8"
          >
            <div className="border border-slate-800 bg-slate-900/80 rounded-lg p-8 max-w-sm ml-auto">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-400 mb-6">
                {business.business_name}
              </p>
              <p className="font-display text-5xl font-bold text-white tabular-nums leading-none">
                {business.google_rating}
              </p>
              <p className="text-slate-400 text-sm mt-2">{business.review_count} verified reviews</p>
              <div className="mt-8 pt-6 border-t border-slate-800">
                <p className="text-3xl font-display font-bold text-white tabular-nums">
                  {business.years_in_business}+
                </p>
                <p className="text-slate-500 text-sm mt-1">years serving {business.city}</p>
              </div>
            </div>
          </motion.aside>
        </div>
      </div>
    </section>
  );
}
