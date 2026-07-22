"use client";

import { useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import { allowCinematicScroll } from "@/lib/immersive";

gsap.registerPlugin(ScrollTrigger, useGSAP);

interface ServiceProcessReelProps {
  content: SiteContent;
  copy: TradeCopy;
  light?: boolean;
}

/**
 * Cinematic numbered service reel.
 * Desktop: horizontal pin scrub. Mobile: vertical stacked chapters.
 */
export default function ServiceProcessReel({
  content,
  copy,
  light = false,
}: ServiceProcessReelProps) {
  const root = useRef<HTMLElement>(null);
  const track = useRef<HTMLDivElement>(null);
  const { business, services } = content;

  const title = light ? "text-[var(--trade-ink)]" : "text-white";
  const muted = light ? "text-stone-600" : "text-[var(--trade-muted)]";
  const panel = light
    ? "bg-white border-stone-200"
    : "bg-[var(--trade-elevated)] border-white/10";
  const sectionBg = light ? "bg-[var(--trade-surface)]" : "bg-[var(--trade-ink)]";

  useGSAP(
    () => {
      const section = root.current;
      const reel = track.current;
      if (!section || !reel) return;

      const mm = gsap.matchMedia();

      mm.add("(min-width: 640px) and (prefers-reduced-motion: no-preference)", () => {
        if (!allowCinematicScroll()) return;

        const getTravel = () => Math.max(0, reel.scrollWidth - section.clientWidth + 64);

        const tween = gsap.to(reel, {
          x: () => -getTravel(),
          ease: "none",
          scrollTrigger: {
            trigger: section,
            start: "top top",
            end: () => `+=${getTravel() + window.innerHeight * 0.35}`,
            pin: true,
            scrub: 1,
            invalidateOnRefresh: true,
            anticipatePin: 1,
          },
        });

        const ro = new ResizeObserver(() => ScrollTrigger.refresh());
        ro.observe(reel);
        return () => {
          ro.disconnect();
          tween.scrollTrigger?.kill();
          tween.kill();
          gsap.set(reel, { clearProps: "transform" });
        };
      });

      mm.add("(max-width: 639px), (prefers-reduced-motion: reduce)", () => {
        gsap.set(reel, { clearProps: "transform" });
        ScrollTrigger.batch("[data-service-card]", {
          start: "top 90%",
          once: true,
          onEnter: (batch) =>
            gsap.fromTo(
              batch,
              { opacity: 0, y: 24 },
              { opacity: 1, y: 0, duration: 0.65, stagger: 0.1, ease: "power3.out" },
            ),
        });
      });
    },
    { scope: root },
  );

  return (
    <section ref={root} className={`immersive-pin relative overflow-hidden ${sectionBg}`}>
      <div className="craft-container relative pt-14 sm:pt-20 lg:pt-24">
        <div className="mb-10 max-w-2xl sm:mb-14">
          <p className="craft-eyebrow mb-3">Services</p>
          <h2 className={`craft-display ${title}`}>{copy.services_title}</h2>
          <p className={`mt-4 text-sm sm:text-base ${muted}`}>
            {copy.services_subtitle} {business.city}, {business.state}
          </p>
        </div>
      </div>

      <div className="immersive-track relative pb-16 sm:pb-24">
        <div
          ref={track}
          className="flex w-max flex-col gap-6 px-[var(--gutter)] sm:flex-row sm:gap-8 sm:will-change-transform"
        >
          {services.map((service, i) => {
            const dominant = i === 0;
            return (
              <article
                key={service.title}
                data-service-card
                className={`relative shrink-0 border ${panel} ${
                  dominant
                    ? "w-full sm:w-[min(34rem,72vw)] sm:min-h-[22rem]"
                    : "w-full sm:w-[min(26rem,58vw)] sm:min-h-[18rem]"
                } rounded-lg p-6 sm:p-8`}
              >
                <span
                  className={`font-display tabular-nums leading-none text-[color-mix(in_oklab,var(--trade-accent)_55%,transparent)] ${
                    dominant ? "text-7xl sm:text-8xl" : "text-6xl sm:text-7xl"
                  }`}
                  aria-hidden
                >
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3
                  className={`mt-4 font-display tracking-tight ${title} ${
                    dominant ? "text-3xl sm:text-4xl" : "text-2xl sm:text-3xl"
                  }`}
                >
                  {service.title}
                </h3>
                <p className={`mt-4 max-w-md text-sm leading-relaxed sm:text-base ${muted}`}>
                  {service.description}
                </p>
                <a
                  href={`tel:${business.phone}`}
                  className="mt-6 inline-flex text-sm font-semibold text-[var(--trade-accent)] underline-offset-4 hover:underline"
                >
                  {service.cta_text} →
                </a>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
