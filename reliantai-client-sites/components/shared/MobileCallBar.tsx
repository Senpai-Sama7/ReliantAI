import { Phone } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface MobileCallBarProps {
  content: SiteContent;
  label?: string;
}

/** Sticky phone CTA for phones only — local-business conversion floor. */
export default function MobileCallBar({ content, label }: MobileCallBarProps) {
  const { business, hero } = content;
  const cta = label || hero.cta_primary || "Call now";

  return (
    <div className="mobile-callbar sm:hidden" role="region" aria-label="Call business">
      <a href={`tel:${business.phone}`} className="btn-trade shadow-none">
        <Phone className="h-4 w-4 shrink-0" aria-hidden />
        <span className="truncate">
          {cta}
          <span className="opacity-70 font-normal"> · {business.phone}</span>
        </span>
      </a>
    </div>
  );
}
