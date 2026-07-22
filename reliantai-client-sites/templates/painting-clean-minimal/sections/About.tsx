import { CheckCircle, Shield } from "lucide-react";
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
    <section className="relative py-28 bg-[var(--trade-surface)] overflow-hidden">
      <div className="absolute top-0 inset-x-0 border-t border-stone-200" />
      <div className="relative max-w-4xl mx-auto px-4 sm:px-6">
        <ScrollReveal className="mb-14">
          <p className="text-[0.65rem] uppercase tracking-[0.28em] text-[var(--trade-accent)] mb-4">
            About
          </p>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl text-[var(--trade-ink)] font-display tracking-tight leading-[1.1]">
            {copy.about_title}
          </h2>

          <div className="mt-8 space-y-5 text-stone-600 leading-relaxed text-base sm:text-lg max-w-3xl">
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
            {business.years_in_business && (
              <p className="text-[var(--trade-primary)] font-medium">
                Serving {business.city} for {business.years_in_business}+ years
              </p>
            )}
          </div>
        </ScrollReveal>

        {about.trust_points.length > 0 && (
          <ScrollReveal delayMs={80} className="mt-16 border-l-2 border-[var(--trade-accent)]/40 pl-8 sm:pl-10">
            <h3 className="text-xl font-display text-[var(--trade-ink)] mb-6">
              {copy.about_trust_title}
            </h3>
            <ul className="space-y-4">
            {about.trust_points.map((point, i) => (
              <li
                key={i}
                className="flex items-start gap-3"
              >
                <CheckCircle className="h-5 w-5 text-[var(--trade-accent)] flex-shrink-0 mt-0.5" />
                <span className="text-stone-700 text-sm leading-relaxed">{point}</span>
              </li>
            ))}
            </ul>
          </ScrollReveal>
        )}

        {about.certifications.length > 0 && (
          <ScrollReveal delayMs={120} className="mt-10 flex flex-wrap gap-2">
            {about.certifications.map((cert, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[color-mix(in_oklab,var(--trade-accent)_30%,transparent)] text-[var(--trade-primary)] text-xs font-medium rounded-md"
              >
                <Shield className="h-3 w-3" />
                {cert}
              </span>
            ))}
          </ScrollReveal>
        )}
      </div>
    </section>
  );
}