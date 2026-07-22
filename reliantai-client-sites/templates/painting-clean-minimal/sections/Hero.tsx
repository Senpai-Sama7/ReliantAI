"use client";

import { Phone } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface HeroProps {
  content: SiteContent;
}

export default function Hero({ content }: HeroProps) {
  const { business, hero } = content;

  return (
    <section className="relative min-h-[85svh] flex items-end overflow-hidden bg-[var(--trade-surface)] pt-14">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 70% 52% at 86% 18%, color-mix(in oklab, var(--trade-accent) 13%, transparent) 0%, transparent 68%)",
        }}
        aria-hidden
      />
      <div
        className="absolute inset-x-0 top-24 h-px bg-[color-mix(in_oklab,var(--trade-accent)_24%,transparent)]"
        aria-hidden
      />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 pt-28 lg:pb-28 lg:pt-36">
        <div className="max-w-3xl">
          <p className="font-display text-[clamp(2.8rem,7.2vw,5.7rem)] leading-[0.96] tracking-[-0.035em] text-[var(--trade-ink)]">
            {business.business_name}
          </p>

          <h1 className="mt-10 text-xl sm:text-2xl lg:text-3xl font-medium text-[var(--trade-primary)] leading-snug max-w-2xl">
            {hero.headline}
          </h1>

          <p className="mt-6 text-base sm:text-lg text-stone-600 max-w-xl leading-relaxed">
            {hero.subheadline}
          </p>

          <div className="mt-12 flex flex-col sm:flex-row items-start gap-3">
            <a
              href={`tel:${business.phone}`}
              className="btn-trade inline-flex items-center gap-2.5 px-7 py-3.5 font-semibold rounded-md text-sm tracking-wide"
            >
              <Phone className="h-4 w-4" />
              {hero.cta_primary}
            </a>
            <a
              href="#services"
              className="btn-trade-outline px-7 py-3.5 font-medium rounded-md text-sm text-[var(--trade-ink)]"
            >
              {hero.cta_secondary}
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
