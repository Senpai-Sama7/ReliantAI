"use client";

import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import ScrollReveal from "@/components/shared/ScrollReveal";

interface EditorialServicesProps {
  content: SiteContent;
  copy: TradeCopy;
  light?: boolean;
}

/**
 * Numbered editorial services — stacked on mobile (no side-by-side smash),
 * asymmetric 12-col on large screens. Never grid-cols-3 equal cards.
 */
export default function EditorialServices({
  content,
  copy,
  light = false,
}: EditorialServicesProps) {
  const { services } = content;
  const title = light ? "text-[var(--trade-ink)]" : "text-white";
  const body = light ? "text-stone-600" : "text-[var(--trade-muted)]";
  const rule = light ? "border-stone-200" : "border-white/10";
  const sectionBg = light ? "bg-[var(--trade-elevated)]" : "bg-[var(--trade-surface)]";

  return (
    <section className={`relative craft-section ${sectionBg}`}>
      <div className={`absolute top-0 inset-x-0 border-t ${rule}`} />
      <div className="craft-container relative">
        <ScrollReveal className="max-w-2xl mb-10 sm:mb-14">
          <p className="craft-eyebrow mb-3 sm:mb-4">Services</p>
          <h2 className={`craft-display ${title}`}>{copy.services_title}</h2>
          <p className={`mt-3 sm:mt-4 leading-relaxed ${body}`}>
            {copy.services_subtitle} {content.business.city}, {content.business.state}
          </p>
        </ScrollReveal>

        <ol className="grid grid-cols-1 lg:grid-cols-12 gap-0">
          {services.map((service, i) => {
            const featured = i === 0;
            return (
              <ScrollReveal
                key={i}
                as="li"
                delayMs={Math.min(i * 50, 200)}
                className={`border-t ${rule} py-7 sm:py-9 ${
                  featured ? "lg:col-span-12" : "lg:col-span-6 lg:odd:pr-8 lg:even:pl-8"
                }`}
              >
                {/* Mobile: number above copy. Desktop featured: large side number. */}
                <div
                  className={`flex flex-col gap-3 ${
                    featured ? "sm:flex-row sm:gap-8 sm:items-start" : "sm:flex-row sm:gap-5 sm:items-start"
                  }`}
                >
                  <span
                    className={`font-display tabular-nums leading-none text-[var(--trade-accent)] ${
                      featured ? "text-4xl sm:text-5xl lg:text-6xl" : "text-2xl sm:text-3xl"
                    }`}
                    aria-hidden
                  >
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div className={featured ? "max-w-3xl min-w-0" : "max-w-md min-w-0"}>
                    <h3
                      className={`font-display tracking-tight text-balance ${title} ${
                        featured ? "text-xl sm:text-2xl lg:text-3xl" : "text-lg sm:text-xl"
                      }`}
                    >
                      {service.title}
                    </h3>
                    <p
                      className={`mt-2.5 sm:mt-3 leading-relaxed ${body} ${
                        featured ? "text-[0.975rem] sm:text-base lg:text-lg" : "text-sm sm:text-[0.95rem]"
                      }`}
                    >
                      {service.description}
                    </p>
                    <a
                      href={`tel:${content.business.phone}`}
                      className="inline-flex min-h-11 items-center mt-4 text-sm font-medium text-[var(--trade-accent)] hover:opacity-80"
                    >
                      {service.cta_text}
                      <span aria-hidden className="ml-1.5">
                        →
                      </span>
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
