import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import CraftFAQ from "@/components/shared/CraftFAQ";

export default function FAQ({ content, copy }: { content: SiteContent; copy: TradeCopy }) {
  return <CraftFAQ content={content} copy={copy} light />;
}
