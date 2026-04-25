import { Phone, MapPin, Globe } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface FooterProps {
  content: SiteContent;
}

export default function Footer({ content }: FooterProps) {
  const { business } = content;
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-slate-950 border-t border-slate-800">
      {/* Lower banner for preview pages — enough space for PreviewBanner */}
      <div className="pb-24 sm:pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Business info */}
            <div>
              <h3 className="text-white font-semibold text-lg mb-3">
                {business.business_name}
              </h3>
              <div className="space-y-2 text-sm text-slate-400">
                <a
                  href={`tel:${business.phone}`}
                  className="flex items-center gap-2 hover:text-emerald-300 transition-colors"
                >
                  <Phone className="h-4 w-4" />
                  {business.phone}
                </a>
                {business.address && (
                  <div className="flex items-start gap-2">
                    <MapPin className="h-4 w-4 flex-shrink-0 mt-0.5" />
                    <span>{business.address}</span>
                  </div>
                )}
              </div>
              <p className="mt-4 text-xs text-emerald-400/80 font-medium">
                Licensed, Bonded &amp; Insured
              </p>
            </div>

            {/* Quick Nav */}
            <div>
              <h4 className="text-white font-semibold text-sm mb-3">
                Quick Links
              </h4>
              <ul className="space-y-1 text-sm text-slate-400">
                <li><a href="#services" className="hover:text-emerald-300 transition-colors">Services</a></li>
                <li><a href="#about" className="hover:text-emerald-300 transition-colors">About Us</a></li>
                <li><a href="#reviews" className="hover:text-emerald-300 transition-colors">Reviews</a></li>
                <li><a href="#faq" className="hover:text-emerald-300 transition-colors">FAQ</a></li>
              </ul>
            </div>

            {/* Service areas */}
            <div>
              <h4 className="text-white font-semibold text-sm mb-3">
                Service Areas
              </h4>
              <ul className="space-y-1 text-sm text-slate-400">
                {content.aeo_signals.area_served.map((area, i) => (
                  <li key={i}>{area}</li>
                ))}
              </ul>
            </div>

            {/* Social */}
            <div>
              <h4 className="text-white font-semibold text-sm mb-3">
                Follow Us
              </h4>
              <div className="flex gap-3">
                {business.website_url && (
                  <a
                    href={business.website_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-400 hover:text-emerald-300 transition-colors"
                    aria-label="Website"
                  >
                    <Globe className="h-5 w-5" />
                  </a>
                )}
              </div>
            </div>
          </div>

          <div className="mt-10 pt-6 border-t border-slate-800 text-center text-xs text-slate-600">
            &copy; {currentYear} {business.business_name}. All rights reserved.
            Built by{" "}
            <a
              href="https://reliantai.org"
              className="text-slate-500 hover:text-emerald-400 transition-colors"
            >
              ReliantAI
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
