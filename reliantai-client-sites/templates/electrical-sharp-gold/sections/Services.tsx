import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import EditorialServices from "@/components/shared/EditorialServices";

export default function Services({ content, copy }: { content: SiteContent; copy: TradeCopy }) {
  return <EditorialServices content={content} copy={copy} />;
}
