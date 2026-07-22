import { Star, Quote } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import ScrollReveal from "@/components/shared/ScrollReveal";

interface ReviewsProps {
  content: SiteContent;
  copy: TradeCopy;
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={`h-3.5 w-3.5 ${
            i < rating ? "fill-amber-400 text-amber-400" : "text-slate-700"
          }`}
        />
      ))}
    </div>
  );
}

export default function Reviews({ content, copy }: ReviewsProps) {
  const { business, reviews } = content;

  return (
    <section className="relative py-24 bg-[var(--trade-surface)]">
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
        <ScrollReveal className="mb-14 max-w-2xl">
          <p className="text-[0.65rem] uppercase tracking-[0.28em] text-[var(--trade-accent)] mb-4">
            Proof
          </p>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl text-white font-display tracking-tight leading-[1.1]">
            {copy.reviews_title}
          </h2>
          <div className="mt-4 flex items-center gap-2">
            <StarRating rating={Math.round(business.google_rating)} />
            <span className="text-slate-400 text-sm">
              {business.google_rating} ({business.review_count} reviews on Google)
            </span>
          </div>
        </ScrollReveal>

        <div className="columns-1 md:columns-2 gap-6 space-y-6 lg:[column-count:3]">
          {reviews.reviews.map((review, i) => (
            <ScrollReveal
              key={i}
              delayMs={i * 40}
              className="break-inside-avoid bg-[var(--trade-elevated)] border border-white/10 rounded-lg p-6 relative mb-6"
            >
              <Quote className="absolute top-4 right-4 h-8 w-8 text-[var(--trade-accent)]/15 fill-current" />
              <StarRating rating={review.rating} />
              <p className="mt-3 text-slate-300 text-sm leading-relaxed">
                &ldquo;{review.text}&rdquo;
              </p>
              <div className="mt-4 pt-3 border-t border-white/10 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-[color-mix(in_oklab,var(--trade-primary)_40%,transparent)] flex items-center justify-center text-[var(--trade-accent)] font-semibold text-xs">
                  {review.author.charAt(0)}
                </div>
                <div className="flex items-baseline gap-2">
                  <p className="text-white text-sm font-medium">{review.author}</p>
                  <p className="text-slate-600 text-xs">{review.time}</p>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>

        <p className="mt-8 text-slate-500 text-xs">{reviews.aggregate_line}</p>
      </div>
    </section>
  );
}
