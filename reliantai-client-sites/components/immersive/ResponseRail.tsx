"use client";

import { useRef } from "react";
import { Phone } from "lucide-react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";

gsap.registerPlugin(ScrollTrigger, useGSAP);

interface ResponseRailProps {
  content: SiteContent;
  copy: TradeCopy;
  light?: boolean;
}

/** Dispatch timeline + conversion beat between services and story. */
export default function ResponseRail({ content, copy, light = false }: ResponseRailProps) {
  const root = useRef<HTMLElement>(null);
  const { business } = content;
  const title = light ? "text-[var(--trade-ink)]" : "text-white";
  const muted = light ? "text-stone-600" : "text-slate-400";
  const bg = light ? "bg-[var(--trade-elevated)]" : "bg-[var(--trade-surface)]";

  const steps = ["Call received", "Crew matched", "On-site window", "Work complete"];

  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      gsap.fromTo(
        "[data-rail-step]",
        { opacity: 0.25 },
        {
          opacity: 1,
          stagger: 0.15,
          ease: "none",
          scrollTrigger: {
            trigger: root.current,
            start: "top 80%",
            end: "bottom 55%",
            scrub: 0.6,
          },
        },
      );
      gsap.fromTo(
        "[data-rail-fill]",
        { scaleX: 0 },
        {
          scaleX: 1,
          ease: "none",
          scrollTrigger: {
            trigger: root.current,
            start: "top 75%",
            end: "center 45%",
            scrub: 0.6,
          },
        },
      );
    },
    { scope: root },
  );

  return (
    <section ref={root} className={`relative ${bg}`}>
      <div className="craft-container grid gap-8 py-12 sm:py-16 lg:grid-cols-12 lg:items-end">
        <div className="lg:col-span-5">
          <p className="craft-eyebrow mb-3">Dispatch</p>
          <h2 className={`craft-display text-[clamp(1.6rem,1.1rem+1.8vw,2.4rem)] ${title}`}>
            {copy.urgency_message}
          </h2>
          <a href={`tel:${business.phone}`} className="btn-trade mt-6 inline-flex max-w-xs">
            <Phone className="h-4 w-4" aria-hidden />
            {business.phone}
          </a>
        </div>

        <div className="lg:col-span-7">
          <div className="relative mb-6 h-px bg-[color-mix(in_oklab,var(--trade-accent)_25%,transparent)]">
            <div
              data-rail-fill
              className="absolute inset-y-0 left-0 origin-left bg-[var(--trade-accent)]"
              style={{ width: "100%" }}
            />
          </div>
          <ol className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {steps.map((step, i) => (
              <li key={step} data-rail-step className="min-w-0">
                <span className="font-display text-2xl text-[var(--trade-accent)] tabular-nums">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <p className={`mt-2 text-xs uppercase tracking-[0.12em] ${muted}`}>{step}</p>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
