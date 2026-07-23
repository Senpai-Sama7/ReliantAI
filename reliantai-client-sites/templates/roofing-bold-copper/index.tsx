import type { SiteContent } from "@/types/SiteContent";
import ImmersiveTemplate from "@/components/immersive/ImmersiveTemplate";
import Footer from "./sections/Footer";

export default function RoofingTemplate({ content }: { content: SiteContent }) {
  return (
    <ImmersiveTemplate
      content={content}
      scene="roof-assembly"
      tradeAttr="roofing"
      contactTagline="Storm-ready roofing crews"
      ctaColor="copper"
    >
      <Footer content={content} />
    </ImmersiveTemplate>
  );
}
