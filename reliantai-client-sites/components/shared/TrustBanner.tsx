import { ShieldCheck, Award, FileCheck } from "lucide-react";

interface TrustBannerProps {
  trade?: string;
  light?: boolean;
}

interface TrustItem {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
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
    { label: "Master Plumber Certified", icon: "award" },
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
    { label: "Worker&rsquo;s Comp Covered", icon: "filecheck" },
  ],
  painting: [
    { label: "Licensed & Insured", icon: "shield" },
    { label: "Lead-Safe Certified", icon: "award" },
    { label: "Satisfaction Guaranteed", icon: "filecheck" },
  ],
  landscaping: [
    { label: "Licensed & Insured", icon: "shield" },
    { label: "Green Industry Certified", icon: "award" },
    { label: "Satisfaction Guaranteed", icon: "filecheck" },
  ],
};

export default function TrustBanner({ trade = "hvac", light = false }: TrustBannerProps) {
  const trustItems = TRADE_TRUST[trade] || TRADE_TRUST.hvac;

  return (
    <div className={light
      ? "bg-white border-b border-slate-200"
      : "relative bg-slate-950 border-b border-slate-800"
    }>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-center gap-8 sm:gap-12 flex-wrap">
        {trustItems.map((item, i) => {
          const Icon = ICONS[item.icon];
          return (
            <div key={i} className="flex items-center gap-2">
              <Icon className="h-4 w-4 text-slate-500" />
              <span className="text-xs font-semibold tracking-wide uppercase text-slate-400">
                {item.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
