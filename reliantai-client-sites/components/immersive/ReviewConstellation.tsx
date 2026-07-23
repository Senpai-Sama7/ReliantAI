"use client";

import { useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";

gsap.registerPlugin(ScrollTrigger, useGSAP);

interface ReviewConstellationProps {
  content: SiteContent;
  copy: TradeCopy;
  light?: boolean;
}

/** Rating center + irregular, keyboard-focusable review nodes. */
export default function ReviewConstellation({
  content,
  copy,
  light = false,
}: ReviewConstellationProps) {
  const root = useRef<HTMLElement>(null);
  const { business, reviews } = content;
  const list = reviews.reviews.slice(0, 6);
  const [active, setActive] = useState(0);

  const title = light ? "text-[var(--trade-ink)]" : "text-white";
  const muted = light ? "text-stone-600" : "text-slate-300";
  const bg = light ? "bg-[var(--trade-surface)]" : "bg-[var(--trade-ink)]";
  const nodeBg = light
    ? "bg-white border-stone-200"
    : "bg-[var(--trade-elevated)] border-white/10";

  // Deterministic irregular layout (no random on SSR)
  const positions = [
    { x: "8%", y: "12%", w: "sm:w-[16rem]" },
    { x: "58%", y: "6%", w: "sm:w-[18rem]" },
    { x: "28%", y: "38%", w: "sm:w-[20rem]" },
    { x: "68%", y: "42%", w: "sm:w-[15rem]" },
    { x: "12%", y: "68%", w: "sm:w-[17rem]" },
    { x: "52%", y: "72%", w: "sm:w-[19rem]" },
  ];

  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      ScrollTrigger.batch("[data-review-node]", {
        start: "top 92%",
        once: true,
        onEnter: (batch) =>
          gsap.fromTo(
            batch,
            { opacity: 0, scale: 0.94, y: 18 },
            {
              opacity: 1,
              scale: 1,
              y: 0,
              duration: 0.65,
              stagger: 0.07,
              ease: "power3.out",
            },
          ),
      });
    },
    { scope: root },
  );

  return (
    <section ref={root} className={`relative overflow-hidden ${bg}`}>
      <div className="craft-container py-16 sm:py-20 lg:py-28">
        <div className="mb-10 max-w-xl sm:mb-14">
          <p className="craft-eyebrow mb-3">Proof</p>
          <h2 className={`craft-display ${title}`}>{copy.reviews_title}</h2>
          <p className={`mt-4 text-sm ${muted}`}>
            {business.google_rating.toFixed(1)}★ · {business.review_count} Google reviews
          </p>
        </div>

        {/* Mobile: vertical stack */}
        <div className="space-y-4 sm:hidden">
          {list.map((review, i) => (
            <button
              key={review.author + i}
              type="button"
              data-review-node
              onClick={() => setActive(i)}
              className={`review-node w-full rounded-lg border p-5 text-left ${nodeBg} ${
                active === i ? "ring-1 ring-[var(--trade-accent)]" : ""
              }`}
            >
              <p className={`text-sm leading-relaxed ${muted}`}>&ldquo;{review.text}&rdquo;</p>
              <p className={`mt-3 text-sm font-medium ${title}`}>
                {review.author} · {review.rating}★
              </p>
            </button>
          ))}
        </div>

        {/* Desktop: constellation */}
        <div className="relative hidden min-h-[34rem] sm:block">
          <div className="pointer-events-none absolute left-1/2 top-1/2 z-0 flex h-36 w-36 -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-full border border-[color-mix(in_oklab,var(--trade-accent)_40%,transparent)]">
            <span className={`font-display text-4xl tabular-nums ${title}`}>
              {business.google_rating.toFixed(1)}
            </span>
            <span className={`text-[0.65rem] uppercase tracking-[0.16em] ${muted}`}>
              Aggregate
            </span>
          </div>

          {list.map((review, i) => {
            const pos = positions[i] || positions[0];
            return (
              <button
                key={review.author + i}
                type="button"
                data-review-node
                onClick={() => setActive(i)}
                onFocus={() => setActive(i)}
                style={{ left: pos.x, top: pos.y }}
                className={`review-node absolute z-10 rounded-lg border p-4 text-left transition-[opacity,transform,box-shadow] duration-200 ${pos.w} ${nodeBg} ${
                  active === i
                    ? "z-20 scale-[1.02] shadow-[0_12px_40px_rgba(0,0,0,0.25)] ring-1 ring-[var(--trade-accent)]"
                    : "opacity-80 hover:opacity-100"
                }`}
              >
                <p className={`line-clamp-4 text-sm leading-relaxed ${muted}`}>
                  &ldquo;{review.text}&rdquo;
                </p>
                <p className={`mt-3 text-xs font-medium ${title}`}>
                  {review.author} · {review.rating}★ · {review.time}
                </p>
              </button>
            );
          })}
        </div>

        {reviews.aggregate_line ? (
          <p className={`mt-8 text-xs ${muted}`}>{reviews.aggregate_line}</p>
        ) : null}
      </div>
    </section>
  );
}
