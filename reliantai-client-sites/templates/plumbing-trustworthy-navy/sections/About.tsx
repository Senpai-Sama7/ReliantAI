import { CheckCircle, ShieldCheck, Award, FileCheck } from "lucide-react";
import { TRADE_COPY } from "@/lib/trade-copy";
import type { SiteContent } from "@/types/SiteContent";

interface AboutProps {
  content: SiteContent;
}

const CERT_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  licensed: ShieldCheck,
  master: Award,
  certified: Award,
  insured: ShieldCheck,
  bonded: ShieldCheck,
  background: FileCheck,
  epa: Award,
  nec: Award,
};

function getCertIcon(cert: string) {
  const lower = cert.toLowerCase();
  for (const [keyword, Icon] of Object.entries(CERT_ICONS)) {
    if (lower.includes(keyword)) return <Icon className="h-4 w-4" />;
  }
  return <Award className="h-4 w-4" />;
}

export default function About({ content }: AboutProps) {
  const { business, about } = content;
  const copy = TRADE_COPY[content.site_config.trade as keyof typeof TRADE_COPY] ?? TRADE_COPY.plumbing;

  return (
    <section id="about" className="py-28 bg-slate-950 relative">
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <span className="inline-block text-blue-400 text-xs font-semibold tracking-[0.2em] uppercase mb-4">
          About Us
        </span>
        <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6 font-display max-w-xl">
          {copy.about_title}
        </h2>

        <div className="max-w-2xl">
          <p className="text-slate-300 leading-relaxed text-lg">
            {about.story}
          </p>
          {business.years_in_business && (
            <p className="mt-6 text-blue-400 font-semibold">
              Serving {business.city} for {business.years_in_business}+ years
            </p>
          )}
        </div>

        <div className="mt-14 lg:ml-16 max-w-xl bg-slate-900/80 border-l-2 border-blue-500/40 rounded-r-2xl p-8">
          <h3 className="text-xl font-semibold text-white mb-5 font-display">
            {copy.about_trust_title}
          </h3>
          <ul className="space-y-3">
            {about.trust_points.map((point, i) => (
              <li key={i} className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <span className="text-slate-300 text-sm">{point}</span>
              </li>
            ))}
          </ul>
          {about.certifications.length > 0 && (
            <div className="mt-7 pt-6 border-t border-slate-800">
              <h4 className="text-sm font-semibold text-slate-400 mb-3">
                Certifications
              </h4>
              <div className="flex flex-wrap gap-2">
                {about.certifications.map((cert, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 border border-slate-700 text-blue-300 text-xs font-medium rounded-full"
                  >
                    {getCertIcon(cert)}
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