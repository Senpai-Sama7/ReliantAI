import { Star } from "lucide-react";
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
          className={`h-4 w-4 ${
            i < rating ? "fill-amber-400 text-amber-400" : "text-slate-600"
          }`}
        />
      ))}
    </div>
  );
}

export default function Reviews({ content }: ReviewsProps) {
  const { business, reviews } = content;
  const copy = TRADE_COPY[content.site_config.trade] || TRADE_COPY.electrical;

  return (
    <section id="reviews" className="py-24 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-white font-display">
            {copy.reviews_title}
          </h2>
          <div className="mt-3 flex items-center justify-center gap-2">
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
              className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 hover:shadow-lg hover:shadow-amber-900/20 hover:-translate-y-0.5 transition-all duration-200"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-amber-900 flex items-center justify-center text-amber-300 font-semibold text-sm">
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

        <div className="mt-8 text-center">
          <p className="text-slate-500 text-xs">
            {reviews.aggregate_line}
          </p>
        </div>
      </div>
    </section>
  );
}
