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
    <section id="about" className="bg-slate-950 py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-amber-400">
            About Us
          </p>
          <h2 className="mt-3 font-display text-3xl font-bold text-white sm:text-4xl">
            {copy.about_title}
          </h2>
          <p className="mt-6 text-base leading-relaxed text-slate-300">{about.story}</p>
          {business.years_in_business && (
            <p className="mt-4 font-medium text-amber-400">
              Serving {business.city} for {business.years_in_business}+ years
            </p>
          )}
        </div>

        <div className="mt-14 border-l-2 border-amber-500/30 pl-8 sm:pl-12">
          <h3 className="font-display text-xl font-semibold text-white">
            {copy.about_trust_title}
          </h3>
          <ul className="mt-6 space-y-4">
            {about.trust_points.map((point, i) => (
              <li key={i} className="flex items-start gap-3">
                <CheckCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-400" />
                <span className="text-sm leading-relaxed text-slate-300">{point}</span>
              </li>
            ))}
          </ul>

          {about.certifications.length > 0 && (
            <div className="mt-8 border-t border-slate-800 pt-6">
              <h4 className="mb-3 text-sm font-semibold text-slate-400">
                <Award className="mr-1.5 inline h-4 w-4 text-amber-400" />
                Certifications
              </h4>
              <div className="flex flex-wrap gap-2">
                {about.certifications.map((cert, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1.5 rounded-full border border-amber-800/50 bg-amber-950/40 px-3 py-1.5 text-xs font-medium text-amber-300"
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
    </section>
  );
}