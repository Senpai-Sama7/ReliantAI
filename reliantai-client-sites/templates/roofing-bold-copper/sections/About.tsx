import { Award } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";

interface AboutProps {
  content: SiteContent;
  copy: TradeCopy;
}

export default function About({ content, copy }: AboutProps) {
  const { business, about } = content;

  return (
    <section className="py-24 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        {/* Editorial narrative — story first */}
        <div className="max-w-3xl">
          <p className="text-orange-400 text-sm font-semibold uppercase tracking-widest mb-3">
            {business.business_name}
          </p>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight leading-tight">
            {copy.about_title}
          </h2>
          <p className="mt-6 text-slate-300 text-lg leading-relaxed">
            {about.story}
          </p>
          {business.years_in_business && (
            <p className="mt-4 text-orange-400 font-semibold text-lg">
              Serving {business.city} for {business.years_in_business}+ years
            </p>
          )}
        </div>

        {/* Trust points — horizontal bar */}
        <div className="mt-14 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {about.trust_points.map((point, i) => (
            <div
              key={i}
              className="flex items-start gap-3 bg-slate-900/50 border border-slate-800/70 rounded-xl px-5 py-4"
            >
              <span className="mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-orange-500/15 text-orange-400">
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </span>
              <span className="text-slate-300 text-sm leading-relaxed">{point}</span>
            </div>
          ))}
        </div>

        {/* Certifications */}
        {about.certifications.length > 0 && (
          <div className="mt-12 flex flex-wrap items-center gap-3">
            {about.certifications.map((cert, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-orange-500/10 border border-orange-500/20 text-orange-300 text-xs font-medium rounded-full"
              >
                <Award className="h-3 w-3" />
                {cert}
              </span>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}