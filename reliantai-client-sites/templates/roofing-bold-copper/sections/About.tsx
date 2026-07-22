import { Award } from "lucide-react";
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
    <section className="relative py-28 bg-[var(--trade-ink)] overflow-hidden">
      <div className="absolute top-0 inset-x-0 border-t border-white/5" />
      <div className="relative max-w-3xl mx-auto px-4 sm:px-6">
        <ScrollReveal>
          <p className="text-[0.65rem] uppercase tracking-[0.28em] text-[var(--trade-accent)] mb-4">
            About
          </p>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl text-white tracking-tight leading-[1.1]">
            {copy.about_title}
          </h2>
          {business.years_in_business && (
            <p className="mt-6 text-[var(--trade-accent)] font-medium">
              Serving {business.city} for {business.years_in_business}+ years
            </p>
          )}
          <div className="mt-8 space-y-5 text-slate-300 text-base sm:text-lg leading-relaxed">
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

        <ScrollReveal delayMs={80} as="ol" className="mt-14 space-y-5 border-l-2 border-[var(--trade-accent)]/50 pl-8 sm:pl-10">
          {about.trust_points.map((point, i) => (
            <li
              key={i}
              className="flex items-start gap-4 border-t border-white/10 pt-5 first:border-t-0 first:pt-0"
            >
              <span className="mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border border-[var(--trade-accent)]/50 text-[var(--trade-accent)]">
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </span>
              <span className="text-slate-300 text-sm leading-relaxed">{point}</span>
            </li>
          ))}
        </ScrollReveal>

        {about.certifications.length > 0 && (
          <ScrollReveal delayMs={120} className="mt-12 flex flex-wrap items-center gap-3">
            {about.certifications.map((cert, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 border border-[color-mix(in_oklab,var(--trade-accent)_35%,transparent)] text-[var(--trade-accent)] text-xs font-medium rounded-md"
              >
                <Award className="h-3 w-3" />
                {cert}
              </span>
            ))}
          </ScrollReveal>
        )}
      </div>
    </section>
  );
}