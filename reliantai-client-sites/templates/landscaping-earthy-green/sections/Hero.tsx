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
      {/* Single subtle emerald glow */}
      <div className="absolute top-1/3 right-0 w-[800px] h-[600px] pointer-events-none bg-emerald-500/5 blur-3xl rounded-full" />
      {/* Bottom fade into next section */}
      <div className="absolute bottom-0 inset-x-0 h-32 bg-gradient-to-t from-slate-950 to-transparent pointer-events-none" />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
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

          <motion.div
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
            className="hidden lg:flex items-center justify-center"
          >
            <div className="relative w-72 h-72">
              <div className="absolute inset-0 rounded-full bg-emerald-500/10 blur-2xl" />
              <div className="absolute inset-[25%] rounded-full bg-emerald-600/15 border border-emerald-500/10" />
              <div className="absolute inset-[45%] rounded-full bg-emerald-400/10" />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}