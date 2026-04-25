import { Star, Quote } from "lucide-react";
import { TRADE_COPY } from "@/lib/trade-copy";
import type { SiteContent } from "@/types/SiteContent";

interface ReviewsProps {
  content: SiteContent;
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={`h-4 w-4 ${i < rating ? "fill-amber-400 text-amber-400" : "text-slate-600"}`}
        />
      ))}
    </div>
  );
}

export default function Reviews({ content }: ReviewsProps) {
  const { business, reviews } = content;
  const copy = TRADE_COPY[content.site_config.trade] || TRADE_COPY.electrical;

  return (
    <section id="reviews" className="bg-slate-950 py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="mb-14 text-center">
          <h2 className="font-display text-3xl font-bold text-white sm:text-4xl">
            {copy.reviews_title}
          </h2>
          <div className="mt-3 flex items-center justify-center gap-2">
            <StarRating rating={Math.round(business.google_rating)} />
            <span className="text-sm text-slate-400">
              {business.google_rating} ({business.review_count} reviews on Google)
            </span>
          </div>
        </div>

        <div className="columns-1 gap-6 md:columns-2 lg:columns-3">
          {reviews.reviews.map((review, i) => (
            <div
              key={i}
              className="mb-6 break-inside-avoid rounded-xl border border-slate-800 bg-slate-900/50 p-6 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-amber-900/20"
            >
              <Quote className="mb-2 h-5 w-5 text-amber-500/30" />
              <StarRating rating={review.rating} />
              <p className="mt-3 text-sm leading-relaxed text-slate-300 line-clamp-5">
                &ldquo;{review.text}&rdquo;
              </p>
              <div className="mt-4 flex items-center gap-3 border-t border-slate-800 pt-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-amber-900 text-sm font-semibold text-amber-300">
                  {review.author.charAt(0)}
                </div>
                <div>
                  <p className="text-sm font-medium text-white">{review.author}</p>
                  <p className="text-xs text-slate-500">{review.time}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <p className="mt-4 text-center text-xs text-slate-500">{reviews.aggregate_line}</p>
      </div>
    </section>
  );
}