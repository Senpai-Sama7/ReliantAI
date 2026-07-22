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

export default function HvacTemplate({ content }: { content: SiteContent }) {
  const copy = TRADE_COPY[content.site_config.trade] || TRADE_COPY.hvac;

  return (
    <div data-trade="hvac" className="bg-[var(--trade-ink)] text-white">
      <ContactBar content={content} />
      <Hero content={content} />
      <TrustBanner trade={content.site_config.trade} />
      <StatsBar content={content} accent="steel" />
      <SectionDivider variant="dots" />
      <div id="services">
        <Services content={content} copy={copy} />
      </div>
      <CTASection content={content} color="steel" variant="urgency" />
      <div id="about">
        <About content={content} copy={copy} />
      </div>
      <SectionDivider variant="line" />
      <div id="reviews">
        <Reviews content={content} copy={copy} />
      </div>
      <CTASection content={content} color="steel" variant="estimate" />
      <SectionDivider variant="wave" />
      <div id="faq">
        <FAQ content={content} copy={copy} />
      </div>
      <Footer content={content} />
    </div>
  );
}
