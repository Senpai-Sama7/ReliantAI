"use client";

import { Wrench, Snowflake, Flame, Wind, Thermometer, ShieldAlert } from "lucide-react";
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
  wrench: Wrench,
  snowflake: Snowflake,
  flame: Flame,
  wind: Wind,
  thermometer: Thermometer,
  shield: ShieldAlert,
};

function getIcon(name: string) {
  const Icon = ICON_MAP[name] || Wrench;
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
  const theme = content.site_config.theme;

  return (
    <section className="relative py-24 bg-slate-900">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 rounded-full bg-blue-600/3 blur-3xl" />
      </div>
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-white font-display">
            {copy.services_title}
          </h2>
          <p className="mt-3 text-slate-400 max-w-2xl mx-auto">
            {copy.services_subtitle} {content.business.city},{" "}
            {content.business.state}
          </p>
        </div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          variants={gridStagger}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {services.map((service, i) => (
            <motion.div
              key={i}
              variants={cardFade}
              className="bg-slate-800/50 border border-slate-700/80 rounded-xl p-6 hover:-translate-y-1 hover:shadow-xl hover:border-blue-500/50 transition-all duration-300 group"
            >
              <div
                className="inline-flex items-center justify-center w-12 h-12 rounded-lg mb-4"
                style={{ backgroundColor: `${theme.primary}20`, color: theme.accent }}
              >
                {getIcon(service.icon)}
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                {service.title}
              </h3>
              <p className="text-slate-400 text-sm leading-relaxed mb-4">
                {service.description}
              </p>
              <a
                href={`tel:${content.business.phone}`}
                className="inline-flex items-center text-sm font-medium text-blue-400 group-hover:text-blue-300 transition-colors"
              >
                {service.cta_text} &rarr;
              </a>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
