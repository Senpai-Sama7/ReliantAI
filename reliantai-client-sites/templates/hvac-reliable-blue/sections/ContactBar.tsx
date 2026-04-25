import { Phone } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface ContactBarProps {
  content: SiteContent;
}

export default function ContactBar({ content }: ContactBarProps) {
  const { phone } = content.business;

  return (
    <div className="fixed top-0 inset-x-0 z-40 bg-slate-950/90 backdrop-blur-sm border-b border-slate-800/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-10 flex items-center justify-center sm:justify-between">
        <a
          href={`tel:${phone}`}
          className="flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-blue-300 transition-colors"
        >
          <Phone className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">{phone}</span>
          <span className="sm:hidden">Call Now</span>
        </a>
        <span className="hidden sm:block text-[11px] text-slate-500 tracking-wide uppercase">
          24/7 Emergency Service Available
        </span>
      </div>
    </div>
  );
}
