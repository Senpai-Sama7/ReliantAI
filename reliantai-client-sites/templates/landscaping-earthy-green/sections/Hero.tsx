"use client";

import { Star, Phone, Shield } from "lucide-react";
import { motion } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";

interface HeroProps {
  content: SiteContent;
}

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

const wordReveal = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.45, ease: "easeOut" as const } },
};

const fadeIn = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
};

export default function Hero({ content }: HeroProps) {
  const { business, hero } = content;
  const words = hero.headline.split(" ");

  const stars = Array.from({ length: Math.round(business.google_rating) });

  return (
    <section className="relative min-h-screen flex items-center pt-12 overflow-hidden bg-gradient-to-b from-slate-950 via-emerald-950/30 to-slate-950">
      {/* Layered gradient blobs — organic, nature feel */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -right-40 w-[640px] h-[640px] rounded-full bg-emerald-600/5 blur-3xl" />
        <div className="absolute top-1/3 -left-20 w-[400px] h-[400px] rounded-full bg-emerald-500/4 blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-[300px] h-[300px] rounded-full bg-teal-600/4 blur-3xl" />
      </div>

      {/* Radial glow behind the nature visual */}
      <div
        className="absolute top-1/2 right-0 -translate-y-1/2 w-[800px] h-[600px] pointer-events-none"
        style={{
          background: "radial-gradient(ellipse at center, rgba(52,211,153,0.12) 0%, rgba(52,211,153,0.03) 50%, transparent 75%)",
        }}
      />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* LEFT: text content */}
          <div>
            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeIn}
              transition={{ duration: 0.5 }}
              className="flex items-center gap-1 mb-6"
            >
              {stars.map((_, i) => (
                <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />
              ))}
              <span className="ml-2 text-slate-400 text-sm tracking-wide">
                {business.google_rating} ({business.review_count} reviews)
              </span>
            </motion.div>

            <motion.h1
              initial="hidden"
              animate="visible"
              variants={staggerContainer}
              className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-bold text-white leading-[1.08] mb-2 font-display"
            >
              {words.map((word, i) => (
                <motion.span key={i} variants={wordReveal} className="inline-block mr-[0.3em]">
                  {word}
                </motion.span>
              ))}
            </motion.h1>

            <motion.p
              initial="hidden"
              animate="visible"
              variants={fadeIn}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="mt-5 text-lg sm:text-xl text-emerald-200/80 max-w-xl leading-relaxed"
            >
              {hero.subheadline}
            </motion.p>

            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeIn}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="mt-8 flex flex-col sm:flex-row items-start gap-4"
            >
              <a
                href={`tel:${business.phone}`}
                className="inline-flex items-center gap-2.5 px-8 py-3.5 bg-emerald-600 text-white font-semibold text-lg rounded-xl hover:bg-emerald-500 transition-all duration-300 shadow-lg shadow-emerald-600/25 hover:shadow-emerald-500/30"
              >
                <Phone className="h-5 w-5" />
                {hero.cta_primary}
              </a>
              <a
                href="#services"
                className="px-8 py-3.5 border border-emerald-400/40 text-emerald-200 font-medium text-lg rounded-xl hover:border-emerald-300 hover:text-white transition-all duration-300"
              >
                {hero.cta_secondary}
              </a>
            </motion.div>

            {hero.trust_bar.length > 0 && (
              <motion.div
                initial="hidden"
                animate="visible"
                variants={fadeIn}
                transition={{ duration: 0.5, delay: 0.5 }}
                className="mt-10 flex flex-wrap items-center gap-x-8 gap-y-3"
              >
                {hero.trust_bar.map((item, i) => (
                  <div key={i} className="flex items-center gap-2 text-slate-500 text-xs uppercase tracking-wider font-medium">
                    <Shield className="h-3.5 w-3.5 text-emerald-400/70" />
                    {item}
                  </div>
                ))}
              </motion.div>
            )}
          </div>

          {/* RIGHT: decorative nature visual element */}
          <motion.div
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
            className="hidden lg:flex items-center justify-center"
          >
            <div className="relative w-full max-w-md aspect-square">
              {/* Outer glow ring */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-br from-emerald-500/15 via-emerald-600/5 to-transparent blur-2xl" />
              {/* Center orb — earth/nature */}
              <div className="absolute inset-[15%] rounded-full bg-gradient-to-br from-emerald-600/20 via-emerald-500/10 to-emerald-900/5 border border-emerald-500/10 shadow-[0_0_120px_rgba(52,211,153,0.08)]" />
              {/* Inner accent */}
              <div className="absolute inset-[35%] rounded-full bg-gradient-to-tr from-emerald-400/10 to-transparent" />
              {/* Floating smaller orbs */}
              <div className="absolute top-[5%] right-[10%] w-20 h-20 rounded-full bg-teal-500/10 blur-xl" />
              <div className="absolute bottom-[10%] left-[5%] w-16 h-16 rounded-full bg-emerald-400/8 blur-xl" />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
