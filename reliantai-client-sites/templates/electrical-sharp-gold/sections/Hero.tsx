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
    <section className="relative min-h-[85vh] flex items-center overflow-hidden bg-slate-950">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 45% 50% at 75% 35%, rgba(217,119,6,0.06) 0%, transparent 70%)",
        }}
        aria-hidden
      />

      <div className="relative z-10 mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:py-24">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-[2fr_3fr]">
          <div>
            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0, 0.4)}
              className="mb-6 flex items-center gap-1"
            >
              {stars.map((_, i) => (
                <Star key={i} className="h-4 w-4 fill-amber-400 text-amber-400" />
              ))}
              <span className="ml-2 text-sm text-slate-400">
                {business.google_rating} · {business.review_count} reviews
              </span>
            </motion.div>

            <motion.h1
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.08)}
              className="text-4xl font-bold leading-[1.08] text-white font-display sm:text-5xl lg:text-6xl tracking-tight"
            >
              {hero.headline}
            </motion.h1>

            <motion.p
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.16)}
              className="mt-4 max-w-lg text-lg text-slate-300 leading-relaxed sm:text-xl"
            >
              {hero.subheadline}
            </motion.p>

            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.24)}
              className="mt-8 flex flex-col items-start gap-3 sm:flex-row"
            >
              <a
                href={`tel:${business.phone}`}
                className="inline-flex items-center gap-2 rounded-md bg-amber-600 px-7 py-3 text-base font-semibold text-white hover:bg-amber-500"
              >
                <Phone className="h-4 w-4" />
                {hero.cta_primary}
              </a>
              <a
                href="#services"
                className="rounded-md border border-slate-600 px-7 py-3 text-base font-medium text-slate-200 hover:border-amber-500/50 hover:text-amber-100"
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
                  <div key={i} className="flex items-center gap-2 text-sm text-slate-500">
                    <Shield className="h-4 w-4 text-amber-500" />
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
            <div className="flex h-72 w-64 flex-col items-start justify-between rounded-lg border border-amber-900/40 bg-amber-950/30 p-8">
              <div className="flex h-12 w-12 items-center justify-center rounded-md border border-amber-800/50 bg-amber-900/40">
                <Shield className="h-6 w-6 text-amber-400" />
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.25em] text-amber-400">Safety first</p>
                <p className="mt-2 font-display text-2xl text-white">Licensed &amp; insured</p>
                <p className="mt-2 text-sm text-slate-400">NEC-compliant work on every job</p>
              </div>
            </div>
          </motion.aside>
        </div>
      </div>
    </section>
  );
}
