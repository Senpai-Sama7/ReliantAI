"use client";

import { Star, Phone, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";
import { fadeUp, premiumTransition } from "@/lib/motion";

interface HeroProps {
  content: SiteContent;
}

export default function Hero({ content }: HeroProps) {
  const { business, hero } = content;
  const stars = Array.from({ length: Math.round(business.google_rating) });

  return (
    <section className="relative min-h-[85vh] flex items-center pt-12 overflow-hidden bg-white">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 45% 40% at 80% 35%, rgba(124,58,237,0.05) 0%, transparent 70%)",
        }}
        aria-hidden
      />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-16 lg:py-24 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_3fr] gap-12 items-center">
          <div className="max-w-xl">
            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0, 0.4)}
              className="flex items-center gap-1 mb-6"
            >
              {stars.map((_, i) => (
                <Star key={i} className="h-4 w-4 fill-amber-400 text-amber-400" />
              ))}
              <span className="ml-2 text-slate-500 text-sm">
                {business.google_rating} · {business.review_count} reviews
              </span>
            </motion.div>

            <motion.h1
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.08)}
              className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 leading-[1.08] font-display tracking-tight"
            >
              {hero.headline}
            </motion.h1>

            <motion.p
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.16)}
              className="mt-5 text-lg sm:text-xl text-slate-600 leading-relaxed"
            >
              {hero.subheadline}
            </motion.p>

            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={premiumTransition(0.24)}
              className="mt-8 flex flex-col sm:flex-row items-start gap-3"
            >
              <a
                href={`tel:${business.phone}`}
                className="inline-flex items-center gap-2 px-7 py-3 bg-violet-700 text-white font-semibold rounded-md hover:bg-violet-600"
              >
                <Phone className="h-4 w-4" />
                {hero.cta_primary}
              </a>
              <a
                href="#services"
                className="px-7 py-3 border border-stone-300 text-violet-800 font-medium rounded-md hover:bg-violet-50"
              >
                {hero.cta_secondary}
              </a>
            </motion.div>

            {hero.trust_bar.length > 0 && (
              <motion.div
                initial="hidden"
                animate="visible"
                variants={fadeUp}
                transition={premiumTransition(0.32)}
                className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-2"
              >
                {hero.trust_bar.map((item, i) => (
                  <div key={i} className="flex items-center gap-2 text-slate-500 text-sm">
                    <ShieldCheck className="h-4 w-4 text-violet-600" />
                    {item}
                  </div>
                ))}
              </motion.div>
            )}
          </div>

          <motion.aside
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            transition={premiumTransition(0.2, 0.5)}
            className="hidden lg:block"
          >
            <div className="border border-stone-200 bg-stone-50 rounded-lg p-8 max-w-sm ml-auto">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-600 mb-4">
                Color consultation
              </p>
              <p className="font-display text-3xl text-slate-900">Included free</p>
              <p className="text-slate-600 text-sm mt-3 leading-relaxed">
                Every estimate includes an on-site palette review with a certified color specialist.
              </p>
              <p className="mt-6 pt-6 border-t border-stone-200 text-slate-500 text-sm">
                Serving {business.city} since {new Date().getFullYear() - (business.years_in_business || 10)}
              </p>
            </div>
          </motion.aside>
        </div>
      </div>
    </section>
  );
}
