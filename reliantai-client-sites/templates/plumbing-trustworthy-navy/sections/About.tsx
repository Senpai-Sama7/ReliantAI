import { CheckCircle, ShieldCheck, Award, FileCheck } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import ScrollReveal from "@/components/shared/ScrollReveal";

interface AboutProps {
  content: SiteContent;
  copy: TradeCopy;
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

export default function About({ content, copy }: AboutProps) {
  const { business, about } = content;

  return (
    <section className="relative py-28 bg-[var(--trade-ink)] overflow-hidden">
      <div className="absolute top-0 inset-x-0 border-t border-white/5" />

      <div className="relative max-w-3xl mx-auto px-4 sm:px-6">
        <ScrollReveal>
          <p className="text-[0.65rem] uppercase tracking-[0.28em] text-[var(--trade-accent)] mb-4">
            About
          </p>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl text-white mb-4 font-display tracking-tight leading-[1.1]">
            {copy.about_title}
          </h2>
          {business.years_in_business && (
            <p className="text-[var(--trade-accent)] font-medium mb-8">
              Serving {business.city} for {business.years_in_business}+ years
            </p>
          )}

          <div className="space-y-5 text-slate-300 leading-relaxed text-base sm:text-lg">
            {about.story.split(/\.\s*/).filter(Boolean).length > 1 ? (
              about.story
                .split(/\.\s*/)
                .filter(Boolean)
                .map((sentence, i, arr) => (
                  <p key={i}>
                    {sentence}
                    {i < arr.length - 1 ? "." : ""}
                  </p>
                ))
            ) : (
              <p>{about.story}</p>
            )}
          </div>
        </ScrollReveal>

        <ScrollReveal delayMs={80} className="mt-14 border-l-2 border-[var(--trade-accent)]/50 pl-8 sm:pl-10">
          <h3 className="text-xl font-semibold text-white mb-5 font-display">
            {copy.about_trust_title}
          </h3>
          <ul className="space-y-3">
            {about.trust_points.map((point, i) => (
              <li key={i} className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-[var(--trade-accent)] flex-shrink-0 mt-0.5" />
                <span className="text-slate-300 text-sm">{point}</span>
              </li>
            ))}
          </ul>
          {about.certifications.length > 0 && (
            <div className="mt-7 pt-6 border-t border-white/10">
              <h4 className="text-sm font-semibold text-slate-400 mb-3">
                Certifications
              </h4>
              <div className="flex flex-wrap gap-2">
                {about.certifications.map((cert, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-[color-mix(in_oklab,var(--trade-accent)_35%,transparent)] text-[var(--trade-accent)] text-xs font-medium rounded-md"
                  >
                    {getCertIcon(cert)}
                    {cert}
                  </span>
                ))}
              </div>
            </div>
          )}
        </ScrollReveal>
      </div>
    </section>
  );
}