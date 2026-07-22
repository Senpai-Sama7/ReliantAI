import type { SiteContent } from "@/types/SiteContent";
import BrandHero from "@/components/shared/BrandHero";

export default function Hero({ content }: { content: SiteContent }) {
  return <BrandHero content={content} signature="gallery" light />;
}
