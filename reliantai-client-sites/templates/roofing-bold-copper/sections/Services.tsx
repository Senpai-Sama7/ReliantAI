"use client";

import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import ScrollReveal from "@/components/shared/ScrollReveal";

interface ServicesProps {
  content: SiteContent;
  copy: TradeCopy;
}

export default function Services({ content, copy }: ServicesProps) {
  const { services, business } = content;

  return (
    <section className="relative py-28 bg-[var(--trade-surface)]">
      <div className="absolute top-0 inset-x-0 border-t border-white/5" />
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
        <ScrollReveal className="max-w-2xl mb-16">
          <p className="text-[0.65rem] uppercase tracking-[0.28em] text-[var(--trade-accent)] mb-4">
            Roofline priorities
          </p>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl text-white tracking-tight leading-[1.1]">
            {copy.services_title}
          </h2>
          <p className="mt-4 text-slate-400 leading-relaxed">
            {copy.services_subtitle} {business.city}, {business.state}
          </p>
        </ScrollReveal>

        <ol className="grid grid-cols-1 lg:grid-cols-12 gap-x-8 gap-y-10">
          {services.map((service, i) => {
            const featured = i === 0;
            return (
              <ScrollReveal
                key={i}
                as="li"
                delayMs={i * 60}
                className={
                  featured
                    ? "lg:col-span-12 border-t-2 border-[var(--trade-accent)] pt-10"
                    : "lg:col-span-6 border-t border-white/10 pt-8"
                }
              >
                <div className={`flex gap-6 ${featured ? "lg:gap-10" : ""}`}>
                  <span
                    className={`font-display tabular-nums leading-none text-[var(--trade-accent)] ${
                      featured ? "text-5xl lg:text-6xl" : "text-3xl"
                    }`}
                    aria-hidden
                  >
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div className={featured ? "max-w-3xl" : "max-w-md"}>
                    <h3
                      className={`font-display text-white tracking-tight ${
                        featured ? "text-2xl sm:text-3xl" : "text-xl"
                      }`}
                    >
                      {service.title}
                    </h3>
                    <p
                      className={`mt-3 text-slate-400 leading-relaxed ${
                        featured ? "text-base sm:text-lg" : "text-sm"
                      }`}
                    >
                      {service.description}
                    </p>
                    <a
                      href={`tel:${business.phone}`}
                      className="inline-flex mt-5 text-sm font-medium text-[var(--trade-accent)] hover:text-white"
                    >
                      {service.cta_text} →
                    </a>
                  </div>
                </div>
              </ScrollReveal>
            );
          })}
        </ol>
      </div>
    </section>
  );
}