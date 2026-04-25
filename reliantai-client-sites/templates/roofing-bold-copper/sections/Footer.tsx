import { Phone, MapPin, Globe } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface FooterProps {
  content: SiteContent;
}

const SECTION_ANCHORS = [
  { id: "services", label: "Services" },
  { id: "about", label: "About" },
  { id: "reviews", label: "Reviews" },
  { id: "faq", label: "FAQ" },
];

export default function Footer({ content }: FooterProps) {
  const { business } = content;
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-slate-950 border-t border-slate-800">
      <div className="pb-24 sm:pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-14">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
            {/* Brand */}
            <div>
              <h3 className="font-display text-white font-bold text-xl mb-4">
                {business.business_name}
              </h3>
              <div className="space-y-3 text-sm text-slate-400">
                <a
                  href={`tel:${business.phone}`}
                  className="flex items-center gap-2 hover:text-orange-300 transition-colors"
                >
                  <Phone className="h-4 w-4 text-orange-500/60" />
                  {business.phone}
                </a>
                {business.address && (
                  <div className="flex items-start gap-2">
                    <MapPin className="h-4 w-4 text-orange-500/60 flex-shrink-0 mt-0.5" />
                    <span>{business.address}</span>
                  </div>
                )}
                {business.website_url && (
                  <a
                    href={business.website_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 hover:text-orange-300 transition-colors"
                  >
                    <Globe className="h-4 w-4 text-orange-500/60" />
                    Website
                  </a>
                )}
              </div>
              <p className="mt-4 text-xs text-orange-400/70 font-semibold uppercase tracking-wider">
                Licensed, Bonded &amp; Insured
              </p>
            </div>

            {/* Navigation */}
            <div>
              <h4 className="text-white font-semibold text-sm mb-4 uppercase tracking-wider">
                Quick Navigation
              </h4>
              <ul className="space-y-2 text-sm text-slate-400">
                {SECTION_ANCHORS.map((anchor) => (
                  <li key={anchor.id}>
                    <a
                      href={`#${anchor.id}`}
                      className="hover:text-orange-300 transition-colors"
                    >
                      {anchor.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Services */}
            <div>
              <h4 className="text-white font-semibold text-sm mb-4 uppercase tracking-wider">
                Services
              </h4>
              <ul className="space-y-2 text-sm text-slate-400">
                {content.services.slice(0, 6).map((s, i) => (
                  <li key={i}>{s.title}</li>
                ))}
              </ul>
            </div>

            {/* Service Areas */}
            <div>
              <h4 className="text-white font-semibold text-sm mb-4 uppercase tracking-wider">
                Service Areas
              </h4>
              <ul className="space-y-2 text-sm text-slate-400">
                {content.aeo_signals.area_served.map((area, i) => (
                  <li key={i}>{area}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-12 pt-6 border-t border-slate-800 text-center text-xs text-slate-600">
            &copy; {currentYear} {business.business_name}. All rights reserved.
            Built by{" "}
            <a
              href="https://reliantai.org"
              className="text-slate-500 hover:text-orange-400 transition-colors"
            >
              ReliantAI
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
