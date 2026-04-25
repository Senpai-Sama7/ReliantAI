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
    <section className="relative min-h-screen flex items-center pt-12 overflow-hidden bg-gradient-to-b from-slate-950 via-blue-950/60 to-slate-950">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 70% 50% at 60% 50%, rgba(96,165,250,0.08) 0%, transparent 70%)",
        }}
      />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
        <div className="max-w-2xl">
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
            className="mt-5 text-lg sm:text-xl text-blue-200/80 max-w-xl leading-relaxed"
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
              className="inline-flex items-center gap-2.5 px-8 py-3.5 bg-blue-600 text-white font-semibold text-lg rounded-xl hover:bg-blue-500 transition-all duration-300 shadow-lg shadow-blue-600/25 hover:shadow-blue-500/30"
            >
              <Phone className="h-5 w-5" />
              {hero.cta_primary}
            </a>
            <a
              href="#services"
              className="px-8 py-3.5 border border-blue-400/40 text-blue-200 font-medium text-lg rounded-xl hover:border-blue-300 hover:text-white transition-all duration-300"
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
                  <Shield className="h-3.5 w-3.5 text-blue-400/70" />
                  {item}
                </div>
              ))}
            </motion.div>
          )}
        </div>
      </div>

      <div className="absolute bottom-0 inset-x-0 h-32 bg-gradient-to-t from-slate-950 to-transparent pointer-events-none" />
    </section>
  );
}