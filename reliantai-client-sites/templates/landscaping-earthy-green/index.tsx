import type { SiteContent } from "@/types/SiteContent";
import ImmersiveTemplate from "@/components/immersive/ImmersiveTemplate";
import Footer from "./sections/Footer";

export default function LandscapingTemplate({ content }: { content: SiteContent }) {
  return (
    <ImmersiveTemplate
      content={content}
      scene="site-plan"
      tradeAttr="landscaping"
      contactTagline="Design · Hardscape · Care"
      ctaColor="moss"
    >
      <Footer content={content} />
    </ImmersiveTemplate>
  );
}
