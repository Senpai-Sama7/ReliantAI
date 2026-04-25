"use client";

import { Star, Phone, Shield, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";

interface HeroProps {
  content: SiteContent;
}

const wordReveal = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, delay: i * 0.06 },
  }),
};

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export default function Hero({ content }: HeroProps) {
  const { business, hero } = content;
  const stars = Array.from({ length: Math.round(business.google_rating) });
  const headlineWords = hero.headline.split(" ");

  return (
    <section
      id="hero"
      className="relative min-h-[90vh] flex items-center pt-12 overflow-hidden bg-gradient-to-b from-slate-950 via-blue-950/40 to-slate-950"
    >
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-20 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-center">
          {/* --- Left: text content --- */}
          <div className="lg:col-span-3 max-w-2xl">
            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={{ duration: 0.4 }}
              className="flex items-center gap-1 mb-6"
            >
              {stars.map((_, i) => (
                <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />
              ))}
              <span className="ml-2 text-slate-300 text-sm">
                {business.google_rating} ({business.review_count} reviews)
              </span>
            </motion.div>

            <motion.h1
              initial="hidden"
              animate="visible"
              className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-[1.08] mb-6 font-display"
            >
              {headlineWords.map((word, i) => (
                <motion.span
                  key={i}
                  custom={i}
                  variants={wordReveal}
                  className="inline-block mr-[0.3em]"
                >
                  {word}
                </motion.span>
              ))}
            </motion.h1>

            <motion.p
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={{ duration: 0.4, delay: 0.45 }}
              className="text-lg sm:text-xl text-blue-200/80"
            >
              {hero.subheadline}
            </motion.p>

            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={{ duration: 0.4, delay: 0.6 }}
              className="mt-8 flex flex-col sm:flex-row items-start gap-4"
            >
              <a
                href={`tel:${business.phone}`}
                className="inline-flex items-center gap-2.5 px-8 py-3.5 bg-blue-600 text-white font-semibold text-lg rounded-xl hover:bg-blue-500 transition-all shadow-lg shadow-blue-600/25 hover:shadow-blue-600/40"
              >
                <Phone className="h-5 w-5" />
                {hero.cta_primary}
              </a>
              <a
                href="#services"
                className="px-8 py-3.5 border border-blue-400/40 text-blue-200 font-medium text-lg rounded-xl hover:border-blue-300 hover:text-blue-100 hover:bg-blue-950/20 transition-all"
              >
                {hero.cta_secondary}
              </a>
            </motion.div>

            {hero.trust_bar.length > 0 && (
              <motion.div
                initial="hidden"
                animate="visible"
                variants={fadeUp}
                transition={{ duration: 0.4, delay: 0.75 }}
                className="mt-12 flex flex-wrap items-center gap-x-8 gap-y-3"
              >
                {hero.trust_bar.map((item, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 text-slate-400 text-sm"
                  >
                    <Shield className="h-4 w-4 text-blue-400 flex-shrink-0" />
                    <span>{item}</span>
                  </div>
                ))}
              </motion.div>
            )}
          </div>

          {/* --- Right: emergency badge --- */}
          <motion.div
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.25, duration: 0.55, ease: "easeOut" }}
            className="lg:col-span-2 flex items-center justify-center lg:justify-end"
          >
            <div className="relative">
              <div className="absolute inset-0 bg-red-500/15 blur-3xl rounded-full" />
              <div className="relative flex flex-col items-center justify-center w-44 h-44 sm:w-52 sm:h-52 rounded-full border-2 border-red-500/25 bg-red-600/5 backdrop-blur-sm">
                <motion.div
                  animate={{
                    boxShadow: [
                      "0 0 20px rgba(239,68,68,0.15)",
                      "0 0 40px rgba(239,68,68,0.25)",
                      "0 0 20px rgba(239,68,68,0.15)",
                    ],
                  }}
                  transition={{ repeat: Infinity, duration: 2.5, ease: "easeInOut" }}
                  className="absolute inset-0 rounded-full pointer-events-none"
                />
                <AlertTriangle className="h-7 w-7 text-red-400 mb-2" />
                <span className="text-red-400 font-bold text-sm tracking-[0.25em] uppercase">
                  24/7
                </span>
                <span className="text-red-300/80 text-[0.65rem] tracking-[0.2em] uppercase mt-0.5">
                  Emergency
                </span>
                <div className="mt-3 w-8 h-px bg-red-500/20" />
                <Phone className="h-4 w-4 text-red-400/70 mt-2" />
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
