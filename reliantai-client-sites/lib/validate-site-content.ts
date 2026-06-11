import type { SiteContent } from "@/types/SiteContent";
import { isTemplateId } from "@/lib/templates";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.length > 0;
}

export function parseSiteContent(payload: unknown): SiteContent | null {
  if (!isRecord(payload)) return null;
  if (!isRecord(payload.business) || !isRecord(payload.hero)) return null;
  if (!isRecord(payload.site_config)) return null;
  if (!isNonEmptyString(payload.site_config.template_id)) return null;
  if (!isTemplateId(payload.site_config.template_id)) return null;
  if (!isNonEmptyString(payload.slug)) return null;
  if (!Array.isArray(payload.services)) return null;
  if (!isRecord(payload.about)) return null;
  if (!isRecord(payload.reviews)) return null;
  if (!Array.isArray(payload.faq)) return null;

  return payload as unknown as SiteContent;
}
