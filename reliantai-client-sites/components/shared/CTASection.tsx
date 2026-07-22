import { Phone, Clock, ArrowRight } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";
import { TRADE_COPY } from "@/lib/trade-copy";

interface CTASectionProps {
  content: SiteContent;
  color?: "steel" | "copper" | "gold" | "ochre" | "moss" | "amber" | "orange" | "emerald" | "blue";
  variant?: "urgency" | "estimate";
  light?: boolean;
}

export default function CTASection({
  content,
  color: _color = "steel",
  variant = "urgency",
  light = false,
}: CTASectionProps) {
  void _color; // color comes from CSS trade tokens now
  const { business } = content;
  const trade = content.site_config?.trade || "hvac";
  const copy = TRADE_COPY[trade] || TRADE_COPY.hvac;
  const message = copy.urgency_message;

  if (variant === "estimate") {
    return (
      <section
        className={`relative craft-section border-t ${
          light ? "border-stone-200 bg-[var(--trade-surface)]" : "border-white/5 bg-[var(--trade-ink)]"
        }`}
      >
        <div className="craft-container">
          <div
            className={`rounded-lg p-6 sm:p-10 lg:p-12 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 sm:gap-8 ${
              light
                ? "bg-[var(--trade-elevated)] border border-stone-200"
                : "bg-[var(--trade-surface)] border border-white/10"
            }`}
          >
            <div className="max-w-lg min-w-0">
              <h3
                className={`craft-display ${light ? "text-stone-900" : "text-white"}`}
              >
                {copy.estimate_heading}
              </h3>
              <p
                className={`mt-3 text-base sm:text-lg leading-relaxed ${
                  light ? "text-stone-600" : "text-[var(--trade-muted)]"
                }`}
              >
                {business.business_name} {copy.estimate_subtext}
              </p>
            </div>
            <div className="flex flex-col items-stretch sm:items-start gap-2 w-full sm:w-auto shrink-0">
              <a href={`tel:${business.phone}`} className="btn-trade">
                <Phone className="h-4 w-4" aria-hidden />
                {business.phone}
              </a>
              <span className="text-xs text-slate-500 text-center sm:text-left">
                Written estimate before any work starts
              </span>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section
      className={`relative border-y py-6 sm:py-8 ${
        light
          ? "bg-[var(--trade-surface)] border-stone-200"
          : "bg-[var(--trade-ink)] border-white/10"
      }`}
    >
      <div className="craft-container flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-start sm:items-center gap-3 min-w-0">
          <div
            className={`hidden sm:flex items-center justify-center w-10 h-10 rounded-md shrink-0 ${
              light
                ? "bg-white border border-stone-200"
                : "bg-[var(--trade-surface)] border border-white/10"
            }`}
          >
            <Clock className="h-5 w-5 text-[var(--trade-accent)]" aria-hidden />
          </div>
          <p className={`text-base sm:text-lg leading-snug ${light ? "text-stone-700" : "text-slate-300"}`}>
            <span className={`font-semibold ${light ? "text-stone-900" : "text-white"}`}>
              {message}
            </span>
          </p>
        </div>
        <a href={`tel:${business.phone}`} className="btn-trade shrink-0">
          <Phone className="h-4 w-4" aria-hidden />
          Call now
          <ArrowRight className="h-4 w-4 opacity-70" aria-hidden />
        </a>
      </div>
    </section>
  );
}
