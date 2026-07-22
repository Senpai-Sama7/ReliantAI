"use client";

import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import ScrollReveal from "@/components/shared/ScrollReveal";

interface ServicesProps {
  content: SiteContent;
  copy: TradeCopy;
}

export default function Services({ content, copy }: ServicesProps) {
  const { services } = content;

  return (
    <section className="relative bg-[var(--trade-surface)] py-28">
      <div className="absolute top-0 inset-x-0 border-t border-white/5" />
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6">
        <ScrollReveal className="mb-16 max-w-2xl">
          <p className="mb-4 text-[0.65rem] font-semibold uppercase tracking-[0.3em] text-[var(--trade-accent)]">
            Clean circuits, sharp work
          </p>
          <h2 className="font-display text-3xl text-white sm:text-4xl lg:text-5xl tracking-tight leading-[1.1]">
            {copy.services_title}
          </h2>
          <p className="mt-4 max-w-2xl text-slate-400 leading-relaxed">
            {copy.services_subtitle} {content.business.city}, {content.business.state}
          </p>
        </ScrollReveal>

        <ol className="grid grid-cols-1 gap-x-8 gap-y-10 lg:grid-cols-12">
          {services.map((service, i) => {
            const featured = i === 0;
            return (
              <ScrollReveal
                key={i}
                as="li"
                delayMs={i * 55}
                className={
                  featured
                    ? "lg:col-span-12 border-l-2 border-[var(--trade-accent)] pl-6 sm:pl-8"
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
                      href={`tel:${content.business.phone}`}
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