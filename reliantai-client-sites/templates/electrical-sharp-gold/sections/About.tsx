import { CheckCircle, Award, BadgeCheck } from "lucide-react";
import { TRADE_COPY } from "@/lib/trade-copy";
import type { SiteContent } from "@/types/SiteContent";

interface AboutProps {
  content: SiteContent;
}

export default function About({ content }: AboutProps) {
  const { business, about } = content;
  const copy = TRADE_COPY[content.site_config.trade] || TRADE_COPY.electrical;

  return (
    <section id="about" className="py-24 bg-slate-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6 font-display">
              {copy.about_title}
            </h2>
            <p className="text-slate-300 leading-relaxed text-base">
              {about.story}
            </p>
            {business.years_in_business && (
              <p className="mt-4 text-amber-400 font-medium">
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
                  <CheckCircle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <span className="text-slate-300 text-sm">{point}</span>
                </li>
              ))}
            </ul>
            {about.certifications.length > 0 && (
              <div className="mt-6 pt-6 border-t border-slate-800">
                <h4 className="text-sm font-semibold text-slate-400 mb-3">
                  <Award className="h-4 w-4 inline mr-1.5 text-amber-400" />
                  Certifications
                </h4>
                <div className="flex flex-wrap gap-2">
                  {about.certifications.map((cert, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-950/40 border border-amber-800/50 text-amber-300 text-xs font-medium rounded-full"
                    >
                      <BadgeCheck className="h-3 w-3" />
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
