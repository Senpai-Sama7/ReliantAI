import { Phone } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface ContactBarProps {
  content: SiteContent;
  light?: boolean;
  tagline?: string;
}

export default function ContactBar({
  content,
  light = false,
  tagline = "Licensed · Local · Ready",
}: ContactBarProps) {
  const { phone, business_name } = content.business;

  return (
    <div
      className={`fixed top-0 inset-x-0 z-40 border-b pt-[var(--safe-top)] ${
        light
          ? "bg-[var(--trade-elevated)] border-stone-200"
          : "bg-[var(--trade-ink)] border-white/10"
      }`}
    >
      <div className="craft-container h-11 flex items-center justify-between gap-3">
        <p
          className={`text-xs font-medium truncate min-w-0 ${
            light ? "text-stone-700" : "text-slate-300"
          }`}
        >
          <span className="sm:hidden">{business_name}</span>
          <span className="hidden sm:inline">{tagline}</span>
        </p>
        <a
          href={`tel:${phone}`}
          className={`flex items-center gap-1.5 text-xs font-semibold shrink-0 min-h-9 px-2 rounded-md ${
            light
              ? "text-[var(--trade-primary)] hover:bg-stone-100"
              : "text-[var(--trade-accent)] hover:bg-white/5"
          }`}
        >
          <Phone className="h-3.5 w-3.5" aria-hidden />
          <span className="tabular-nums">{phone}</span>
        </a>
      </div>
    </div>
  );
}
