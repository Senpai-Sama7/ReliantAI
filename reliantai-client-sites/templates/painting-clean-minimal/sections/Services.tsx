"use client";

import { Paintbrush, Palette, Brush, Home, ShieldCheck, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";

interface ServicesProps {
  content: SiteContent;
  copy: {
    services_title: string;
    services_subtitle: string;
  };
}

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  paintbrush: Paintbrush,
  palette: Palette,
  brush: Brush,
  home: Home,
  shield: ShieldCheck,
  sparkles: Sparkles,
};

function getIcon(name: string) {
  const Icon = ICON_MAP[name] || Paintbrush;
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
    <section className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 font-display tracking-tight">
            {copy.services_title}
          </h2>
          <p className="mt-3 text-slate-500 max-w-2xl mx-auto">
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
            const isFeatured = i === 0 && services.length >= 3;
            return (
              <motion.div
                key={i}
                variants={cardFade}
                className={`rounded-lg p-6 transition-[transform,border-color,box-shadow] duration-300 group ${
                  isFeatured
                    ? "md:col-span-2 bg-amber-50 border-2 border-amber-200 hover:border-amber-600/40 shadow-md"
                    : "bg-white border border-stone-200 hover:-translate-y-1 hover:border-amber-600/40"
                }`}
              >
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-md mb-4 ${
                  isFeatured ? "bg-amber-700 text-white" : "bg-amber-50 text-amber-700"
                }`}>
                  {getIcon(service.icon)}
                </div>
                <h3 className={`text-lg font-semibold mb-2 ${
                  isFeatured ? "text-stone-900" : "text-slate-900"
                }`}>
                  {service.title}
                </h3>
                <p className={`text-sm leading-relaxed mb-4 ${
                  isFeatured ? "text-amber-700/80" : "text-slate-600"
                }`}>
                  {service.description}
                </p>
                <a
                  href={`tel:${content.business.phone}`}
                  className={`inline-flex items-center text-sm font-medium transition-colors ${
                    isFeatured
                      ? "text-amber-700 group-hover:text-amber-900"
                      : "text-amber-700 group-hover:text-amber-700"
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