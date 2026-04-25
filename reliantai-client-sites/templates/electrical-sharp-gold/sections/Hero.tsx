"use client";

import { Star, Phone, Shield } from "lucide-react";
import { motion } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";

interface HeroProps {
  content: SiteContent;
}

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export default function Hero({ content }: HeroProps) {
  const { business, hero } = content;
  const stars = Array.from({ length: Math.round(business.google_rating) });

  return (
    <section className="relative min-h-screen flex items-center overflow-hidden bg-slate-950">
      <div
        className="pointer-events-none absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[900px] rounded-full bg-amber-500/[0.07] blur-3xl"
        aria-hidden
      />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-slate-950 to-transparent" aria-hidden />

      <div className="relative z-10 mx-auto max-w-7xl px-4 py-28 sm:px-6">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
          <div>
            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={{ duration: 0.5 }}
              className="mb-6 flex items-center justify-center gap-1 lg:justify-start"
            >
              {stars.map((_, i) => (
                <Star key={i} className="h-5 w-5 fill-amber-400 text-amber-400" />
              ))}
              <span className="ml-2 text-sm text-slate-300">
                {business.google_rating} ({business.review_count} reviews)
              </span>
            </motion.div>

            <motion.h1
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-center text-4xl font-bold leading-tight text-white font-display sm:text-5xl lg:text-left lg:text-6xl"
            >
              {hero.headline}
            </motion.h1>

            <motion.p
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="mx-auto mt-4 max-w-3xl text-lg text-amber-200 sm:text-xl lg:mx-0 text-center lg:text-left"
            >
              {hero.subheadline}
            </motion.p>

            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row lg:justify-start"
            >
              <a
                href={`tel:${business.phone}`}
                className="inline-flex items-center gap-2 rounded-lg bg-amber-600 px-8 py-3 text-lg font-semibold text-white shadow-lg shadow-amber-600/25 transition-colors hover:bg-amber-500"
              >
                <Phone className="h-5 w-5" />
                {hero.cta_primary}
              </a>
              <a
                href="#services"
                className="rounded-lg border border-amber-400 px-8 py-3 text-lg font-medium text-amber-200 transition-colors hover:border-amber-300 hover:text-amber-100"
              >
                {hero.cta_secondary}
              </a>
            </motion.div>

            {hero.trust_bar.length > 0 && (
              <motion.div
                initial="hidden"
                animate="visible"
                variants={fadeUp}
                transition={{ duration: 0.5, delay: 0.4 }}
                className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 lg:justify-start"
              >
                {hero.trust_bar.map((item, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm text-slate-400">
                    <Shield className="h-4 w-4 text-amber-400" />
                    {item}
                  </div>
                ))}
              </motion.div>
            )}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.5 }}
            className="hidden items-center justify-center lg:flex"
          >
            <div className="relative flex h-64 w-64 flex-col items-center justify-center rounded-2xl border border-amber-500/20 bg-amber-500/[0.04] backdrop-blur-sm">
              <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-xl border border-amber-500/20 bg-amber-500/10">
                <Shield className="h-7 w-7 text-amber-400" />
              </div>
              <span className="font-display text-sm font-bold tracking-[0.3em] text-amber-300">
                SAFETY
              </span>
              <span className="font-display text-sm font-bold tracking-[0.3em] text-amber-300">
                FIRST
              </span>
              <span className="mt-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
                Licensed & Insured
              </span>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}