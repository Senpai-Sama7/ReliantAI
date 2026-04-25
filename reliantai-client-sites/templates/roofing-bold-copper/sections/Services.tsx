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
    transition: { delay: i * 0.1, duration: 0.5, ease: "easeOut" as const },
  }),
};

function getIcon(name: string) {
  const Icon = ICON_MAP[name] || Home;
  return <Icon className="h-8 w-8" />;
}

export default function Services({ content, copy }: ServicesProps) {
  const { services } = content;

  return (
    <section className="py-28 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight">
            {copy.services_title}
          </h2>
          <p className="mt-4 text-slate-400 text-lg max-w-2xl mx-auto leading-relaxed">
            {copy.services_subtitle} {content.business.city},{" "}
            {content.business.state}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((service, i) => (
            <motion.div
              key={i}
              custom={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.1 }}
              variants={cardVariants}
              whileHover={{ y: -6, transition: { duration: 0.25 } }}
              className="group bg-slate-900/40 border-2 border-slate-800/60 rounded-xl p-7 hover:border-orange-500/50 hover:bg-slate-900/80 transition-all duration-300"
            >
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-orange-500/10 text-orange-400 mb-5 group-hover:bg-orange-500/20 group-hover:scale-110 transition-all duration-300">
                {getIcon(service.icon)}
              </div>
              <h3 className="font-display text-lg font-semibold text-white mb-2">
                {service.title}
              </h3>
              <p className="text-slate-400 text-sm leading-relaxed mb-5">
                {service.description}
              </p>
              <a
                href={`tel:${content.business.phone}`}
                className="inline-flex items-center text-sm font-semibold text-orange-400 group-hover:text-orange-300 transition-colors"
              >
                {service.cta_text} &rarr;
              </a>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
