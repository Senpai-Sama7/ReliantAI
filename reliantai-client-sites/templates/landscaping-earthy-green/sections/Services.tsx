"use client";

import { TreePine, Flower2, Shovel, Tractor, Sun, Sprout } from "lucide-react";
import { motion } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";

interface TradeCopy {
  services_title: string;
  services_subtitle: string;
  about_title: string;
  about_trust_title: string;
  reviews_title: string;
  faq_title: string;
  urgency_message: string;
  estimate_heading: string;
  estimate_subtext: string;
  trust_badges: string[];
  stats: { label: string; value_key: string; suffix: string; fallback: string }[];
}

interface ServicesProps {
  content: SiteContent;
  copy: TradeCopy;
}

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  "tree-pine": TreePine,
  flower2: Flower2,
  shovel: Shovel,
  tractor: Tractor,
  sun: Sun,
  sprout: Sprout,
};

function getIcon(name: string) {
  const Icon = ICON_MAP[name] || Sprout;
  return <Icon className="h-8 w-8" />;
}

const gridStagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
};

const cardFade = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export default function Services({ content, copy }: ServicesProps) {
  const { services } = content;

  return (
    <section className="relative py-28 bg-slate-900 overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 rounded-full bg-emerald-600/3 blur-3xl" />
      </div>
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-white font-display">
            {copy.services_title}
          </h2>
          <p className="mt-3 text-slate-400 max-w-2xl mx-auto">
            {copy.services_subtitle} {content.business.city}, {content.business.state}
          </p>
        </div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          variants={gridStagger}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {services.map((service, i) => {
            const isFeatured = i === 0;
            return (
              <motion.div
                key={i}
                variants={cardFade}
                className={`rounded-xl p-6 transition-all duration-300 group ${
                  isFeatured
                    ? "bg-emerald-900/30 border-2 border-emerald-500/40 hover:border-emerald-400/60 shadow-lg shadow-emerald-500/10"
                    : "bg-slate-800/50 border border-slate-700/80 hover:-translate-y-1 hover:shadow-xl hover:border-emerald-500/50"
                }`}
              >
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg mb-4 ${
                  isFeatured ? "bg-emerald-400/20 text-emerald-300" : "bg-emerald-500/10 text-emerald-400"
                }`}>
                  {getIcon(service.icon)}
                </div>
                <h3 className={`text-lg font-semibold mb-2 ${
                  isFeatured ? "text-emerald-100" : "text-white"
                }`}>
                  {service.title}
                </h3>
                <p className={`text-sm leading-relaxed mb-4 ${
                  isFeatured ? "text-emerald-200/70" : "text-slate-400"
                }`}>
                  {service.description}
                </p>
                <a
                  href={`tel:${content.business.phone}`}
                  className={`inline-flex items-center text-sm font-medium transition-colors ${
                    isFeatured
                      ? "text-emerald-300 group-hover:text-emerald-200"
                      : "text-emerald-400 group-hover:text-emerald-300"
                  }`}
                >
                  {service.cta_text} →
                </a>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}