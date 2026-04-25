import { Phone, MapPin, Globe } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface FooterProps {
  content: SiteContent;
}

export default function Footer({ content }: FooterProps) {
  const { business } = content;
  const currentYear = new Date().getFullYear();
  const websiteUrl = business.website_url || "#";
  const areasServed = content.aeo_signals?.area_served ?? [];

  return (
    <footer id="footer" className="bg-slate-950 border-t border-slate-800">
      <div className="pb-24 sm:pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-14">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
            <div>
              <h3 className="text-white font-semibold text-lg mb-4 font-display">
                {business.business_name}
              </h3>
              <div className="space-y-2.5 text-sm text-slate-400">
                <a
                  href={`tel:${business.phone}`}
                  className="flex items-center gap-2 hover:text-blue-300 transition-colors"
                >
                  <Phone className="h-4 w-4 flex-shrink-0" />
                  {business.phone}
                </a>
                {business.address && (
                  <div className="flex items-start gap-2">
                    <MapPin className="h-4 w-4 flex-shrink-0 mt-0.5" />
                    <span>{business.address}</span>
                  </div>
                )}
                {websiteUrl !== "#" && (
                  <a
                    href={websiteUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 hover:text-blue-300 transition-colors"
                  >
                    <Globe className="h-4 w-4 flex-shrink-0" />
                    {websiteUrl.replace(/^https?:\/\//, "")}
                  </a>
                )}
              </div>
              <p className="mt-3 text-xs text-blue-400 font-medium">
                Licensed, Bonded & Insured
              </p>
            </div>

            <div>
              <h4 className="text-white font-semibold text-sm mb-4">
                Quick Navigation
              </h4>
              <ul className="space-y-1.5 text-sm text-slate-400">
                <li>
                  <a href="#services" className="hover:text-blue-300 transition-colors">
                    Services
                  </a>
                </li>
                <li>
                  <a href="#about" className="hover:text-blue-300 transition-colors">
                    About Us
                  </a>
                </li>
                <li>
                  <a href="#reviews" className="hover:text-blue-300 transition-colors">
                    Reviews
                  </a>
                </li>
                <li>
                  <a href="#faq" className="hover:text-blue-300 transition-colors">
                    FAQ
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="text-white font-semibold text-sm mb-4">
                Service Areas
              </h4>
              <ul className="space-y-1.5 text-sm text-slate-400">
                {areasServed.map((area, i) => (
                  <li key={i}>{area}</li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="text-white font-semibold text-sm mb-4 font-display">
                {business.business_name}
              </h4>
              <p className="text-slate-400 text-sm leading-relaxed">
                Professional plumbing services in {business.city}, {business.state}. Available 24/7 for emergency repairs.
              </p>
              {websiteUrl !== "#" && (
                <a
                  href={websiteUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-4 inline-flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                >
                  <Globe className="h-4 w-4" />
                  Visit Website
                </a>
              )}
            </div>
          </div>

          <div className="mt-12 pt-6 border-t border-slate-800 text-center text-xs text-slate-600">
            © {currentYear} {business.business_name}. All rights reserved. Built by{" "}
            <a
              href="https://reliantai.org"
              className="text-slate-500 hover:text-blue-400 transition-colors"
            >
              ReliantAI
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}