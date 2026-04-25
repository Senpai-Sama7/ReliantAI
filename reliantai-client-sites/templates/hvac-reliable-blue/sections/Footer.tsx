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
      <div className="pb-24 sm:pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            <div>
              <h3 className="text-white font-semibold text-lg mb-3">
                {business.business_name}
              </h3>
              <div className="space-y-2 text-sm text-slate-400">
                <a
                  href={`tel:${business.phone}`}
                  className="flex items-center gap-2 hover:text-blue-300 transition-colors"
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
              <p className="mt-4 text-xs text-slate-500">
                Licensed, Bonded & Insured
              </p>
            </div>

            <div>
              <h4 className="text-white font-semibold text-sm mb-3">
                Services
              </h4>
              <ul className="space-y-1 text-sm text-slate-400">
                {content.services.slice(0, 6).map((s, i) => (
                  <li key={i}>{s.title}</li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="text-white font-semibold text-sm mb-3">
                Quick Links
              </h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><a href="#services" className="hover:text-blue-300 transition-colors">Our Services</a></li>
                <li><a href="#about" className="hover:text-blue-300 transition-colors">About Us</a></li>
                <li><a href="#reviews" className="hover:text-blue-300 transition-colors">Reviews</a></li>
                <li><a href="#faq" className="hover:text-blue-300 transition-colors">FAQ</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-white font-semibold text-sm mb-3">
                Service Areas
              </h4>
              <ul className="space-y-1 text-sm text-slate-400">
                {content.aeo_signals?.area_served?.map((area, i) => (
                  <li key={i}>{area}</li>
                )) ?? <li className="text-slate-600">{business.city}, {business.state}</li>}
              </ul>
            </div>
          </div>

          <div className="mt-10 pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-[11px] text-slate-600">
              &copy; {currentYear} {business.business_name}
            </p>
            <a
              href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(business.business_name + " " + business.city)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-xs text-slate-500 hover:text-blue-400 transition-colors"
              aria-label="Find us on Google"
            >
              <Globe className="h-4 w-4" />
              Find us on Google
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}