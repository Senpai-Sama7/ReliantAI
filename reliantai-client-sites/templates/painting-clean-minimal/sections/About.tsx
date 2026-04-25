import { CheckCircle, Shield } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface AboutProps {
  content: SiteContent;
  copy: {
    about_title: string;
    about_trust_title: string;
  };
}

export default function About({ content, copy }: AboutProps) {
  const { business, about } = content;

  return (
    <section className="py-28 bg-stone-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-6 font-display tracking-tight">
              {copy.about_title}
            </h2>
            <p className="text-slate-600 leading-relaxed text-base">
              {about.story}
            </p>
            {business.years_in_business && (
              <p className="mt-4 text-violet-600 font-medium">
                Serving {business.city} for {business.years_in_business}+ years
              </p>
            )}
          </div>

          <div className="bg-white border border-stone-200 rounded-xl p-8">
            <h3 className="text-xl font-semibold text-slate-900 mb-6">
              {copy.about_trust_title}
            </h3>
            <ul className="space-y-4">
              {about.trust_points.map((point, i) => (
                <li key={i} className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-violet-600 flex-shrink-0 mt-0.5" />
                  <span className="text-slate-600 text-sm">{point}</span>
                </li>
              ))}
            </ul>
            {about.certifications.length > 0 && (
              <div className="mt-6 pt-6 border-t border-stone-200">
                <h4 className="text-sm font-semibold text-slate-500 mb-3">
                  Certifications
                </h4>
                <div className="flex flex-wrap gap-2">
                  {about.certifications.map((cert, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-violet-50 border border-violet-200 text-violet-700 text-xs font-medium rounded-full"
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
