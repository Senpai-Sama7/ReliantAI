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
    <section className="relative py-28 bg-slate-950 overflow-hidden">
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-blue-500/20 to-transparent" />

      <div className="relative max-w-3xl mx-auto px-4 sm:px-6">
        <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4 font-display">
          {copy.about_title}
        </h2>
        {business.years_in_business && (
          <p className="text-blue-400 font-medium mb-8">
            Serving {business.city} for {business.years_in_business}+ years
          </p>
        )}

        <div className="space-y-5 text-slate-300 leading-relaxed">
          {about.story.split(/\.\s*/).filter(Boolean).length > 1 ? (
            about.story.split(/\.\s*/).filter(Boolean).map((sentence, i, arr) => (
              <p key={i}>
                {sentence}{i < arr.length - 1 ? "." : ""}
              </p>
            ))
          ) : (
            <p>{about.story}</p>
          )}
        </div>

        <div className="mt-14 bg-slate-900/60 border border-slate-800 rounded-2xl p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-1 h-8 bg-blue-500 rounded-full" />
            <h3 className="text-xl font-semibold text-white">
              {copy.about_trust_title}
            </h3>
          </div>
          <ul className="space-y-4">
            {about.trust_points.map((point, i) => (
              <li key={i} className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <span className="text-slate-300 text-sm">{point}</span>
              </li>
            ))}
          </ul>
          {about.certifications.length > 0 && (
            <div className="mt-8 pt-6 border-t border-slate-800">
              <h4 className="text-sm font-semibold text-slate-400 mb-3">
                Certifications
              </h4>
              <div className="flex flex-wrap gap-2">
                {about.certifications.map((cert, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-900/40 border border-blue-700/40 text-blue-300 text-xs font-medium rounded-full"
                  >
                    <Shield className="h-3 w-3" />
                    {cert}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}