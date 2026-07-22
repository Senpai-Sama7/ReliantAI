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

export default function LandscapingTemplate({ content }: { content: SiteContent }) {
  const copy = TRADE_COPY[content.site_config.trade] || TRADE_COPY.landscaping;

  return (
    <div data-trade="landscaping" className="bg-[var(--trade-ink)] text-white">
      <ContactBar content={content} />
      <Hero content={content} />
      <TrustBanner trade="landscaping" />
      <StatsBar content={content} accent="moss" />
      <SectionDivider variant="dots" />
      <div id="services">
        <Services content={content} copy={copy} />
      </div>
      <CTASection content={content} color="moss" variant="urgency" />
      <SectionDivider variant="line" />
      <div id="about">
        <About content={content} copy={copy} />
      </div>
      <SectionDivider />
      <div id="reviews">
        <Reviews content={content} copy={copy} />
      </div>
      <CTASection content={content} color="moss" variant="estimate" />
      <SectionDivider variant="wave" />
      <div id="faq">
        <FAQ content={content} copy={copy} />
      </div>
      <Footer content={content} />
    </div>
  );
}