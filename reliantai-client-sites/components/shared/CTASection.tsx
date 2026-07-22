import { Phone, Clock, ArrowRight } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";
import { TRADE_COPY } from "@/lib/trade-copy";

interface CTASectionProps {
  content: SiteContent;
  /** Token-driven accents — never Tailwind blue-500 / indigo */
  color: "steel" | "copper" | "gold" | "ochre" | "moss" | "amber" | "orange" | "emerald" | "blue";
  variant?: "urgency" | "estimate";
  light?: boolean;
}

/** Map legacy color names → CSS custom properties (no Tailwind blue-500) */
const TOKEN: Record<string, { btn: string; accent: string }> = {
  steel: {
    btn: "bg-[var(--trade-primary)] hover:brightness-110",
    accent: "text-[var(--trade-accent)]",
  },
  copper: {
    btn: "bg-[var(--trade-primary)] hover:brightness-110",
    accent: "text-[var(--trade-accent)]",
  },
  gold: {
    btn: "bg-[var(--trade-primary)] hover:brightness-110",
    accent: "text-[var(--trade-accent)]",
  },
  ochre: {
    btn: "bg-[var(--trade-primary)] hover:brightness-110",
    accent: "text-[var(--trade-accent)]",
  },
  moss: {
    btn: "bg-[var(--trade-primary)] hover:brightness-110",
    accent: "text-[var(--trade-accent)]",
  },
  // Legacy aliases → same token system
  blue: {
    btn: "bg-[var(--trade-primary)] hover:brightness-110",
    accent: "text-[var(--trade-accent)]",
  },
  amber: {
    btn: "bg-[var(--trade-primary)] hover:brightness-110",
    accent: "text-[var(--trade-accent)]",
  },
  orange: {
    btn: "bg-[var(--trade-primary)] hover:brightness-110",
    accent: "text-[var(--trade-accent)]",
  },
  emerald: {
    btn: "bg-[var(--trade-primary)] hover:brightness-110",
    accent: "text-[var(--trade-accent)]",
  },
};

export default function CTASection({
  content,
  color = "steel",
  variant = "urgency",
  light = false,
}: CTASectionProps) {
  const { business } = content;
  const trade = content.site_config?.trade || "hvac";
  const copy = TRADE_COPY[trade] || TRADE_COPY.hvac;
  const message = copy.urgency_message;
  const tokens = TOKEN[color] || TOKEN.steel;

  if (variant === "estimate") {
    return (
      <section className={`relative py-24 ${light ? "bg-white" : "border-t border-white/5"}`}>
        <div className={`absolute inset-0 ${light ? "bg-[var(--trade-surface)]" : "bg-[var(--trade-ink)]"}`} />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
          <div
            className={`${
              light
                ? "bg-[var(--trade-elevated)] border border-stone-200"
                : "bg-[var(--trade-surface)] border border-white/10"
            } rounded-lg p-10 sm:p-12 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-8`}
          >
            <div className="max-w-lg">
              <h3
                className={`text-3xl font-display tracking-tight ${light ? "text-stone-900" : "text-white"}`}
              >
                {copy.estimate_heading}
              </h3>
              <p className={`mt-3 text-lg leading-relaxed ${light ? "text-stone-600" : "text-slate-400"}`}>
                {business.business_name} {copy.estimate_subtext}
              </p>
            </div>
            <div className="flex flex-col items-start gap-2">
              <a
                href={`tel:${business.phone}`}
                className={`inline-flex items-center gap-3 px-8 py-3.5 text-white font-semibold rounded-md ${tokens.btn}`}
              >
                <Phone className="h-5 w-5" />
                {business.phone}
              </a>
              <span className="text-xs text-slate-500">Written estimate before any work starts</span>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section
      className={`relative py-8 border-y ${
        light
          ? "bg-[var(--trade-surface)] border-stone-200"
          : "bg-[var(--trade-ink)] border-white/10"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div
            className={`hidden sm:flex items-center justify-center w-10 h-10 rounded-md ${
              light ? "bg-white border border-stone-200" : "bg-[var(--trade-surface)] border border-white/10"
            }`}
          >
            <Clock className={`h-5 w-5 ${tokens.accent}`} />
          </div>
          <p className={light ? "text-stone-700 text-lg" : "text-slate-300 text-lg"}>
            <span className={`font-semibold ${light ? "text-stone-900" : "text-white"}`}>{message}</span>
          </p>
        </div>
        <a
          href={`tel:${business.phone}`}
          className={`inline-flex items-center gap-2 px-6 py-3 text-white font-semibold rounded-md ${tokens.btn}`}
        >
          <Phone className="h-4 w-4" />
          Call now
          <ArrowRight className="h-4 w-4 opacity-70" />
        </a>
      </div>
    </section>
  );
}
