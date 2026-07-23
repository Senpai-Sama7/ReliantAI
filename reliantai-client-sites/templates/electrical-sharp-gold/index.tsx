import type { SiteContent } from "@/types/SiteContent";
import ImmersiveTemplate from "@/components/immersive/ImmersiveTemplate";
import Footer from "./sections/Footer";

export default function ElectricalTemplate({ content }: { content: SiteContent }) {
  return (
    <ImmersiveTemplate
      content={content}
      scene="circuit-load"
      tradeAttr="electrical"
      contactTagline="Licensed · NEC compliant"
      ctaColor="gold"
    >
      <Footer content={content} />
    </ImmersiveTemplate>
  );
}
