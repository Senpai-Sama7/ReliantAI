import { CheckCircle, Shield } from "lucide-react";
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

interface AboutProps {
  content: SiteContent;
  copy: TradeCopy;
}

export default function About({ content, copy }: AboutProps) {
  const { business, about } = content;

  return (
    <section className="relative py-24 bg-slate-950 overflow-hidden">
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent" />

      <div className="relative max-w-4xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <p className="text-emerald-400 text-sm font-semibold uppercase tracking-wider mb-3">
            {copy.about_trust_title}
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-white font-display">
            {copy.about_title}
          </h2>
        </div>

        <div className="relative">
          <div className="absolute -left-4 top-0 bottom-0 w-1 bg-emerald-500/20 rounded-full hidden sm:block" />
          <div className="sm:pl-8 space-y-8">
            <p className="text-slate-300 leading-relaxed text-lg">
              {about.story}
            </p>
            {business.years_in_business && (
              <p className="text-emerald-400 font-medium text-lg">
                Serving {business.city} for {business.years_in_business}+ years
              </p>
            )}
          </div>
        </div>

        {about.trust_points.length > 0 && (
          <div className="mt-16 grid grid-cols-1 sm:grid-cols-2 gap-4">
            {about.trust_points.map((point, i) => (
              <div
                key={i}
                className="flex items-start gap-3 bg-slate-900/50 border border-slate-800 rounded-lg px-5 py-4"
              >
                <CheckCircle className="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                <span className="text-slate-300 text-sm font-medium">{point}</span>
              </div>
            ))}
          </div>
        )}

        {about.certifications.length > 0 && (
          <div className="mt-10 flex flex-wrap justify-center gap-2">
            {about.certifications.map((cert, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-900/40 border border-emerald-700/40 text-emerald-300 text-xs font-medium rounded-full"
              >
                <Shield className="h-3 w-3" />
                {cert}
              </span>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}