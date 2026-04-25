import { Phone, MapPin, Globe } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface FooterProps {
  content: SiteContent;
}

export default function Footer({ content }: FooterProps) {
  const { business } = content;
  const currentYear = new Date().getFullYear();

  const navLinks = [
    { label: "Services", href: "#services" },
    { label: "About", href: "#about" },
    { label: "Reviews", href: "#reviews" },
    { label: "FAQ", href: "#faq" },
  ];

  return (
    <footer id="contact" className="border-t border-slate-800 bg-slate-950">
      <div className="pb-24 sm:pb-20">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <h3 className="mb-3 text-lg font-semibold text-white">{business.business_name}</h3>
              <div className="space-y-2 text-sm text-slate-400">
                <a
                  href={`tel:${business.phone}`}
                  className="flex items-center gap-2 transition-colors hover:text-amber-300"
                >
                  <Phone className="h-4 w-4" />
                  {business.phone}
                </a>
                {business.address && (
                  <div className="flex items-start gap-2">
                    <MapPin className="mt-0.5 h-4 w-4 flex-shrink-0" />
                    <span>{business.address}</span>
                  </div>
                )}
              </div>
              <p className="mt-4 text-xs font-medium text-amber-400/80">
                Licensed, Bonded & Insured
              </p>
            </div>

            <div>
              <h4 className="mb-3 text-sm font-semibold text-white">Quick Nav</h4>
              <ul className="space-y-1.5 text-sm text-slate-400">
                {navLinks.map((link) => (
                  <li key={link.href}>
                    <a href={link.href} className="transition-colors hover:text-amber-300">
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="mb-3 text-sm font-semibold text-white">Services</h4>
              <ul className="space-y-1 text-sm text-slate-400">
                {content.services.slice(0, 6).map((s, i) => (
                  <li key={i}>{s.title}</li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="mb-3 text-sm font-semibold text-white">Service Areas</h4>
              <ul className="space-y-1 text-sm text-slate-400">
                {(content.aeo_signals?.area_served ?? []).map((area, i) => (
                  <li key={i}>{area}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-8 flex items-center gap-4">
            {business.website_url && (
              <a
                href={business.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="transition-colors hover:text-amber-300 text-slate-400"
                aria-label="Website"
              >
                <Globe className="h-5 w-5" />
              </a>
            )}
          </div>

          <div className="mt-10 border-t border-slate-800 pt-6 text-center text-xs text-slate-600">
            &copy; {currentYear} {business.business_name}. All rights reserved. · Licensed, Bonded
            & Insured
            <br />
            Built by{" "}
            <a
              href="https://reliantai.org"
              className="transition-colors text-slate-500 hover:text-amber-400"
            >
              ReliantAI
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}