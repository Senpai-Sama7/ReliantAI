import { Phone } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface ContactBarProps {
  content: SiteContent;
}

export default function ContactBar({ content }: ContactBarProps) {
  const { phone } = content.business;

  return (
    <div className="fixed top-0 inset-x-0 z-40 bg-slate-950/95 backdrop-blur-sm border-b border-slate-800/50 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-12 flex items-center justify-center sm:justify-between">
        <a
          href={`tel:${phone}`}
          className="flex items-center gap-2 text-sm font-semibold hover:text-orange-300 transition-colors"
        >
          <Phone className="h-4 w-4 text-orange-400" />
          <span className="hidden sm:inline">{phone}</span>
          <span className="sm:hidden">Call Now</span>
        </a>
        <span className="hidden sm:block text-xs text-slate-500 font-medium tracking-wide uppercase">
          24/7 Emergency Roofing
        </span>
      </div>
    </div>
  );
}
