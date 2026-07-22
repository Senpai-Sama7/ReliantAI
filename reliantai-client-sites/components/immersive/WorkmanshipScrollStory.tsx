"use client";

import { useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import type { TradeScene } from "@/lib/immersive";
import { allowCinematicScroll } from "@/lib/immersive";
import TradeInstrument from "./TradeInstrument";

gsap.registerPlugin(ScrollTrigger, useGSAP);

interface WorkmanshipScrollStoryProps {
  content: SiteContent;
  copy: TradeCopy;
  scene: TradeScene;
  light?: boolean;
}

/** Chaptered about story with sticky instrument that advances per chapter. */
export default function WorkmanshipScrollStory({
  content,
  copy,
  scene,
  light = false,
}: WorkmanshipScrollStoryProps) {
  const root = useRef<HTMLElement>(null);
  const [progress, setProgress] = useState(0.4);
  const { business, about } = content;

  const title = light ? "text-[var(--trade-ink)]" : "text-white";
  const muted = light ? "text-stone-600" : "text-slate-300";
  const bg = light ? "bg-[var(--trade-surface)]" : "bg-[var(--trade-ink)]";

  const sentences = about.story.split(/\.\s+/).filter(Boolean);
  const chapters = [
    {
      label: "Origin",
      body: sentences[0] ? `${sentences[0]}.` : about.story,
    },
    {
      label: "Standard",
      body:
        (sentences.length > 1
          ? `${sentences.slice(1).join(". ")}.`
          : about.trust_points[0]) || copy.about_trust_title,
    },
    {
      label: "Proof",
      body: about.trust_points.slice(0, 3).join(" · ") || copy.about_trust_title,
    },
  ];

  useGSAP(
    () => {
      const el = root.current;
      if (!el) return;

      const mm = gsap.matchMedia();
      mm.add("(min-width: 640px) and (prefers-reduced-motion: no-preference)", () => {
        if (!allowCinematicScroll()) return;
        const chaptersEls = gsap.utils.toArray<HTMLElement>("[data-chapter]");
        chaptersEls.forEach((chapter, i) => {
          ScrollTrigger.create({
            trigger: chapter,
            start: "top 60%",
            end: "bottom 40%",
            onEnter: () => setProgress(0.35 + (i + 1) * 0.22),
            onEnterBack: () => setProgress(0.35 + (i + 1) * 0.22),
          });
          gsap.fromTo(
            chapter,
            { opacity: 0.35 },
            {
              opacity: 1,
              scrollTrigger: {
                trigger: chapter,
                start: "top 75%",
                end: "top 35%",
                scrub: 0.5,
              },
            },
          );
        });
      });
    },
    { scope: root },
  );

  return (
    <section ref={root} className={`relative ${bg}`}>
      <div className="craft-container grid gap-10 py-16 sm:py-20 lg:grid-cols-12 lg:gap-14 lg:py-28">
        <div className="lg:col-span-5">
          <div className="lg:sticky lg:top-24">
            <p className="craft-eyebrow mb-3">About</p>
            <h2 className={`craft-display mb-6 ${title}`}>{copy.about_title}</h2>
            {business.years_in_business ? (
              <p className="mb-8 text-[var(--trade-accent)]">
                Serving {business.city} for {business.years_in_business}+ years
              </p>
            ) : null}
            <div className="hidden sm:block">
              <TradeInstrument scene={scene} progress={progress} light={light} />
            </div>
          </div>
        </div>

        <div className="space-y-16 sm:space-y-24 lg:col-span-7">
          {chapters.map((chapter, i) => (
            <article key={chapter.label} data-chapter className="max-w-xl">
              <p className="craft-eyebrow mb-3">
                {String(i + 1).padStart(2, "0")} · {chapter.label}
              </p>
              <p className={`text-lg leading-relaxed sm:text-xl ${muted}`}>{chapter.body}</p>
            </article>
          ))}

          {about.certifications.length > 0 ? (
            <div className="flex flex-wrap gap-2 border-t border-[var(--trade-hairline)] pt-8">
              {about.certifications.map((cert) => (
                <span
                  key={cert}
                  className="rounded-md border border-[color-mix(in_oklab,var(--trade-accent)_35%,transparent)] px-3 py-1.5 text-xs text-[var(--trade-accent)]"
                >
                  {cert}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
