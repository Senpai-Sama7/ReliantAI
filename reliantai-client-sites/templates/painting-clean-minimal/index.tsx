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
    <>
      <ContactBar content={content} />
      <TrustBanner trade={content.site_config.trade} light={true} />
      <Hero content={content} />
      <StatsBar content={content} accent="violet-600" light={true} />
      <SectionDivider variant="dots" light={true} />
      <div id="services">
        <Services content={content} copy={copy} />
      </div>
      <CTASection content={content} color="violet" variant="urgency" light={true} />
      <SectionDivider variant="line" light={true} />
      <div id="about">
        <About content={content} copy={copy} />
      </div>
      <SectionDivider light={true} />
      <div id="reviews">
        <Reviews content={content} copy={copy} />
      </div>
      <CTASection content={content} color="violet" variant="estimate" light={true} />
      <SectionDivider variant="wave" light={true} />
      <div id="faq">
        <FAQ content={content} copy={copy} />
      </div>
      <Footer content={content} />
    </>
  );
}