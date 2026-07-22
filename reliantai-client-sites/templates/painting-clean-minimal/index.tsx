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

export default function PaintingTemplate({ content }: { content: SiteContent }) {
  const copy = TRADE_COPY[content.site_config.trade] || TRADE_COPY.painting;

  return (
    <div data-trade="painting" className="template-shell bg-[var(--trade-surface)] text-[var(--trade-ink)]">
      <ContactBar content={content} light tagline="Free color consultation" />
      <BrandHero content={content} signature="gallery" light />
      <TrustBanner trade={content.site_config.trade} light />
      <StatsBar content={content} accent="ochre" light />
      <SectionDivider variant="dots" light />
      <div id="services">
        <EditorialServices content={content} copy={copy} light />
      </div>
      <CTASection content={content} color="ochre" variant="urgency" light />
      <div id="about">
        <About content={content} copy={copy} />
      </div>
      <SectionDivider variant="line" light />
      <div id="reviews">
        <Reviews content={content} copy={copy} />
      </div>
      <CTASection content={content} color="ochre" variant="estimate" light />
      <SectionDivider variant="wave" light />
      <div id="faq">
        <FAQ content={content} copy={copy} />
      </div>
      <Footer content={content} />
      <MobileCallBar content={content} />
    </div>
  );
}
