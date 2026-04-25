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
      {/* Subtle top gradient border */}
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent" />
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute bottom-0 left-0 w-80 h-80 rounded-full bg-emerald-600/3 blur-3xl" />
      </div>
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6 font-display">
              {copy.about_title}
            </h2>
            <p className="text-slate-300 leading-relaxed text-base">
              {about.story}
            </p>
            {business.years_in_business && (
              <p className="mt-4 text-emerald-400 font-medium">
                Serving {business.city} for {business.years_in_business}+ years
              </p>
            )}
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8">
            <h3 className="text-xl font-semibold text-white mb-6">
              {copy.about_trust_title}
            </h3>
            <ul className="space-y-4">
              {about.trust_points.map((point, i) => (
                <li key={i} className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span className="text-slate-300 text-sm">{point}</span>
                </li>
              ))}
            </ul>
            {about.certifications.length > 0 && (
              <div className="mt-6 pt-6 border-t border-slate-800">
                <h4 className="text-sm font-semibold text-slate-400 mb-3">
                  Certifications
                </h4>
                <div className="flex flex-wrap gap-2">
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
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
