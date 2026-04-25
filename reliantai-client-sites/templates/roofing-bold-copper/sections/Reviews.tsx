"use client";

import { Star } from "lucide-react";
import { motion } from "framer-motion";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";

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

const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.97 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { delay: i * 0.08, duration: 0.4, ease: "easeOut" as const },
  }),
};

export default function Reviews({ content, copy }: ReviewsProps) {
  const { business, reviews } = content;

  return (
    <section className="py-24 bg-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight">
            {copy.reviews_title}
          </h2>
          <div className="mt-4 flex items-center justify-center gap-2">
            <StarRating rating={Math.round(business.google_rating)} />
            <span className="text-slate-400 text-sm font-medium">
              {business.google_rating} ({business.review_count} reviews on
              Google)
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {reviews.reviews.map((review, i) => (
            <motion.div
              key={i}
              custom={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.1 }}
              variants={cardVariants}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
              className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-6 hover:border-orange-500/30 transition-colors duration-300"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-orange-500/20 border border-orange-500/30 flex items-center justify-center text-orange-300 font-semibold text-sm">
                  {review.author.charAt(0)}
                </div>
                <div>
                  <p className="text-white text-sm font-semibold">
                    {review.author}
                  </p>
                  <p className="text-slate-500 text-xs">{review.time}</p>
                </div>
              </div>
              <StarRating rating={review.rating} />
              <p className="mt-3 text-slate-400 text-sm leading-relaxed line-clamp-4">
                &ldquo;{review.text}&rdquo;
              </p>
            </motion.div>
          ))}
        </div>

        <div className="mt-10 text-center">
          <p className="text-slate-500 text-xs font-medium">
            {reviews.aggregate_line}
          </p>
        </div>
      </div>
    </section>
  );
}
