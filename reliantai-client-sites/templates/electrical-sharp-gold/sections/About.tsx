import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import CraftAbout from "@/components/shared/CraftAbout";

export default function About({ content, copy }: { content: SiteContent; copy: TradeCopy }) {
  return <CraftAbout content={content} copy={copy} />;
}
