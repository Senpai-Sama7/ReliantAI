import type { SiteContent } from "@/types/SiteContent";
import ImmersiveTemplate from "@/components/immersive/ImmersiveTemplate";
import Footer from "./sections/Footer";

export default function PaintingTemplate({ content }: { content: SiteContent }) {
  return (
    <ImmersiveTemplate
      content={content}
      scene="finish-wipe"
      tradeAttr="painting"
      light
      contactTagline="Free color consultation"
      ctaColor="ochre"
    >
      <Footer content={content} />
    </ImmersiveTemplate>
  );
}
