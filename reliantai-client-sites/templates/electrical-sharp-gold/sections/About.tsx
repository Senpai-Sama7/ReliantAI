import { CheckCircle, Award, BadgeCheck } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import ScrollReveal from "@/components/shared/ScrollReveal";

interface AboutProps {
  content: SiteContent;
  copy: TradeCopy;
}

export default function About({ content, copy }: AboutProps) {
  const { business, about } = content;

  return (
    <section className="relative bg-[var(--trade-ink)] py-28 overflow-hidden">
      <div className="absolute top-0 inset-x-0 border-t border-white/5" />
      <div className="relative mx-auto max-w-3xl px-4 sm:px-6">
        <ScrollReveal>
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.3em] text-[var(--trade-accent)]">
            About
          </p>
          <h2 className="mt-4 font-display text-3xl text-white sm:text-4xl lg:text-5xl tracking-tight leading-[1.1]">
            {copy.about_title}
          </h2>
          {business.years_in_business && (
            <p className="mt-6 font-medium text-[var(--trade-accent)]">
              Serving {business.city} for {business.years_in_business}+ years
            </p>
          )}
          <div className="mt-8 space-y-5 text-base leading-relaxed text-slate-300 sm:text-lg">
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

        <ScrollReveal delayMs={80} className="mt-14 border-l-2 border-[var(--trade-accent)]/50 pl-8 sm:pl-12">
          <h3 className="font-display text-xl font-semibold text-white">
            {copy.about_trust_title}
          </h3>
          <ul className="mt-6 space-y-4">
            {about.trust_points.map((point, i) => (
              <li key={i} className="flex items-start gap-3">
                <CheckCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-[var(--trade-accent)]" />
                <span className="text-sm leading-relaxed text-slate-300">{point}</span>
              </li>
            ))}
          </ul>

          {about.certifications.length > 0 && (
            <div className="mt-8 border-t border-white/10 pt-6">
              <h4 className="mb-3 text-sm font-semibold text-slate-400">
                <Award className="mr-1.5 inline h-4 w-4 text-[var(--trade-accent)]" />
                Certifications
              </h4>
              <div className="flex flex-wrap gap-2">
                {about.certifications.map((cert, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1.5 rounded-md border border-[color-mix(in_oklab,var(--trade-accent)_35%,transparent)] px-3 py-1.5 text-xs font-medium text-[var(--trade-accent)]"
                  >
                    <BadgeCheck className="h-3 w-3" />
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