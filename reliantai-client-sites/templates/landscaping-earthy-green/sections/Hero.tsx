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
            "radial-gradient(ellipse 50% 45% at 75% 40%, rgba(16,185,129,0.06) 0%, transparent 70%)",
        }}
        aria-hidden
      />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_3fr] gap-12 items-center">
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
              className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-[1.08] font-display tracking-tight"
            >
              {hero.headline}
            </motion.h1>

            <motion.p
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.16)}
              className="mt-5 text-lg sm:text-xl text-slate-300 max-w-lg leading-relaxed"
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
                className="inline-flex items-center gap-2.5 px-7 py-3 bg-emerald-700 text-white font-semibold rounded-md hover:bg-emerald-600"
              >
                <Phone className="h-4 w-4" />
                {hero.cta_primary}
              </a>
              <a
                href="#services"
                className="px-7 py-3 border border-slate-600 text-slate-200 font-medium rounded-md hover:border-emerald-500/40 hover:text-white"
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
                    <Shield className="h-3.5 w-3.5 text-emerald-500/80" />
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
            className="hidden lg:flex justify-end"
          >
            <div className="border border-slate-800 bg-slate-900 rounded-lg p-8 max-w-md w-full">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400 mb-4">
                Free estimate
              </p>
              <p className="font-display text-4xl text-white">Same-week start</p>
              <p className="text-slate-400 text-sm mt-3 leading-relaxed">
                Design, install, and maintenance for residential and commercial properties across {business.city}.
              </p>
              <p className="mt-6 pt-6 border-t border-slate-800 text-emerald-300/80 text-sm">
                {business.years_in_business}+ years · locally owned
              </p>
            </div>
          </motion.aside>
        </div>
      </div>
    </section>
  );
}
