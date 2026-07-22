import { CheckCircle, Shield } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import ScrollReveal from "@/components/shared/ScrollReveal";

interface CraftAboutProps {
  content: SiteContent;
  copy: TradeCopy;
  light?: boolean;
}

export default function CraftAbout({ content, copy, light = false }: CraftAboutProps) {
  const { business, about } = content;
  const title = light ? "text-[var(--trade-ink)]" : "text-white";
  const body = light ? "text-stone-600" : "text-slate-300";
  const sectionBg = light ? "bg-[var(--trade-surface)]" : "bg-[var(--trade-ink)]";
  const rule = light ? "border-stone-200" : "border-white/5";

  const sentences = about.story.split(/\.\s*/).filter(Boolean);

  return (
    <section className={`relative craft-section overflow-hidden ${sectionBg}`}>
      <div className={`absolute top-0 inset-x-0 border-t ${rule}`} />
      <div className="craft-container relative max-w-3xl mx-auto">
        <ScrollReveal>
          <p className="craft-eyebrow mb-3 sm:mb-4">About</p>
          <h2 className={`craft-display ${title}`}>{copy.about_title}</h2>
          {business.years_in_business ? (
            <p className="text-[var(--trade-accent)] font-medium mt-4 mb-6 sm:mb-8">
              Serving {business.city} for {business.years_in_business}+ years
            </p>
          ) : (
            <div className="mb-6 sm:mb-8" />
          )}

          <div className={`space-y-4 sm:space-y-5 leading-relaxed text-base sm:text-lg ${body}`}>
            {sentences.length > 1 ? (
              sentences.map((sentence, i, arr) => (
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

        <ScrollReveal
          delayMs={80}
          className="mt-10 sm:mt-14 border-l-2 border-[var(--trade-accent)]/50 pl-5 sm:pl-8"
        >
          <h3 className={`text-lg sm:text-xl font-display mb-5 ${title}`}>
            {copy.about_trust_title}
          </h3>
          <ul className="space-y-3.5">
            {about.trust_points.map((point, i) => (
              <li key={i} className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-[var(--trade-accent)] flex-shrink-0 mt-0.5" />
                <span className={`text-sm leading-relaxed ${body}`}>{point}</span>
              </li>
            ))}
          </ul>
          {about.certifications.length > 0 && (
            <div className={`mt-7 sm:mt-8 pt-6 border-t ${light ? "border-stone-200" : "border-white/10"}`}>
              <h4 className={`text-sm font-semibold mb-3 ${light ? "text-stone-500" : "text-slate-400"}`}>
                Certifications
              </h4>
              <div className="flex flex-wrap gap-2">
                {about.certifications.map((cert, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-[color-mix(in_oklab,var(--trade-accent)_35%,transparent)] text-[var(--trade-accent)] text-xs font-medium rounded-md"
                  >
                    <Shield className="h-3 w-3" aria-hidden />
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
