"use client";

import { Phone } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

export default function Hero({ content }: { content: SiteContent }) {
  const { business, hero } = content;

  return (
    <section className="relative min-h-[85svh] flex items-end overflow-hidden bg-[var(--trade-ink)] atmosphere-grain pt-14">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 72% 58% at 78% 18%, color-mix(in oklab, var(--trade-accent) 17%, transparent) 0%, transparent 68%)",
        }}
        aria-hidden
      />

      <div
        className="absolute inset-0 pointer-events-none opacity-[0.04]"
        style={{
          backgroundImage:
            "linear-gradient(to bottom, currentColor 1px, transparent 1px)",
          backgroundSize: "100% 64px",
          color: "var(--trade-accent)",
        }}
        aria-hidden
      />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16 pt-24 lg:pb-24 lg:pt-32">
        <div className="max-w-4xl">
          <p className="font-display text-[clamp(3.25rem,8.6vw,6.6rem)] leading-[0.9] tracking-[-0.045em] text-white">
            {business.business_name}
          </p>
          <div className="mt-6 h-1.5 w-36 bg-[var(--trade-accent)]" aria-hidden />

          <h1 className="mt-8 text-xl sm:text-2xl lg:text-3xl font-medium text-[color-mix(in_oklab,var(--trade-accent)_88%,white)] leading-snug max-w-2xl">
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
