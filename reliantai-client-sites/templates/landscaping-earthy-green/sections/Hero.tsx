"use client";

import { Phone } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface HeroProps {
  content: SiteContent;
}

export default function Hero({ content }: HeroProps) {
  const { business, hero } = content;

  return (
    <section className="relative min-h-[85svh] flex items-end overflow-hidden bg-[var(--trade-ink)] atmosphere-grain pt-14">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 78% 60% at 80% 18%, color-mix(in oklab, var(--trade-primary) 19%, transparent) 0%, transparent 68%), radial-gradient(ellipse 44% 40% at 16% 76%, color-mix(in oklab, var(--trade-accent) 12%, transparent) 0%, transparent 72%)",
        }}
        aria-hidden
      />
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, currentColor 1px, transparent 0)",
          backgroundSize: "34px 34px",
          color: "var(--trade-accent)",
        }}
        aria-hidden
      />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 pt-28 lg:pb-28 lg:pt-36">
        <div className="max-w-3xl">
          <p className="font-display text-[clamp(2.8rem,7vw,5.65rem)] leading-[0.96] tracking-[-0.035em] text-white">
            {business.business_name}
          </p>
          <div className="mt-6 h-px w-28 bg-[var(--trade-accent)]" aria-hidden />

          <h1 className="mt-10 text-xl sm:text-2xl lg:text-3xl font-medium text-[color-mix(in_oklab,var(--trade-accent)_86%,white)] leading-snug max-w-2xl">
            {hero.headline}
          </h1>

          <p className="mt-6 text-base sm:text-lg text-slate-400 max-w-xl leading-relaxed">
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
              className="btn-trade-outline px-7 py-3.5 font-medium rounded-md text-sm text-slate-200"
            >
              {hero.cta_secondary}
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
