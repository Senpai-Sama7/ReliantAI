"use client";

import { Phone } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface HeroProps {
  content: SiteContent;
}

/**
 * T1 brand-first hero — business name is the hero-level signal.
 * Budget: brand + headline + one sentence + CTAs + atmosphere.
 * Proof (stars, trust bar, credential cards) lives below the fold.
 */
export default function Hero({ content }: HeroProps) {
  const { business, hero } = content;

  return (
    <section className="relative min-h-[85svh] flex items-end overflow-hidden bg-[var(--trade-ink)] atmosphere-grain pt-14">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 70% 55% at 85% 20%, color-mix(in oklab, var(--trade-accent) 14%, transparent) 0%, transparent 65%)",
        }}
        aria-hidden
      />
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.04]"
        style={{
          backgroundImage:
            "linear-gradient(to right, currentColor 1px, transparent 1px), linear-gradient(to bottom, currentColor 1px, transparent 1px)",
          backgroundSize: "72px 72px",
          color: "var(--trade-accent)",
        }}
        aria-hidden
      />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16 pt-24 lg:pb-24 lg:pt-32">
        <div className="max-w-3xl">
          <p className="font-display text-[clamp(2.75rem,7vw,5.5rem)] leading-[0.95] tracking-[-0.03em] text-white">
            {business.business_name}
          </p>

          <h1 className="mt-8 text-xl sm:text-2xl lg:text-3xl font-medium text-[color-mix(in_oklab,var(--trade-accent)_90%,white)] leading-snug max-w-2xl">
            {hero.headline}
          </h1>

          <p className="mt-5 text-base sm:text-lg text-slate-400 max-w-xl leading-relaxed">
            {hero.subheadline}
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-start gap-3">
            <a
              href={`tel:${business.phone}`}
              className="btn-trade inline-flex items-center gap-2.5 px-7 py-3.5 font-semibold rounded-md text-sm tracking-wide"
            >
              <Phone className="h-4 w-4" />
              {hero.cta_primary}
            </a>
            <a
              href="#services"
              className="btn-trade-outline px-7 py-3.5 font-medium rounded-md text-sm text-slate-200"
            >
              {hero.cta_secondary}
            </a>
          </div>

          <p className="mt-12 text-[0.65rem] uppercase tracking-[0.28em] text-slate-500">
            {business.city}, {business.state}
            {business.years_in_business
              ? ` · Serving since ${new Date().getFullYear() - business.years_in_business}`
              : null}
          </p>
        </div>
      </div>
    </section>
  );
}
