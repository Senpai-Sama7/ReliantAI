import type { SiteContent } from "@/types/SiteContent";
import { TRADE_COPY } from "@/lib/trade-copy";
import ContactBar from "./sections/ContactBar";
import TrustBanner from "@/components/shared/TrustBanner";
import Hero from "./sections/Hero";
import StatsBar from "@/components/shared/StatsBar";
import SectionDivider from "@/components/shared/SectionDivider";
import Services from "./sections/Services";
import CTASection from "@/components/shared/CTASection";
import About from "./sections/About";
import Reviews from "./sections/Reviews";
import FAQ from "./sections/FAQ";
import Footer from "./sections/Footer";

export default function ElectricalTemplate({ content }: { content: SiteContent }) {
  const copy = TRADE_COPY[content.site_config.trade] || TRADE_COPY.electrical;

  return (
    <div data-trade="electrical" className="bg-[var(--trade-ink)] text-white">
      <ContactBar content={content} />
      <Hero content={content} />
      <TrustBanner trade={content.site_config.trade} />
      <StatsBar content={content} accent="gold" />
      <SectionDivider variant="dots" />
      <div id="services">
        <Services content={content} copy={copy} />
      </div>
      <CTASection content={content} color="gold" variant="urgency" />
      <SectionDivider variant="line" />
      <div id="about">
        <About content={content} copy={copy} />
      </div>
      <SectionDivider />
      <div id="reviews">
        <Reviews content={content} />
      </div>
      <CTASection content={content} color="gold" variant="estimate" />
      <SectionDivider variant="wave" />
      <div id="faq">
        <FAQ content={content} />
      </div>
      <Footer content={content} />
    </div>
  );
}
