"use client";

import { Star, Phone, Shield, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";

const fadeInUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
};

const fadeInLeft = {
  hidden: { opacity: 0, x: -40 },
  visible: { opacity: 1, x: 0 },
};

export default function Hero({ content }: { content: SiteContent }) {
  const { business, hero } = content;
  const stars = Array.from({ length: Math.round(business.google_rating) });

  return (
    <section className="relative min-h-[90vh] flex items-center overflow-hidden bg-gradient-to-b from-slate-950 via-orange-950/30 to-slate-950">
      {/* Single subtle background glow */}
      <div
        className="pointer-events-none absolute top-1/4 right-1/4 -translate-y-1/2 translate-x-1/2 w-[800px] h-[800px] rounded-full opacity-20 blur-[180px]"
        style={{ background: "radial-gradient(circle, rgba(249,115,22,0.4) 0%, transparent 70%)" }}
      />

      {/* Bottom gradient fade into content */}
      <div className="absolute bottom-0 inset-x-0 h-40 bg-gradient-to-t from-slate-950 to-transparent pointer-events-none z-10" />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 py-28 lg:py-36">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-20 items-center">
          {/* Left: Bold commanding layout */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeInLeft}
            transition={{ duration: 0.7, ease: "easeOut" }}
          >
            {/* FREE INSPECTIONS badge */}
            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeInUp}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-orange-500/15 border border-orange-500/30 rounded-full text-orange-400 text-xs font-semibold tracking-wider uppercase mb-6"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500" />
              </span>
              Free Inspections — Same Day
            </motion.div>

            {/* Stars */}
            <div className="flex items-center gap-1.5 mb-5">
              {stars.map((_, i) => (
                <Star key={i} className="h-4.5 w-4.5 fill-yellow-400 text-yellow-400" />
              ))}
              <span className="ml-2 text-slate-400 text-sm font-medium">
                {business.google_rating} ({business.review_count} reviews)
              </span>
            </div>

            {/* Headline */}
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-bold text-white leading-[1.05] tracking-tight">
              {hero.headline}
            </h1>
            <p className="mt-6 text-lg sm:text-xl text-slate-300 leading-relaxed max-w-xl">
              {hero.subheadline}
            </p>

            {/* CTAs */}
            <div className="mt-8 flex flex-col sm:flex-row gap-4">
              <a
                href={`tel:${business.phone}`}
                className="inline-flex items-center justify-center gap-2.5 px-8 py-4 bg-orange-600 text-white font-semibold text-lg rounded-xl hover:bg-orange-500 transition-all duration-300 shadow-lg shadow-orange-600/30 hover:shadow-orange-500/40 hover:-translate-y-0.5"
              >
                <Phone className="h-5 w-5" />
                {hero.cta_primary}
              </a>
              <a
                href="#services"
                className="inline-flex items-center justify-center gap-2 px-8 py-4 border-2 border-slate-700 text-slate-200 font-semibold text-lg rounded-xl hover:border-orange-500/60 hover:text-orange-200 transition-all duration-300"
              >
                {hero.cta_secondary}
                <ArrowRight className="h-4 w-4" />
              </a>
            </div>

            {/* Trust bar */}
            {hero.trust_bar.length > 0 && (
              <div className="mt-12 flex flex-wrap items-center gap-x-6 gap-y-3">
                {hero.trust_bar.map((item, i) => (
                  <div key={i} className="flex items-center gap-2 text-slate-500 text-sm font-medium">
                    <Shield className="h-4 w-4 text-orange-500/60" />
                    {item}
                  </div>
                ))}
              </div>
            )}
          </motion.div>

          {/* Right: Rating + credential stack */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeInUp}
            transition={{ duration: 0.7, delay: 0.25, ease: "easeOut" }}
            className="hidden lg:flex items-center justify-center"
          >
            <div className="relative flex flex-col gap-5 w-full max-w-sm">
              {/* Rating card */}
              <div className="bg-slate-900/80 backdrop-blur-sm border border-slate-700/60 rounded-2xl p-6 shadow-2xl">
                <div className="flex items-center gap-4 mb-3">
                  <span className="font-display text-5xl font-bold text-white tabular-nums">
                    {business.google_rating}
                  </span>
                  <div>
                    <div className="flex gap-0.5">
                      {stars.map((_, i) => (
                        <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                      ))}
                    </div>
                    <p className="text-slate-500 text-xs mt-1">
                      {business.review_count} reviews on Google
                    </p>
                  </div>
                </div>
                <p className="text-slate-400 text-sm">
                  Top-rated roofing in {business.city}, {business.state}
                </p>
              </div>

              {/* Years card */}
              <div className="bg-slate-900/80 backdrop-blur-sm border border-slate-700/60 rounded-2xl p-5 shadow-2xl flex items-center gap-4">
                <span className="font-display text-4xl font-bold text-orange-400 tabular-nums">
                  {business.years_in_business || 10}+
                </span>
                <div>
                  <p className="text-white font-semibold text-sm">Years Serving</p>
                  <p className="text-slate-500 text-xs">{business.city} & Surrounding Areas</p>
                </div>
              </div>

              {/* FREE INSPECTION badge — bold */}
              <div className="bg-orange-600 text-white text-center text-base font-bold px-8 py-4 rounded-2xl shadow-xl shadow-orange-600/30 border border-orange-500">
                FREE INSPECTION TODAY
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}