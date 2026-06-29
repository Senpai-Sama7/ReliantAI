"use client";

import BrandLogo from "./BrandLogo";
import StoreStatus from "./StoreStatus";

const MAPS = "https://maps.google.com/?q=6590+SW+Freeway+Houston+TX";

export default function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--dd-line)] bg-[var(--dd-bg)]/95 backdrop-blur-sm">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
        <a href="#" className="flex items-center gap-3 min-w-0">
          <BrandLogo size="sm" showWordmark={false} />
          <span className="dd-brand text-lg text-[var(--dd-gold)] hidden sm:block truncate">
            DOLLAR DANK
          </span>
        </a>

        <div className="hidden md:block">
          <StoreStatus inline />
        </div>

        <a href={MAPS} target="_blank" rel="noopener noreferrer" className="dd-btn-primary text-sm shrink-0">
          Directions
        </a>
      </div>
    </header>
  );
}
