import { Star } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface TradeCopy {
  services_title: string;
  services_subtitle: string;
  about_title: string;
  about_trust_title: string;
  reviews_title: string;
  faq_title: string;
  urgency_message: string;
  estimate_heading: string;
  estimate_subtext: string;
  trust_badges: string[];
  stats: { label: string; value_key: string; suffix: string; fallback: string }[];
}

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
          className={`h-4 w-4 ${
            i < rating ? "fill-yellow-400 text-yellow-400" : "text-slate-600"
          }`}
        />
      ))}
    </div>
  );
}

export default function Reviews({ content, copy }: ReviewsProps) {
  const { business, reviews } = content;

  return (
    <section className="py-24 bg-slate-900">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-white font-display">
            {copy.reviews_title}
          </h2>
          <div className="mt-3 flex items-center justify-center gap-2">
            <StarRating rating={Math.round(business.google_rating)} />
            <span className="text-slate-400 text-sm">
              {business.google_rating} ({business.review_count} reviews on Google)
            </span>
          </div>
        </div>

        <div className="columns-1 md:columns-2 lg:columns-3 gap-6 space-y-6">
          {reviews.reviews.map((review, i) => (
            <div
              key={i}
              className="break-inside-avoid bg-slate-800/50 border border-slate-700/80 rounded-xl p-6 shadow-sm hover:shadow-lg hover:border-slate-600 transition-all duration-300"
            >
              <span className="block text-5xl leading-none text-emerald-500/30 font-serif select-none" aria-hidden="true">
                "
              </span>
              <p className="text-slate-300 text-sm leading-relaxed -mt-3 line-clamp-5">
                {review.text}
              </p>
              <div className="mt-4 pt-4 border-t border-slate-700/50 flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-emerald-900 flex items-center justify-center text-emerald-300 font-semibold text-xs">
                  {review.author.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium truncate">
                    {review.author}
                  </p>
                  <div className="flex items-center gap-2">
                    <StarRating rating={review.rating} />
                    <span className="text-slate-500 text-xs">{review.time}</span>
                  </div>
                </div>
              </div>
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