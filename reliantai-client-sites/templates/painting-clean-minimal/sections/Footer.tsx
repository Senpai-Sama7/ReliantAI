import { Globe, Phone, MapPin } from "lucide-react";
import type { SiteContent } from "@/types/SiteContent";

interface FooterProps {
  content: SiteContent;
}

export default function Footer({ content }: FooterProps) {
  const { business } = content;
  const currentYear = new Date().getFullYear();

  return (
    <footer id="contact" className="bg-stone-900 border-t border-stone-800">
      <div className="pb-24 sm:pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            <div>
              <h3 className="text-white font-semibold text-lg mb-3">
                {business.business_name}
              </h3>
              <div className="mb-3 flex items-center gap-2 text-violet-400 text-sm font-medium">
                <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
                </svg>
                Licensed, Bonded &amp; Insured
              </div>
              <div className="space-y-2 text-sm text-stone-400">
                <a
                  href={`tel:${business.phone}`}
                  className="flex items-center gap-2 hover:text-violet-400 transition-colors"
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
            </div>

            <div>
              <h4 className="text-white font-semibold text-sm mb-3">
                Quick Links
              </h4>
              <ul className="space-y-1 text-sm text-stone-400">
                <li><a href="#services" className="hover:text-violet-400 transition-colors">Services</a></li>
                <li><a href="#about" className="hover:text-violet-400 transition-colors">About Us</a></li>
                <li><a href="#reviews" className="hover:text-violet-400 transition-colors">Reviews</a></li>
                <li><a href="#faq" className="hover:text-violet-400 transition-colors">FAQ</a></li>
                <li><a href="#contact" className="hover:text-violet-400 transition-colors">Contact</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-white font-semibold text-sm mb-3">
                Service Areas
              </h4>
              <ul className="space-y-1 text-sm text-stone-400">
                {content.aeo_signals.area_served.map((area, i) => (
                  <li key={i}>{area}</li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="text-white font-semibold text-sm mb-3">
                Visit Us
              </h4>
              {business.website_url && (
                <a
                  href={business.website_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-stone-400 hover:text-violet-400 transition-colors"
                  aria-label="Website"
                >
                  <Globe className="h-5 w-5" />
                  <span className="text-sm">Website</span>
                </a>
              )}
            </div>
          </div>

          <div className="mt-10 pt-6 border-t border-stone-800 text-center text-xs text-stone-600">
            &copy; {currentYear} {business.business_name}. All rights reserved.
            Built by{" "}
            <a
              href="https://reliantai.org"
              className="text-stone-500 hover:text-violet-400 transition-colors"
            >
              ReliantAI
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
