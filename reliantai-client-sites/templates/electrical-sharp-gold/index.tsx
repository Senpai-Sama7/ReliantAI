import type { SiteContent } from "@/types/SiteContent";
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
  return (
    <>
      <ContactBar content={content} />
      <TrustBanner trade={content.site_config.trade} />
      <Hero content={content} />
      <StatsBar content={content} accent="amber-400" />
      <SectionDivider variant="dots" />
      <Services content={content} />
      <CTASection content={content} color="amber" variant="urgency" />
      <SectionDivider variant="line" />
      <About content={content} />
      <SectionDivider />
      <Reviews content={content} />
      <CTASection content={content} color="amber" variant="estimate" />
      <SectionDivider variant="wave" />
      <FAQ content={content} />
      <Footer content={content} />
    </>
  );
}
