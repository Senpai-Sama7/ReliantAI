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
            "radial-gradient(ellipse 62% 52% at 82% 24%, color-mix(in oklab, var(--trade-accent) 16%, transparent) 0%, transparent 66%)",
        }}
        aria-hidden
      />
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.035]"
        style={{
          backgroundImage:
            "linear-gradient(135deg, currentColor 1px, transparent 1px)",
          backgroundSize: "54px 54px",
          color: "var(--trade-accent)",
        }}
        aria-hidden
      />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16 pt-24 lg:pb-24 lg:pt-32">
        <div className="max-w-3xl border-l-2 border-[var(--trade-accent)] pl-6 sm:pl-8">
          <p className="font-display text-[clamp(2.7rem,6.8vw,5.35rem)] leading-[0.94] tracking-[-0.055em] text-white">
            {business.business_name}
          </p>

          <h1 className="mt-8 text-xl sm:text-2xl lg:text-3xl font-medium text-[color-mix(in_oklab,var(--trade-accent)_92%,white)] leading-snug max-w-2xl">
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
        </div>
      </div>
    </section>
  );
}
