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
              className="bg-slate-800/50 border border-slate-700/80 rounded-xl p-6 shadow-sm hover:shadow-lg hover:border-slate-600 transition-all duration-300"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-emerald-900 flex items-center justify-center text-emerald-300 font-semibold text-sm">
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
