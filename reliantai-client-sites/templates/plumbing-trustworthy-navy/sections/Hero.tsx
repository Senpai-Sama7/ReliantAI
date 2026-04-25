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
      className="relative min-h-[90vh] flex items-center pt-12 overflow-hidden"
    >
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-blue-950/30 to-slate-900" />
      <div className="absolute top-24 left-16 w-[500px] h-[400px] bg-blue-400/5 blur-3xl rounded-full pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-20 w-full">
        <div className="max-w-2xl">
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            transition={{ duration: 0.4 }}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-red-500/10 border border-red-500/20 rounded-full mb-6"
          >
            <AlertTriangle className="h-3.5 w-3.5 text-red-400" />
            <span className="text-red-300 text-xs font-semibold tracking-widest uppercase">
              24/7 Emergency Service
            </span>
          </motion.div>

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
      </div>

      <div className="absolute bottom-0 inset-x-0 h-24 bg-gradient-to-t from-slate-900 to-transparent pointer-events-none" />
    </section>
  );
}