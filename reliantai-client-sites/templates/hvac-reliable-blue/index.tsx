import type { SiteContent } from "@/types/SiteContent";
import ImmersiveTemplate from "@/components/immersive/ImmersiveTemplate";
import Footer from "./sections/Footer";

export default function HvacTemplate({ content }: { content: SiteContent }) {
  return (
    <ImmersiveTemplate
      content={content}
      scene="thermal-airflow"
      tradeAttr="hvac"
      contactTagline="24/7 emergency HVAC"
      ctaColor="steel"
    >
      <Footer content={content} />
    </ImmersiveTemplate>
  );
}
