import { Star } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface ReviewsProps {
  content: SiteContent;
  copy: {
    reviews_title: string;
  };
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={`h-4 w-4 ${
            i < rating ? "fill-yellow-400 text-yellow-400" : "text-stone-300"
          }`}
        />
      ))}
    </div>
  );
}

export default function Reviews({ content, copy }: ReviewsProps) {
  const { business, reviews } = content;

  return (
    <section className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 font-display tracking-tight">
            {copy.reviews_title}
          </h2>
          <div className="mt-3 flex items-center justify-center gap-2">
            <StarRating rating={Math.round(business.google_rating)} />
            <span className="text-slate-500 text-sm">
              {business.google_rating} ({business.review_count} reviews on
              Google)
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {reviews.reviews.map((review, i) => (
            <div
              key={i}
              className="bg-white border border-stone-200 rounded-xl p-6 hover:shadow-lg hover:border-stone-300 transition-all duration-300"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center text-violet-600 font-semibold text-sm">
                  {review.author.charAt(0)}
                </div>
                <div>
                  <p className="text-slate-800 text-sm font-medium">
                    {review.author}
                  </p>
                  <p className="text-slate-400 text-xs">{review.time}</p>
                </div>
              </div>
              <StarRating rating={review.rating} />
              <p className="mt-3 text-slate-600 text-sm leading-relaxed line-clamp-4">
                &ldquo;{review.text}&rdquo;
              </p>
            </div>
          ))}
        </div>

        <div className="mt-8 text-center">
          <p className="text-slate-400 text-xs">
            {reviews.aggregate_line}
          </p>
        </div>
      </div>
    </section>
  );
}
