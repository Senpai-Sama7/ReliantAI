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
  visible: { transition: { staggerChildren: 0.08 } },
};

const card = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export default function Services({ content }: ServicesProps) {
  const { services } = content;
  const copy = TRADE_COPY[content.site_config.trade] || TRADE_COPY.electrical;
  const featuredIndex = Math.min(2, services.length - 1);

  return (
    <section id="services" className="bg-slate-950 py-28">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="mb-14 text-center">
          <h2 className="font-display text-3xl font-bold text-white sm:text-4xl">
            {copy.services_title}
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-slate-400">
            {copy.services_subtitle} {content.business.city}, {content.business.state}
          </p>
        </div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
          className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3"
        >
          {services.map((service, i) => {
            const isFeatured = i === featuredIndex;
            return (
              <motion.div
                key={i}
                variants={card}
                className={`rounded-xl p-6 transition-all duration-200 group hover:-translate-y-1 ${
                  isFeatured
                    ? "border-2 border-amber-500/40 bg-amber-950/30 shadow-lg shadow-amber-500/10 hover:border-amber-400/60"
                    : "border border-slate-800 bg-slate-900/50 hover:border-amber-500/50"
                }`}
              >
                {isFeatured && (
                  <span className="mb-3 inline-block rounded-full bg-amber-500/20 px-3 py-0.5 text-xs font-semibold uppercase tracking-wider text-amber-300">
                    Most Popular
                  </span>
                )}
                <div
                  className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg ${
                    isFeatured
                      ? "bg-amber-500/20 text-amber-300"
                      : "bg-amber-950/40 text-amber-400"
                  }`}
                >
                  {getIcon(service.icon)}
                </div>
                <h3 className="mb-2 text-lg font-semibold text-white">{service.title}</h3>
                <p className="mb-4 text-sm leading-relaxed text-slate-400">{service.description}</p>
                <a
                  href={`tel:${content.business.phone}`}
                  className={`inline-flex items-center text-sm font-medium transition-colors ${
                    isFeatured
                      ? "text-amber-300 group-hover:text-amber-200"
                      : "text-amber-400 group-hover:text-amber-300"
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