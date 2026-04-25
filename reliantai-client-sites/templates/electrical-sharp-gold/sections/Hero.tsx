"use client";

import { Star, Phone, Shield } from "lucide-react";
import { motion } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";

interface HeroProps {
  content: SiteContent;
}

const sideSlide = {
  hidden: { opacity: 0, x: 80 },
  visible: { opacity: 1, x: 0 },
};

export default function Hero({ content }: HeroProps) {
  const { business, hero } = content;
  const stars = Array.from({ length: Math.round(business.google_rating) });

  return (
    <section className="relative min-h-screen flex items-center justify-center pt-12 overflow-hidden bg-gradient-to-b from-slate-950 via-amber-950/40 to-slate-950">

      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] pointer-events-none rounded-full bg-amber-500/8 blur-3xl" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-20">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">

          <div>
            <motion.div
              initial="hidden"
              animate="visible"
              variants={sideSlide}
              transition={{ duration: 0.5 }}
              className="flex items-center justify-center lg:justify-start gap-1 mb-6"
            >
              {stars.map((_, i) => (
                <Star key={i} className="h-5 w-5 fill-amber-400 text-amber-400" />
              ))}
              <span className="ml-2 text-slate-300 text-sm">
                {business.google_rating} ({business.review_count} reviews)
              </span>
            </motion.div>

            <motion.h1
              initial="hidden"
              animate="visible"
              variants={sideSlide}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight text-center lg:text-left font-display"
            >
              {hero.headline}
            </motion.h1>

            <motion.p
              initial="hidden"
              animate="visible"
              variants={sideSlide}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="mt-4 text-lg sm:text-xl text-amber-200 max-w-3xl mx-auto lg:mx-0 text-center lg:text-left"
            >
              {hero.subheadline}
            </motion.p>

            <motion.div
              initial="hidden"
              animate="visible"
              variants={sideSlide}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="mt-8 flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4"
            >
              <a
                href={`tel:${business.phone}`}
                className="inline-flex items-center gap-2 px-8 py-3 bg-amber-600 text-white font-semibold text-lg rounded-lg hover:bg-amber-500 transition-colors shadow-lg shadow-amber-600/25"
              >
                <Phone className="h-5 w-5" />
                {hero.cta_primary}
              </a>
              <a
                href="#services"
                className="px-8 py-3 border border-amber-400 text-amber-200 font-medium text-lg rounded-lg hover:border-amber-300 hover:text-amber-100 transition-colors"
              >
                {hero.cta_secondary}
              </a>
            </motion.div>

            {hero.trust_bar.length > 0 && (
              <motion.div
                initial="hidden"
                animate="visible"
                variants={sideSlide}
                transition={{ duration: 0.5, delay: 0.4 }}
                className="mt-12 flex flex-wrap items-center justify-center lg:justify-start gap-x-8 gap-y-3"
              >
                {hero.trust_bar.map((item, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 text-slate-400 text-sm"
                  >
                    <Shield className="h-4 w-4 text-amber-400" />
                    {item}
                  </div>
                ))}
              </motion.div>
            )}
          </div>

          <motion.div
            initial={{ opacity: 0, x: 80 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.5 }}
            className="hidden lg:flex items-center justify-center"
          >
            <div className="relative w-72 h-72">
              <div className="absolute inset-0 rounded-full border-2 border-amber-500/20" />
              <div className="absolute inset-4 rounded-full border border-amber-500/10" />
              <div className="absolute inset-10 rounded-full border border-amber-500/10 bg-amber-500/5" />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber-500/10 border border-amber-500/20 mb-3">
                    <Shield className="h-8 w-8 text-amber-400" />
                  </div>
                  <p className="text-amber-300 font-display font-bold text-base tracking-[0.25em]">SAFETY</p>
                  <p className="text-amber-300 font-display font-bold text-base tracking-[0.25em]">FIRST</p>
                  <p className="mt-3 text-slate-500 text-xs tracking-widest uppercase">
                    Licensed &amp; Insured
                  </p>
                </div>
              </div>
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
