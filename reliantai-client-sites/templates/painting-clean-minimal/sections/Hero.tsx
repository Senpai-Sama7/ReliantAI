"use client";

import { Star, Phone, ShieldCheck } from "lucide-react";
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
  hidden: { opacity: 0, y: 24 },
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
    <section className="relative min-h-screen flex items-center pt-12 overflow-hidden bg-gradient-to-b from-white via-violet-50/30 to-white">
      {/* Primary violet glow — right side */}
      <div
        className="absolute top-1/4 -right-32 w-[640px] h-[640px] pointer-events-none"
        style={{
          background: "radial-gradient(ellipse at center, rgba(124,58,237,0.10) 0%, rgba(124,58,237,0.03) 40%, transparent 70%)",
        }}
      />
      {/* Secondary violet glow — left side */}
      <div
        className="absolute bottom-0 left-0 w-[480px] h-[480px] pointer-events-none"
        style={{
          background: "radial-gradient(ellipse at center, rgba(124,58,237,0.05) 0%, transparent 70%)",
        }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-20 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
        {/* Left: Text content */}
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
            <span className="ml-2 text-slate-500 text-sm font-medium">
              {business.google_rating} ({business.review_count} reviews)
            </span>
          </motion.div>

          <motion.h1
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
            className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 leading-tight mb-2 font-display tracking-tight"
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
            className="mt-5 text-lg sm:text-xl text-slate-600 max-w-xl leading-relaxed"
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
              className="inline-flex items-center gap-2 px-8 py-3.5 bg-violet-600 text-white font-semibold text-lg rounded-xl hover:bg-violet-500 transition-colors shadow-lg shadow-violet-600/25"
            >
              <Phone className="h-5 w-5" />
              {hero.cta_primary}
            </a>
            <a
              href="#services"
              className="px-8 py-3.5 border border-violet-200 text-violet-700 font-medium text-lg rounded-xl hover:bg-violet-50 hover:border-violet-300 transition-colors"
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
              className="mt-12 flex flex-wrap items-center gap-x-8 gap-y-3"
            >
              {hero.trust_bar.map((item, i) => (
                <div key={i} className="flex items-center gap-2 text-slate-500 text-sm">
                  <ShieldCheck className="h-4 w-4 text-violet-500" />
                  {item}
                </div>
              ))}
            </motion.div>
          )}
        </div>

        {/* Right: Paint-themed abstract visual */}
        <div className="hidden lg:flex items-center justify-center">
          <div className="relative w-80 h-80">
            <div className="absolute top-0 right-0 w-52 h-52 rounded-full bg-violet-200/50 blur-sm" />
            <div className="absolute bottom-8 left-4 w-40 h-40 rounded-full bg-violet-100/70 blur-sm" />
            <div className="absolute top-16 left-14 w-28 h-28 rounded-full bg-violet-300/40 blur-sm" />
            <div className="absolute top-6 left-28 w-10 h-10 rounded-full bg-violet-400/30" />
            <div className="absolute bottom-2 right-20 w-7 h-7 rounded-full bg-violet-500/25" />
            <div className="absolute top-28 right-10 w-4 h-4 rounded-full bg-stone-300/50" />
          </div>
        </div>
      </div>
    </section>
  );
}
