import type { SiteContent } from "@/types/SiteContent";
import { TRADE_COPY } from "@/lib/trade-copy";
import ContactBar from "@/components/shared/ContactBar";
import TrustBanner from "@/components/shared/TrustBanner";
import BrandHero from "@/components/shared/BrandHero";
import StatsBar from "@/components/shared/StatsBar";
import EditorialServices from "@/components/shared/EditorialServices";
import CTASection from "@/components/shared/CTASection";
import About from "./sections/About";
import Reviews from "./sections/Reviews";
import FAQ from "./sections/FAQ";
import Footer from "./sections/Footer";
import SectionDivider from "@/components/shared/SectionDivider";
import MobileCallBar from "@/components/shared/MobileCallBar";

export default function LandscapingTemplate({ content }: { content: SiteContent }) {
  const copy = TRADE_COPY[content.site_config.trade] || TRADE_COPY.landscaping;

  return (
    <div data-trade="landscaping" className="template-shell bg-[var(--trade-ink)] text-white">
      <ContactBar content={content} tagline="Free landscape estimate" />
      <BrandHero content={content} signature="moss-organic" />
      <TrustBanner trade={content.site_config.trade} />
      <StatsBar content={content} accent="moss" />
      <SectionDivider variant="dots" />
      <div id="services">
        <EditorialServices content={content} copy={copy} />
      </div>
      <CTASection content={content} color="moss" variant="urgency" />
      <div id="about">
        <About content={content} copy={copy} />
      </div>
      <SectionDivider variant="line" />
      <div id="reviews">
        <Reviews content={content} copy={copy} />
      </div>
      <CTASection content={content} color="moss" variant="estimate" />
      <SectionDivider variant="wave" />
      <div id="faq">
        <FAQ content={content} copy={copy} />
      </div>
      <Footer content={content} />
      <MobileCallBar content={content} />
    </div>
  );
}
