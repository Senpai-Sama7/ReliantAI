import type { SiteContent } from "@/types/SiteContent";
import { TRADE_COPY } from "@/lib/trade-copy";
import ContactBar from "./sections/ContactBar";
import TrustBanner from "@/components/shared/TrustBanner";
import Hero from "./sections/Hero";
import StatsBar from "@/components/shared/StatsBar";
import Services from "./sections/Services";
import CTASection from "@/components/shared/CTASection";
import About from "./sections/About";
import Reviews from "./sections/Reviews";
import FAQ from "./sections/FAQ";
import Footer from "./sections/Footer";
import SectionDivider from "@/components/shared/SectionDivider";

export default function PaintingTemplate({ content }: { content: SiteContent }) {
  const copy = TRADE_COPY[content.site_config.trade] || TRADE_COPY.painting;

  return (
    <div data-trade="painting" className="bg-[var(--trade-surface)] text-[var(--trade-ink)]">
      <ContactBar content={content} />
      <Hero content={content} />
      <TrustBanner trade={content.site_config.trade} light={true} />
      <StatsBar content={content} accent="ochre" light={true} />
      <SectionDivider variant="dots" light={true} />
      <div id="services">
        <Services content={content} copy={copy} />
      </div>
      <CTASection content={content} color="ochre" variant="urgency" light={true} />
      <SectionDivider variant="line" light={true} />
      <div id="about">
        <About content={content} copy={copy} />
      </div>
      <SectionDivider light={true} />
      <div id="reviews">
        <Reviews content={content} copy={copy} />
      </div>
      <CTASection content={content} color="ochre" variant="estimate" light={true} />
      <SectionDivider variant="wave" light={true} />
      <div id="faq">
        <FAQ content={content} copy={copy} />
      </div>
      <Footer content={content} />
    </div>
  );
}