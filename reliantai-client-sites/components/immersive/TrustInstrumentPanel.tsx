"use client";

import { useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";

gsap.registerPlugin(ScrollTrigger, useGSAP);

interface TrustInstrumentPanelProps {
  content: SiteContent;
  copy: TradeCopy;
  light?: boolean;
}

/**
 * Asymmetric proof composition — rating dial + ledger.
 * Replaces equal-card stats / trust chip strips.
 */
export default function TrustInstrumentPanel({
  content,
  copy,
  light = false,
}: TrustInstrumentPanelProps) {
  const root = useRef<HTMLElement>(null);
  const { business, about } = content;
  const rating = business.google_rating || 0;
  const reviews = business.review_count || 0;
  const years = business.years_in_business;
  const circumference = 2 * Math.PI * 54;
  const ratingArc = (Math.min(rating, 5) / 5) * circumference;

  const title = light ? "text-[var(--trade-ink)]" : "text-white";
  const muted = light ? "text-stone-500" : "text-slate-400";
  const surface = light ? "bg-[var(--trade-elevated)]" : "bg-[var(--trade-surface)]";
  const rule = light ? "border-stone-200" : "border-white/8";

  useGSAP(
    () => {
      const el = root.current;
      if (!el) return;
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

      ScrollTrigger.batch("[data-proof]", {
        start: "top 88%",
        once: true,
        onEnter: (batch) =>
          gsap.fromTo(
            batch,
            { opacity: 0, y: 22 },
            {
              opacity: 1,
              y: 0,
              duration: 0.7,
              stagger: 0.08,
              ease: "power3.out",
              overwrite: true,
            },
          ),
      });

      gsap.fromTo(
        "[data-rating-arc]",
        { strokeDashoffset: circumference },
        {
          strokeDashoffset: circumference - ratingArc,
          duration: 1.2,
          ease: "power2.out",
          scrollTrigger: {
            trigger: el,
            start: "top 75%",
            once: true,
          },
        },
      );
    },
    { scope: root, dependencies: [ratingArc, circumference] },
  );

  return (
    <section ref={root} className={`relative border-y ${rule} ${surface}`}>
      <div className="craft-container grid gap-10 py-12 sm:py-16 lg:grid-cols-12 lg:gap-12 lg:py-20">
        <div data-proof className="lg:col-span-4">
          <p className="craft-eyebrow mb-4">Verified locally</p>
          <div className="relative mx-auto w-40 sm:mx-0">
            <svg viewBox="0 0 140 140" className="h-40 w-40 -rotate-90">
              <circle
                cx="70"
                cy="70"
                r="54"
                fill="none"
                stroke="color-mix(in oklab, var(--trade-accent) 22%, transparent)"
                strokeWidth="8"
              />
              <circle
                data-rating-arc
                cx="70"
                cy="70"
                r="54"
                fill="none"
                stroke="var(--trade-accent)"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={circumference - ratingArc}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center rotate-0">
              <span className={`font-display text-4xl tabular-nums ${title}`}>
                {rating ? rating.toFixed(1) : "—"}
              </span>
              <span className={`text-[0.65rem] uppercase tracking-[0.16em] ${muted}`}>
                Google
              </span>
            </div>
          </div>
          {reviews > 0 ? (
            <p className={`mt-4 text-sm ${muted}`}>
              {reviews} published reviews · {business.city}
            </p>
          ) : null}
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:col-span-8 lg:gap-8">
          {years ? (
            <div data-proof className={`border-l-2 border-[var(--trade-accent)] pl-5`}>
              <p className={`font-display text-5xl tabular-nums tracking-tight ${title}`}>
                {years}+
              </p>
              <p className={`mt-2 text-xs uppercase tracking-[0.14em] ${muted}`}>
                Years serving {business.city}
              </p>
            </div>
          ) : null}

          <div data-proof>
            <p className={`mb-3 text-sm font-medium ${title}`}>{copy.about_trust_title}</p>
            <ul className="space-y-2.5">
              {(about.trust_points.length ? about.trust_points : copy.trust_badges)
                .slice(0, 4)
                .map((point) => (
                  <li key={point} className={`text-sm leading-relaxed ${muted}`}>
                    <span className="mr-2 text-[var(--trade-accent)]">▸</span>
                    {point}
                  </li>
                ))}
            </ul>
          </div>

          {about.certifications.length > 0 ? (
            <div data-proof className="sm:col-span-2">
              <p className={`mb-3 text-[0.65rem] uppercase tracking-[0.16em] ${muted}`}>
                Credentials on file
              </p>
              <div className="flex flex-wrap gap-2">
                {about.certifications.map((cert) => (
                  <span
                    key={cert}
                    className="rounded-md border border-[color-mix(in_oklab,var(--trade-accent)_35%,transparent)] px-3 py-1.5 text-xs font-medium text-[var(--trade-accent)]"
                  >
                    {cert}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
