import { Star } from "lucide-react";
import { TRADE_COPY } from "@/lib/trade-copy";
import type { SiteContent } from "@/types/SiteContent";

interface ReviewsProps {
  content: SiteContent;
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: 5 }).map((_, i) =>
        i < rating ? (
          <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
        ) : (
          <Star key={i} className="h-4 w-4 text-slate-600" />
        )
      )}
    </div>
  );
}

export default function Reviews({ content }: ReviewsProps) {
  const { business, reviews } = content;
  const copy = TRADE_COPY[content.site_config.trade as keyof typeof TRADE_COPY] ?? TRADE_COPY.plumbing;
  const featured = reviews.reviews[0];
  const rest = reviews.reviews.slice(1);

  return (
    <section id="reviews" className="py-24 bg-slate-900/95">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white font-display">
            {copy.reviews_title}
          </h2>
          <div className="mt-4 flex items-center justify-center gap-2">
            <StarRating rating={Math.round(business.google_rating)} />
            <span className="text-slate-400 text-sm">
              {business.google_rating} ({business.review_count} reviews on Google)
            </span>
          </div>
        </div>

        {featured && (
          <div className="bg-[var(--trade-surface)] border border-[color-mix(in_oklab,var(--trade-accent)_24%,transparent)] rounded-2xl p-8 md:p-10 relative hover:border-[color-mix(in_oklab,var(--trade-accent)_42%,transparent)] transition-colors duration-300">
            <span className="absolute top-3 left-6 text-6xl text-[color-mix(in_oklab,var(--trade-accent)_18%,transparent)] font-serif leading-none select-none pointer-events-none">
              &ldquo;
            </span>
            <div className="relative flex flex-col md:flex-row md:items-start gap-6">
              <div className="flex items-center gap-3 md:flex-col md:items-start md:w-40 flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-[color-mix(in_oklab,var(--trade-accent)_14%,transparent)] flex items-center justify-center text-[var(--trade-accent)] font-semibold text-base">
                  {featured.author.charAt(0)}
                </div>
                <div>
                  <p className="text-white font-medium">{featured.author}</p>
                  <p className="text-slate-500 text-xs">{featured.time}</p>
                </div>
              </div>
              <div className="flex-1">
                <StarRating rating={featured.rating} />
                <p className="mt-3 text-slate-300 leading-relaxed">
                  {featured.text}
                </p>
              </div>
            </div>
          </div>
        )}

        {rest.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            {rest.map((review, i) => (
              <div
                key={i}
                className="relative bg-slate-800/40 border border-slate-700/60 rounded-2xl p-6 hover:-translate-y-1.5 hover:border-[color-mix(in_oklab,var(--trade-accent)_42%,transparent)] transition-[transform,border-color] duration-300"
              >
                <span className="absolute top-2 left-4 text-5xl text-[color-mix(in_oklab,var(--trade-accent)_18%,transparent)] font-serif leading-none select-none pointer-events-none">
                  &ldquo;
                </span>
                <div className="relative">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-full bg-[color-mix(in_oklab,var(--trade-accent)_14%,transparent)] flex items-center justify-center text-[var(--trade-accent)] font-semibold text-sm flex-shrink-0">
                      {review.author.charAt(0)}
                    </div>
                    <div>
                      <p className="text-white text-sm font-medium">{review.author}</p>
                      <p className="text-slate-500 text-xs">{review.time}</p>
                    </div>
                  </div>
                  <StarRating rating={review.rating} />
                  <p className="mt-3 text-slate-400 text-sm leading-relaxed line-clamp-4">
                    {review.text}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-10 text-center">
          <p className="text-slate-500 text-xs">{reviews.aggregate_line}</p>
        </div>
      </div>
    </section>
  );
}