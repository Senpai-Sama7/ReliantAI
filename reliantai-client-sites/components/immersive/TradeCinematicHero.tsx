"use client";

import { useRef } from "react";
import { Phone } from "lucide-react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeScene } from "@/lib/immersive";
import { allowCinematicScroll } from "@/lib/immersive";
import TradeInstrument from "./TradeInstrument";
import MagneticCTA from "./MagneticCTA";

gsap.registerPlugin(ScrollTrigger, useGSAP);

interface TradeCinematicHeroProps {
  content: SiteContent;
  scene: TradeScene;
  light?: boolean;
  badge?: string;
}

/**
 * Brand-first cinematic stage.
 * Desktop: pin + scrub brand → promise → instrument.
 * Mobile: natural height, light entrance — never bottom-crammed.
 */
export default function TradeCinematicHero({
  content,
  scene,
  light = false,
  badge,
}: TradeCinematicHeroProps) {
  const root = useRef<HTMLElement>(null);
  const { business, hero } = content;

  const ink = light ? "text-[var(--trade-ink)]" : "text-white";
  const muted = light ? "text-stone-600" : "text-[var(--trade-muted)]";
  const headline = light
    ? "text-[var(--trade-primary)]"
    : "text-[color-mix(in_oklab,var(--trade-accent)_88%,white)]";

  useGSAP(
    () => {
      const el = root.current;
      if (!el) return;

      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (reduced) {
        gsap.set("[data-hero-line]", { opacity: 1, y: 0 });
        return;
      }

      // Entrance — phrase lines, never word-by-word spam
      gsap.fromTo(
        "[data-hero-line]",
        { opacity: 0, y: 28 },
        {
          opacity: 1,
          y: 0,
          duration: 0.85,
          stagger: 0.12,
          ease: "power3.out",
          delay: 0.05,
        },
      );

      const mm = gsap.matchMedia();
      mm.add("(min-width: 640px) and (prefers-reduced-motion: no-preference)", () => {
        if (!allowCinematicScroll()) return;

        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: el,
            start: "top top",
            end: "+=105%",
            pin: true,
            scrub: 0.85,
            invalidateOnRefresh: true,
          },
        });

        tl.to("[data-hero-brand]", { scale: 0.92, y: -18, ease: "none" }, 0)
          .to("[data-hero-copy]", { y: -36, opacity: 0.92, ease: "none" }, 0)
          .fromTo(
            "[data-hero-instrument]",
            { y: 40, opacity: 0.55, scale: 0.94 },
            { y: -12, opacity: 1, scale: 1, ease: "none" },
            0,
          );
      });
    },
    { scope: root },
  );

  return (
    <section
      ref={root}
      className={`immersive-stage relative overflow-hidden pt-[calc(var(--topbar-h)+0.5rem)] ${
        light ? "bg-[var(--trade-surface)]" : "bg-[var(--trade-ink)] atmosphere-grain"
      }`}
    >
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 70% 55% at 78% 18%, color-mix(in oklab, var(--trade-accent) 16%, transparent) 0%, transparent 70%)",
        }}
        aria-hidden
      />

      <div className="craft-container relative z-10 grid min-h-[85svh] items-center gap-10 py-12 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:gap-14 lg:py-16">
        <div data-hero-copy className="max-w-2xl">
          {badge ? (
            <p data-hero-line className="craft-eyebrow mb-4 sm:mb-5">
              {badge}
            </p>
          ) : null}

          <p data-hero-line data-hero-brand className={`craft-brand origin-left ${ink}`}>
            {business.business_name}
          </p>

          <h1 data-hero-line className={`craft-headline mt-6 sm:mt-8 max-w-xl ${headline}`}>
            {hero.headline}
          </h1>

          <p data-hero-line className={`craft-lead mt-4 sm:mt-5 ${muted}`}>
            {hero.subheadline}
          </p>

          <div
            data-hero-line
            className="mt-8 sm:mt-10 flex w-full max-w-md flex-col gap-3 sm:w-auto sm:max-w-none sm:flex-row sm:items-center"
          >
            <MagneticCTA href={`tel:${business.phone}`} className="btn-trade">
              <Phone className="h-4 w-4 shrink-0" aria-hidden />
              {hero.cta_primary}
            </MagneticCTA>
            <a
              href="#services"
              className={`btn-trade-outline ${light ? ink : "text-slate-200"}`}
            >
              {hero.cta_secondary}
            </a>
          </div>

          <p
            data-hero-line
            className={`mt-8 text-[0.6875rem] uppercase tracking-[0.16em] ${
              light ? "text-stone-500" : "text-slate-500"
            }`}
          >
            {business.city}, {business.state}
            {business.years_in_business
              ? ` · Since ${new Date().getFullYear() - business.years_in_business}`
              : null}
          </p>
        </div>

        <div
          data-hero-instrument
          className="hidden origin-center opacity-95 sm:block lg:translate-y-2"
        >
          <TradeInstrument scene={scene} progress={0.68} light={light} />
        </div>
      </div>
    </section>
  );
}
