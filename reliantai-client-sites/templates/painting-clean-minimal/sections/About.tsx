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
      <div className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <p className="text-violet-600 text-sm font-semibold uppercase tracking-wider mb-3">
            {copy.about_trust_title}
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 font-display tracking-tight">
            {copy.about_title}
          </h2>
        </div>

        <div className="relative">
          <div className="absolute -left-4 top-0 bottom-0 w-1 bg-violet-200 rounded-full hidden sm:block" />
          <div className="sm:pl-8 space-y-8">
            <p className="text-slate-600 leading-relaxed text-lg">
              {about.story}
            </p>
            {business.years_in_business && (
              <p className="text-violet-600 font-medium text-lg">
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
                className="flex items-start gap-3 bg-white border border-stone-200 rounded-lg px-5 py-4"
              >
                <CheckCircle className="h-5 w-5 text-violet-600 flex-shrink-0 mt-0.5" />
                <span className="text-slate-700 text-sm font-medium">{point}</span>
              </div>
            ))}
          </div>
        )}

        {about.certifications.length > 0 && (
          <div className="mt-10 flex flex-wrap justify-center gap-2">
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
        )}
      </div>
    </section>
  );
}