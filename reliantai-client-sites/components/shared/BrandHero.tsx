"use client";

import { Phone } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

export type HeroSignature =
  | "steel-grid" // HVAC — soft grid + radial
  | "copper-rule" // Plumbing — copper hairline + 24/7
  | "gold-rule" // Electrical — left gold rule
  | "copper-bold" // Roofing — thick rule under brand
  | "gallery" // Painting — light gallery
  | "moss-organic"; // Landscaping — clay hairline

interface BrandHeroProps {
  content: SiteContent;
  signature?: HeroSignature;
  light?: boolean;
  badge?: string;
}

/**
 * Mobile-first brand hero.
 * Phone: natural height, top-aligned composition (never bottom-crammed).
 * Desktop: taller stage with breathing room.
 */
export default function BrandHero({
  content,
  signature = "steel-grid",
  light = false,
  badge,
}: BrandHeroProps) {
  const { business, hero } = content;
  const ink = light ? "text-[var(--trade-ink)]" : "text-white";
  const muted = light ? "text-stone-600" : "text-[var(--trade-muted)]";
  const headlineColor = light
    ? "text-[var(--trade-primary)]"
    : "text-[color-mix(in_oklab,var(--trade-accent)_88%,white)]";

  const radialPos =
    signature === "copper-rule"
      ? "18% 22%"
      : signature === "moss-organic"
        ? "72% 28%"
        : "82% 18%";

  return (
    <section
      className={`relative flex flex-col justify-start overflow-hidden pt-[calc(var(--topbar-h)+0.75rem)] sm:justify-center ${
        light ? "bg-[var(--trade-surface)]" : "bg-[var(--trade-ink)] atmosphere-grain"
      } min-h-0 sm:min-h-[72svh] lg:min-h-[82svh]`}
    >
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `radial-gradient(ellipse 75% 55% at ${radialPos}, color-mix(in oklab, var(--trade-accent) 14%, transparent) 0%, transparent 68%)`,
        }}
        aria-hidden
      />

      {(signature === "steel-grid" || signature === "copper-rule") && (
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.035] hidden sm:block"
          style={{
            backgroundImage:
              "linear-gradient(to right, currentColor 1px, transparent 1px), linear-gradient(to bottom, currentColor 1px, transparent 1px)",
            backgroundSize: "72px 72px",
            color: "var(--trade-accent)",
          }}
          aria-hidden
        />
      )}

      {signature === "gold-rule" && (
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.03] hidden sm:block"
          style={{
            backgroundImage: "linear-gradient(135deg, currentColor 1px, transparent 1px)",
            backgroundSize: "54px 54px",
            color: "var(--trade-accent)",
          }}
          aria-hidden
        />
      )}

      {signature === "gallery" && (
        <div
          className="absolute inset-x-0 top-[calc(var(--topbar-h)+1.25rem)] h-px bg-[color-mix(in_oklab,var(--trade-accent)_22%,transparent)]"
          aria-hidden
        />
      )}

      <div className="craft-container relative z-10 w-full py-10 sm:py-16 lg:py-24">
        <div
          className={`max-w-3xl ${
            signature === "gold-rule"
              ? "border-l-2 border-[var(--trade-accent)] pl-5 sm:pl-8"
              : ""
          }`}
        >
          {(badge || signature === "copper-rule") && (
            <p className="craft-eyebrow mb-4 sm:mb-5">
              {badge || "24/7 Emergency"}
            </p>
          )}

          <p className={`craft-brand ${ink}`}>{business.business_name}</p>

          {(signature === "copper-rule" ||
            signature === "copper-bold" ||
            signature === "moss-organic") && (
            <div
              className={`mt-5 sm:mt-6 h-0.5 bg-[var(--trade-accent)] ${
                signature === "copper-bold" ? "w-16 sm:w-28" : "w-12 sm:w-20"
              }`}
              aria-hidden
            />
          )}

          <h1 className={`craft-headline mt-6 sm:mt-8 ${headlineColor} max-w-2xl`}>
            {hero.headline}
          </h1>

          <p className={`craft-lead mt-4 sm:mt-5 ${muted}`}>{hero.subheadline}</p>

          <div className="mt-8 sm:mt-10 flex flex-col sm:flex-row sm:items-center gap-3 w-full sm:w-auto max-w-md sm:max-w-none">
            <a href={`tel:${business.phone}`} className="btn-trade">
              <Phone className="h-4 w-4 shrink-0" aria-hidden />
              {hero.cta_primary}
            </a>
            <a
              href="#services"
              className={`btn-trade-outline ${light ? ink : "text-slate-200"}`}
            >
              {hero.cta_secondary}
            </a>
          </div>

          <p
            className={`mt-8 sm:mt-10 text-[0.6875rem] uppercase tracking-[0.16em] ${
              light ? "text-stone-500" : "text-slate-500"
            }`}
          >
            {business.city}, {business.state}
            {business.years_in_business
              ? ` · Since ${new Date().getFullYear() - business.years_in_business}`
              : null}
          </p>
        </div>
      </div>
    </section>
  );
}
