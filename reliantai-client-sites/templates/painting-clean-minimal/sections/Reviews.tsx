import type { SiteContent } from "@/types/SiteContent";
import type { TradeCopy } from "@/lib/trade-copy";
import CraftReviews from "@/components/shared/CraftReviews";

export default function Reviews({ content, copy }: { content: SiteContent; copy: TradeCopy }) {
  return <CraftReviews content={content} copy={copy} light />;
}
