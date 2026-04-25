"use client";

import { Droplet, Wrench, Bath, Droplets, Flame, ShieldAlert } from "lucide-react";
import { motion } from "framer-motion";
import { TRADE_COPY } from "@/lib/trade-copy";
import type { SiteContent } from "@/types/SiteContent";

interface ServicesProps {
  content: SiteContent;
}

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  droplet: Droplet,
  wrench: Wrench,
  bath: Bath,
  pipe: Droplets,
  flame: Flame,
  shield: ShieldAlert,
};

function getIcon(name: string) {
  const Icon = ICON_MAP[name] ?? Wrench;
  return <Icon className="h-8 w-8" />;
}

const cardVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, delay: i * 0.08 },
  }),
};

export default function Services({ content }: ServicesProps) {
  const { services } = content;
  const copy = TRADE_COPY[content.site_config.trade as keyof typeof TRADE_COPY] ?? TRADE_COPY.plumbing;

  return (
    <section id="services" className="py-24 bg-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white font-display">
            {copy.services_title}
          </h2>
          <p className="mt-4 text-slate-400 max-w-2xl mx-auto">
            {copy.services_subtitle} {content.business.city}, {content.business.state}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((service, i) => {
            const isFeatured = i === 0;

            return (
              <motion.div
                key={i}
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-50px" }}
                variants={cardVariants}
                className={`rounded-2xl p-7 transition-all duration-300 hover:-translate-y-1.5 group ${
                  isFeatured
                    ? "bg-gradient-to-br from-blue-950/50 to-slate-900/60 border border-blue-500/30 shadow-lg shadow-blue-900/10 hover:shadow-blue-900/25 hover:border-blue-400/40"
                    : "bg-slate-800/40 border border-slate-700/60 hover:shadow-xl hover:shadow-blue-900/10 hover:border-blue-500/30"
                }`}
              >
                {isFeatured && (
                  <span className="inline-block px-2.5 py-0.5 bg-blue-500/15 text-blue-300 text-[0.65rem] font-semibold tracking-widest uppercase rounded-full mb-4">
                    Most Requested
                  </span>
                )}
                <div
                  className={`inline-flex items-center justify-center rounded-xl bg-blue-500/10 text-blue-400 mb-5 group-hover:bg-blue-500/20 transition-colors ${
                    isFeatured ? "w-14 h-14" : "w-12 h-12"
                  }`}
                >
                  {getIcon(service.icon)}
                </div>
                <h3
                  className={`font-semibold text-white mb-2 group-hover:text-blue-200 transition-colors ${
                    isFeatured ? "text-xl" : "text-lg"
                  }`}
                >
                  {service.title}
                </h3>
                <p className="text-slate-400 text-sm leading-relaxed mb-5">
                  {service.description}
                </p>
                <a
                  href={`tel:${content.business.phone}`}
                  className="inline-flex items-center text-sm font-medium text-blue-400 group-hover:text-blue-300 transition-colors"
                >
                  {service.cta_text}
                  <span className="ml-1.5 group-hover:ml-2 transition-all">&rarr;</span>
                </a>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}