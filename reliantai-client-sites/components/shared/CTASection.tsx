import { Phone, Clock, ArrowRight } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface CTASectionProps {
  content: SiteContent;
  color: "blue" | "amber" | "orange" | "violet" | "emerald";
  variant?: "urgency" | "estimate";
  light?: boolean;
}

const BG_CLASSES: Record<string, string> = {
  blue: "bg-blue-700 hover:bg-blue-600",
  amber: "bg-amber-600 hover:bg-amber-500",
  orange: "bg-orange-600 hover:bg-orange-500",
  violet: "bg-violet-700 hover:bg-violet-600",
  emerald: "bg-emerald-700 hover:bg-emerald-600",
};

const ACCENT_COLORS: Record<string, string> = {
  blue: "text-blue-400",
  amber: "text-amber-400",
  orange: "text-orange-400",
  violet: "text-violet-600",
  emerald: "text-emerald-400",
};

const TRADE_URGENCY: Record<string, string> = {
  hvac: "AC broken? We can be there today.",
  plumbing: "Burst pipe? 24/7 emergency response.",
  electrical: "Sparking outlet? Don\u2019t wait \u2014 call now.",
  roofing: "Storm damage? Free inspection within 24 hours.",
  painting: "Ready to transform your space? Free color consultation.",
  landscaping: "Want a yard you love? Get a free estimate.",
};

export default function CTASection({ content, color = "blue", variant = "urgency", light = false }: CTASectionProps) {
  const { business } = content;
  const trade = content.site_config?.trade || "hvac";
  const message = TRADE_URGENCY[trade] || TRADE_URGENCY.hvac;
  const btnClass = BG_CLASSES[color] || BG_CLASSES.blue;
  const accentClass = ACCENT_COLORS[color] || ACCENT_COLORS.blue;

  if (variant === "estimate") {
    return (
      <section className={`relative py-24 ${light ? "bg-white" : "border-t border-slate-800/30"}`}>
        <div className={`absolute inset-0 ${light ? "bg-stone-50" : "bg-slate-950"}`} />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
          <div className={`${light ? "bg-white border border-stone-200" : "bg-slate-900 border border-slate-800"} rounded-lg p-10 sm:p-12 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-8`}>
            <div className="max-w-lg">
              <h3 className={`text-3xl font-bold font-display tracking-tight ${light ? "text-stone-900" : "text-white"}`}>
                Ready for a free estimate?
              </h3>
              <p className={`mt-3 text-lg leading-relaxed ${light ? "text-slate-600" : "text-slate-400"}`}>
                {business.business_name} serves {business.city} and surrounding areas. No obligation.
              </p>
            </div>
            <div className="flex flex-col items-start gap-2">
              <a
                href={`tel:${business.phone}`}
                className={`inline-flex items-center gap-3 px-8 py-3.5 text-white font-semibold rounded-md ${btnClass}`}
              >
                <Phone className="h-5 w-5" />
                {business.phone}
              </a>
              <span className={`text-xs ${light ? "text-slate-500" : "text-slate-500"}`}>Free estimates — no strings attached</span>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className={`relative py-8 border-y ${
      light
        ? "bg-stone-50 border-stone-200"
        : "bg-slate-950 border-slate-800/50"
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className={`hidden sm:flex items-center justify-center w-10 h-10 rounded-md ${light ? "bg-white border border-stone-200" : "bg-slate-900 border border-slate-800"}`}>
            <Clock className={`h-5 w-5 ${light ? accentClass : accentClass}`} />
          </div>
          <p className={light ? "text-stone-700 text-lg" : "text-slate-300 text-lg"}>
            <span className={`font-semibold ${light ? "text-stone-900" : "text-white"}`}>{message}</span>
            <span className={`hidden sm:inline ${light ? "text-stone-400" : "text-slate-500"}`}>{" "}— Same-day response.</span>
          </p>
        </div>
        <a
          href={`tel:${business.phone}`}
          className={`inline-flex items-center gap-2 px-6 py-3 text-white font-semibold rounded-md ${btnClass}`}
        >
          <Phone className="h-4 w-4" />
          Call now
          <ArrowRight className="h-4 w-4 opacity-70" />
        </a>
      </div>
    </section>
  );
}
