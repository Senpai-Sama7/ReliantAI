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

const fadeInRight = {
  hidden: { opacity: 0, x: 40 },
  visible: { opacity: 1, x: 0 },
};

export default function Hero({ content }: { content: SiteContent }) {
  const { business, hero } = content;
  const stars = Array.from({ length: Math.round(business.google_rating) });

  return (
    <section className="relative min-h-[90vh] flex items-center overflow-hidden bg-gradient-to-b from-slate-950 via-orange-950/40 to-slate-950">
      {/* Orange glow - top right */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] rounded-full blur-[160px] opacity-30 pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(249,115,22,0.5) 0%, transparent 70%)" }}
      />

      {/* Subtle glow - bottom left */}
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full blur-[120px] opacity-20 pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(249,115,22,0.35) 0%, transparent 70%)" }}
      />

      {/* Noise texture overlay */}
      <div className="absolute inset-0 opacity-[0.015] pointer-events-none"
        style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E\")" }}
      />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 py-28 lg:py-32">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-20 items-center">

          {/* --- LEFT: Text --- */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeInLeft}
            transition={{ duration: 0.7, ease: "easeOut" }}
          >
            {/* Badge */}
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
            <div className="flex items-center gap-1 mb-5">
              {stars.map((_, i) => (
                <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
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
                className="inline-flex items-center justify-center gap-2.5 px-8 py-4 bg-orange-600 text-white font-semibold text-lg rounded-xl hover:bg-orange-500 transition-all duration-300 shadow-lg shadow-orange-600/30 hover:shadow-orange-600/40 hover:-translate-y-0.5"
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

          {/* --- RIGHT: Visual --- */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeInRight}
            transition={{ duration: 0.7, delay: 0.2, ease: "easeOut" }}
            className="hidden lg:flex items-center justify-center"
          >
            <div className="relative">
              {/* Glow behind the visual */}
              <div className="absolute inset-0 rounded-full blur-[100px] opacity-40"
                style={{ background: "radial-gradient(circle, rgba(249,115,22,0.6) 0%, transparent 60%)" }}
              />

              {/* Abstract roof / protection visual */}
              <div className="relative w-80 h-80">
                {/* Large primary shape */}
                <div className="absolute inset-8 rounded-2xl bg-gradient-to-br from-orange-500/20 to-orange-600/5 border border-orange-500/20 backdrop-blur-sm" />

                {/* Roof triangle */}
                <div className="absolute top-10 left-1/2 -translate-x-1/2">
                  <div
                    className="w-48 h-28 relative"
                    style={{
                      clipPath: "polygon(50% 0%, 100% 100%, 0% 100%)",
                      background: "linear-gradient(180deg, rgba(249,115,22,0.25) 0%, rgba(249,115,22,0.05) 100%)",
                    }}
                  />
                </div>

                {/* Stats pill */}
                <div className="absolute top-14 right-0 bg-slate-900/90 border border-slate-700 rounded-xl px-5 py-3 shadow-2xl">
                  <div className="text-2xl font-bold text-white tabular-nums font-display">
                    {business.google_rating}
                  </div>
                  <div className="flex gap-0.5 mt-1">
                    {stars.map((_, i) => (
                      <Star key={i} className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                </div>

                {/* Years pill */}
                <div className="absolute bottom-12 left-4 bg-slate-900/90 border border-slate-700 rounded-xl px-5 py-3 shadow-2xl">
                  <div className="text-2xl font-bold text-orange-400 tabular-nums font-display">
                    {business.years_in_business || 10}+
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">Years Local</div>
                </div>

                {/* Free inspection badge */}
                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-orange-600 text-white text-sm font-bold px-8 py-3.5 rounded-xl shadow-xl shadow-orange-600/40 border border-orange-500">
                  🛡️ FREE INSPECTION TODAY
                </div>
              </div>
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
