import { Star, Quote } from "lucide-react";
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
    <section className="relative py-24 bg-slate-900">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] rounded-full bg-blue-600/3 blur-3xl" />
      </div>
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
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
              className="break-inside-avoid bg-slate-800/50 border border-slate-700 rounded-xl p-6 shadow-sm hover:border-slate-600 transition-colors duration-300 relative"
            >
              <Quote className="absolute top-4 right-4 h-8 w-8 text-blue-500/10 fill-current" />
              <StarRating rating={review.rating} />
              <p className="mt-3 text-slate-300 text-sm leading-relaxed">
                &ldquo;{review.text}&rdquo;
              </p>
              <div className="mt-4 pt-3 border-t border-slate-700/50 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-900/60 flex items-center justify-center text-blue-300 font-semibold text-xs">
                  {review.author.charAt(0)}
                </div>
                <div className="flex items-baseline gap-2">
                  <p className="text-white text-sm font-medium">
                    {review.author}
                  </p>
                  <p className="text-slate-600 text-xs">{review.time}</p>
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