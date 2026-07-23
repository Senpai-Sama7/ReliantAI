import type { SiteContent } from "@/types/SiteContent";
import ImmersiveTemplate from "@/components/immersive/ImmersiveTemplate";
import Footer from "./sections/Footer";

export default function PlumbingTemplate({ content }: { content: SiteContent }) {
  return (
    <ImmersiveTemplate
      content={content}
      scene="pressure-flow"
      tradeAttr="plumbing"
      badge="24/7 Emergency"
      contactTagline="24/7 emergency plumbing"
      ctaColor="copper"
    >
      <Footer content={content} />
    </ImmersiveTemplate>
  );
}
