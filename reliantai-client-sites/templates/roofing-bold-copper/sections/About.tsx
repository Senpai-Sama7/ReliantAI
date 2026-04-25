import { CheckCircle, Award } from "lucide-react";
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-white mb-6 tracking-tight">
              {copy.about_title}
            </h2>
            <p className="text-slate-300 leading-relaxed text-base">
              {about.story}
            </p>
            {business.years_in_business && (
              <p className="mt-6 text-orange-400 font-semibold text-lg">
                Serving {business.city} for {business.years_in_business}+ years
              </p>
            )}
          </div>

          <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-8">
            <h3 className="font-display text-xl font-semibold text-white mb-6">
              {copy.about_trust_title}
            </h3>
            <ul className="space-y-4">
              {about.trust_points.map((point, i) => (
                <li key={i} className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-orange-400 flex-shrink-0 mt-0.5" />
                  <span className="text-slate-300 text-sm leading-relaxed">{point}</span>
                </li>
              ))}
            </ul>
            {about.certifications.length > 0 && (
              <div className="mt-8 pt-6 border-t border-slate-800">
                <h4 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">
                  Certifications
                </h4>
                <div className="flex flex-wrap gap-2">
                  {about.certifications.map((cert, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-orange-500/10 border border-orange-500/20 text-orange-300 text-xs font-medium rounded-full"
                    >
                      <Award className="h-3 w-3" />
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
