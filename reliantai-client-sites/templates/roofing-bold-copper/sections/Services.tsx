"use client";

import { Home, ShieldCheck, CloudRain, Wind, Sun, Umbrella } from "lucide-react";
import { motion } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";

interface ServicesProps {
  content: SiteContent;
  copy: TradeCopy;
}

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  home: Home,
  "shield-check": ShieldCheck,
  "cloud-rain": CloudRain,
  wind: Wind,
  sun: Sun,
  umbrella: Umbrella,
};

const cardVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.5, ease: "easeOut" as const },
  }),
};

function getIcon(name: string) {
  const Icon = ICON_MAP[name] || Home;
  return <Icon className="h-7 w-7" />;
}

export default function Services({ content, copy }: ServicesProps) {
  const { services, business } = content;
  const featured = 0;

  return (
    <section className="py-28 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight">
            {copy.services_title}
          </h2>
          <p className="mt-4 text-slate-400 text-lg max-w-2xl mx-auto leading-relaxed">
            {copy.services_subtitle} {business.city}, {business.state}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((service, i) => {
            const isFeatured = i === featured;
            return (
              <motion.div
                key={i}
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, amount: 0.1 }}
                variants={cardVariants}
                whileHover={{ y: -6, transition: { duration: 0.25 } }}
                className={`group rounded-xl p-7 transition-all duration-300 ${
                  isFeatured
                    ? "bg-orange-500/10 border-2 border-orange-500/40 shadow-lg shadow-orange-500/10"
                    : "bg-slate-900/40 border-2 border-slate-800/60 hover:border-orange-500/50 hover:bg-slate-900/80"
                }`}
              >
                <div
                  className={`inline-flex items-center justify-center w-14 h-14 rounded-xl mb-5 transition-all duration-300 ${
                    isFeatured
                      ? "bg-orange-500 text-white group-hover:scale-110"
                      : "bg-orange-500/10 text-orange-400 group-hover:bg-orange-500/20 group-hover:scale-110"
                  }`}
                >
                  {getIcon(service.icon)}
                </div>
                {isFeatured && (
                  <span className="inline-block bg-orange-500/15 text-orange-400 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full mb-3 border border-orange-500/25">
                    Most Popular
                  </span>
                )}
                <h3 className="font-display text-lg font-semibold text-white mb-2">
                  {service.title}
                </h3>
                <p className="text-slate-400 text-sm leading-relaxed mb-5">
                  {service.description}
                </p>
                <a
                  href={`tel:${business.phone}`}
                  className={`inline-flex items-center text-sm font-semibold transition-colors ${
                    isFeatured
                      ? "text-orange-300 hover:text-orange-200"
                      : "text-orange-400 hover:text-orange-300"
                  }`}
                >
                  {service.cta_text} →
                </a>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}