import { ShieldCheck, Award, FileCheck } from "lucide-react";

interface TrustBannerProps {
  trade?: string;
  light?: boolean;
}

const ICONS = {
  shield: ShieldCheck,
  award: Award,
  filecheck: FileCheck,
} as const;

type IconKey = keyof typeof ICONS;

const TRADE_TRUST: Record<string, { label: string; icon: IconKey }[]> = {
  hvac: [
    { label: "Licensed & Insured", icon: "shield" },
    { label: "EPA Certified", icon: "award" },
    { label: "Background Checked", icon: "filecheck" },
  ],
  plumbing: [
    { label: "Licensed & Insured", icon: "shield" },
    { label: "Master Plumber", icon: "award" },
    { label: "Background Checked", icon: "filecheck" },
  ],
  electrical: [
    { label: "Licensed & Insured", icon: "shield" },
    { label: "NEC Compliant", icon: "award" },
    { label: "Background Checked", icon: "filecheck" },
  ],
  roofing: [
    { label: "Licensed & Insured", icon: "shield" },
    { label: "GAF Certified", icon: "award" },
    { label: "Workers Comp", icon: "filecheck" },
  ],
  painting: [
    { label: "Licensed & Insured", icon: "shield" },
    { label: "Lead-Safe Certified", icon: "award" },
    { label: "Satisfaction Guarantee", icon: "filecheck" },
  ],
  landscaping: [
    { label: "Licensed & Insured", icon: "shield" },
    { label: "Industry Certified", icon: "award" },
    { label: "Satisfaction Guarantee", icon: "filecheck" },
  ],
};

export default function TrustBanner({ trade = "hvac", light = false }: TrustBannerProps) {
  const trustItems = TRADE_TRUST[trade] || TRADE_TRUST.hvac;

  return (
    <div
      className={
        light
          ? "bg-[var(--trade-elevated)] border-b border-stone-200"
          : "relative bg-[var(--trade-ink)] border-b border-white/10"
      }
    >
      {/* Horizontal scroll on narrow phones — never wraps into a smushed pile */}
      <div className="craft-container py-3.5">
        <ul className="flex items-center gap-5 sm:gap-8 lg:gap-12 overflow-x-auto scrollbar-none [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {trustItems.map((item, i) => {
            const Icon = ICONS[item.icon];
            return (
              <li key={i} className="flex items-center gap-2 shrink-0">
                <Icon
                  className={`h-3.5 w-3.5 ${light ? "text-stone-500" : "text-slate-500"}`}
                  aria-hidden
                />
                <span
                  className={`text-[0.6875rem] sm:text-xs font-semibold tracking-[0.12em] uppercase whitespace-nowrap ${
                    light ? "text-stone-600" : "text-slate-400"
                  }`}
                >
                  {item.label}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
