"use client";

import { useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import type { SiteContent } from "@/types/SiteContent";
import { allowCinematicScroll } from "@/lib/immersive";

gsap.registerPlugin(ScrollTrigger, useGSAP);

interface CoverageRadiusMapProps {
  content: SiteContent;
  light?: boolean;
}

/**
 * Labelled service-area diagram — rings for city + area_served.
 * Explicitly schematic when coordinates are absent.
 */
export default function CoverageRadiusMap({ content, light = false }: CoverageRadiusMapProps) {
  const root = useRef<HTMLElement>(null);
  const { business, aeo_signals } = content;
  const areas = [
    business.city,
    ...(aeo_signals?.area_served || []).filter(
      (a) => a.toLowerCase() !== business.city.toLowerCase(),
    ),
  ].slice(0, 6);

  const title = light ? "text-[var(--trade-ink)]" : "text-white";
  const muted = light ? "text-stone-500" : "text-slate-400";
  const bg = light ? "bg-[var(--trade-elevated)]" : "bg-[var(--trade-surface)]";

  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

      const mm = gsap.matchMedia();
      mm.add("(min-width: 640px)", () => {
        if (!allowCinematicScroll()) return;
        gsap.fromTo(
          "[data-ring]",
          { opacity: 0, scale: 0.82 },
          {
            opacity: 1,
            scale: 1,
            stagger: 0.12,
            ease: "power2.out",
            scrollTrigger: {
              trigger: root.current,
              start: "top 70%",
              end: "center 45%",
              scrub: 0.7,
            },
          },
        );
      });

      mm.add("(max-width: 639px)", () => {
        gsap.fromTo(
          "[data-ring]",
          { opacity: 0, y: 16 },
          {
            opacity: 1,
            y: 0,
            stagger: 0.08,
            duration: 0.55,
            ease: "power3.out",
            scrollTrigger: { trigger: root.current, start: "top 85%", once: true },
          },
        );
      });
    },
    { scope: root },
  );

  return (
    <section ref={root} className={`relative overflow-hidden ${bg}`}>
      <div className="craft-container grid items-center gap-10 py-16 sm:py-20 lg:grid-cols-2 lg:py-24">
        <div>
          <p className="craft-eyebrow mb-3">Coverage</p>
          <h2 className={`craft-display ${title}`}>
            Service radius from {business.city}
          </h2>
          <p className={`mt-4 max-w-md text-sm leading-relaxed ${muted}`}>
            Schematic coverage diagram — not a survey map. Dispatch windows vary by crew load
            and weather.
          </p>
          <ul className="mt-8 space-y-2">
            {areas.map((area, i) => (
              <li key={area} className={`flex items-center gap-3 text-sm ${title}`}>
                <span className="font-display text-[var(--trade-accent)] tabular-nums">
                  {String(i + 1).padStart(2, "0")}
                </span>
                {area}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative mx-auto aspect-square w-full max-w-md">
          <svg viewBox="0 0 400 400" className="h-full w-full" aria-hidden>
            {[0.28, 0.48, 0.68, 0.88].map((scale, i) => (
              <circle
                key={scale}
                data-ring
                cx="200"
                cy="200"
                r={160 * scale}
                fill="none"
                stroke="var(--trade-accent)"
                strokeWidth={i === 0 ? 2 : 1}
                opacity={0.15 + i * 0.12}
              />
            ))}
            <circle cx="200" cy="200" r="8" fill="var(--trade-accent)" data-ring />
            {areas.slice(0, 4).map((area, i) => {
              const angle = -90 + i * 70;
              const rad = (angle * Math.PI) / 180;
              const r = 70 + i * 32;
              const x = 200 + Math.cos(rad) * r;
              const y = 200 + Math.sin(rad) * r;
              return (
                <g key={area} data-ring>
                  <circle cx={x} cy={y} r="4" fill="var(--trade-accent)" />
                  <text
                    x={x + 10}
                    y={y + 4}
                    fill={light ? "var(--trade-ink)" : "white"}
                    fontSize="11"
                    fontFamily="var(--font-sans), system-ui, sans-serif"
                    className="coverage-label"
                  >
                    {area}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    </section>
  );
}
