"use client";

import { Star, Quote } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import ScrollReveal from "@/components/shared/ScrollReveal";

interface CraftReviewsProps {
  content: SiteContent;
  copy: TradeCopy;
  light?: boolean;
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5" aria-label={`${rating} out of 5 stars`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={`h-3.5 w-3.5 ${
            i < rating ? "fill-amber-400 text-amber-400" : "text-slate-600"
          }`}
        />
      ))}
    </div>
  );
}

export default function CraftReviews({ content, copy, light = false }: CraftReviewsProps) {
  const { business, reviews } = content;
  const title = light ? "text-[var(--trade-ink)]" : "text-white";
  const body = light ? "text-stone-600" : "text-slate-300";
  const card = light
    ? "bg-white border-stone-200"
    : "bg-[var(--trade-elevated)] border-white/10";
  const sectionBg = light ? "bg-[var(--trade-elevated)]" : "bg-[var(--trade-surface)]";

  return (
    <section className={`relative craft-section ${sectionBg}`}>
      <div className="craft-container relative">
        <ScrollReveal className="mb-10 sm:mb-14 max-w-2xl">
          <p className="craft-eyebrow mb-3">Proof</p>
          <h2 className={`craft-display ${title}`}>{copy.reviews_title}</h2>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <StarRating rating={Math.round(business.google_rating)} />
            <span className={`text-sm ${light ? "text-stone-500" : "text-slate-400"}`}>
              {business.google_rating} ({business.review_count} reviews)
            </span>
          </div>
        </ScrollReveal>

        <div className="columns-1 sm:columns-2 gap-5 space-y-5 lg:[column-count:3]">
          {reviews.reviews.map((review, i) => (
            <ScrollReveal
              key={i}
              delayMs={Math.min(i * 40, 160)}
              className={`break-inside-avoid border rounded-lg p-5 sm:p-6 relative mb-5 ${card}`}
            >
              <Quote
                className="absolute top-4 right-4 h-7 w-7 text-[var(--trade-accent)]/15 fill-current"
                aria-hidden
              />
              <StarRating rating={review.rating} />
              <p className={`mt-3 text-sm leading-relaxed ${body}`}>
                &ldquo;{review.text}&rdquo;
              </p>
              <div
                className={`mt-4 pt-3 border-t flex items-center gap-3 ${
                  light ? "border-stone-100" : "border-white/10"
                }`}
              >
                <div className="w-8 h-8 rounded-full bg-[color-mix(in_oklab,var(--trade-primary)_35%,transparent)] flex items-center justify-center text-[var(--trade-accent)] font-semibold text-xs shrink-0">
                  {review.author.charAt(0)}
                </div>
                <div className="min-w-0 flex items-baseline gap-2">
                  <p className={`text-sm font-medium truncate ${title}`}>{review.author}</p>
                  <p className="text-xs text-slate-500 shrink-0">{review.time}</p>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>

        {reviews.aggregate_line ? (
          <p className="mt-8 text-xs text-slate-500">{reviews.aggregate_line}</p>
        ) : null}
      </div>
    </section>
  );
}
