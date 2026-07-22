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
    <section className="relative py-28 bg-[var(--trade-elevated)]">
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
        <ScrollReveal className="mb-20 max-w-2xl">
          <p className="mb-4 text-[0.65rem] uppercase tracking-[0.28em] text-[var(--trade-accent)]">
            Finish schedule
          </p>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-display text-[var(--trade-ink)] tracking-tight leading-[1.1]">
            {copy.services_title}
          </h2>
          <p className="mt-4 text-stone-600 max-w-2xl leading-relaxed">
            {copy.services_subtitle} {content.business.city}, {content.business.state}
          </p>
        </ScrollReveal>

        <ol className="grid grid-cols-1 lg:grid-cols-12 gap-x-10 gap-y-12">
          {services.map((service, i) => {
            const featured = i === 0;
            return (
              <ScrollReveal
                key={i}
                as="li"
                delayMs={i * 65}
                className={
                  featured
                    ? "lg:col-span-12 border-t border-[color-mix(in_oklab,var(--trade-accent)_36%,transparent)] pt-10"
                    : "lg:col-span-6 border-t border-stone-200 pt-8"
                }
              >
                <div className={`flex gap-6 ${featured ? "lg:gap-12" : ""}`}>
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
                      className={`font-display text-[var(--trade-ink)] tracking-tight ${
                        featured ? "text-2xl sm:text-3xl" : "text-xl"
                      }`}
                    >
                      {service.title}
                    </h3>
                    <p
                      className={`mt-3 text-stone-600 leading-relaxed ${
                        featured ? "text-base sm:text-lg" : "text-sm"
                      }`}
                    >
                      {service.description}
                    </p>
                    <a
                      href={`tel:${content.business.phone}`}
                      className="inline-flex mt-5 text-sm font-medium text-[var(--trade-primary)] hover:text-[var(--trade-ink)]"
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