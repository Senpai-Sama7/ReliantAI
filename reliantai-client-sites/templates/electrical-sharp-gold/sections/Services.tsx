"use client";

import { Zap, Plug, Lightbulb, Wrench, ShieldAlert, Sun } from "lucide-react";
import { motion } from "framer-motion";
import { TRADE_COPY } from "@/lib/trade-copy";
import type { SiteContent } from "@/types/SiteContent";

interface ServicesProps {
  content: SiteContent;
}

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  zap: Zap,
  plug: Plug,
  lightbulb: Lightbulb,
  wrench: Wrench,
  shield: ShieldAlert,
  sun: Sun,
};

function getIcon(name: string) {
  const Icon = ICON_MAP[name] || Wrench;
  return <Icon className="h-8 w-8" />;
}

const container = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.08 },
  },
};

const card = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export default function Services({ content }: ServicesProps) {
  const { services } = content;
  const copy = TRADE_COPY[content.site_config.trade] || TRADE_COPY.electrical;

  return (
    <section id="services" className="py-28 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
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
          variants={container}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {services.map((service, i) => (
            <motion.div
              key={i}
              variants={card}
              className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 hover:border-amber-500/50 hover:-translate-y-1 transition-all duration-200 group"
            >
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg mb-4 bg-amber-950/40 text-amber-400">
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
                className="inline-flex items-center text-sm font-medium text-amber-400 group-hover:text-amber-300 transition-colors"
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
