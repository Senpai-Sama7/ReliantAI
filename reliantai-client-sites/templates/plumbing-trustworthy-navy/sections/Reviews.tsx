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
              {business.google_rating} ({business.review_count} reviews on
              Google)
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {reviews.reviews.map((review, i) => (
            <div
              key={i}
              className="bg-slate-800/40 border border-slate-700/60 rounded-2xl p-6 hover:-translate-y-1.5 hover:shadow-xl hover:shadow-blue-900/10 hover:border-blue-500/20 transition-all duration-300"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-blue-900/50 flex items-center justify-center text-blue-300 font-semibold text-sm flex-shrink-0">
                  {review.author.charAt(0)}
                </div>
                <div>
                  <p className="text-white text-sm font-medium">
                    {review.author}
                  </p>
                  <p className="text-slate-500 text-xs">{review.time}</p>
                </div>
              </div>
              <StarRating rating={review.rating} />
              <p className="mt-3 text-slate-400 text-sm leading-relaxed line-clamp-4">
                &ldquo;{review.text}&rdquo;
              </p>
            </div>
          ))}
        </div>

        <div className="mt-10 text-center">
          <p className="text-slate-500 text-xs">
            {reviews.aggregate_line}
          </p>
        </div>
      </div>
    </section>
  );
}
