import type { SiteContent } from "@/types/SiteContent";
import { sanitizeHttpUrl } from "@/lib/safe-url";
import { isValidSlug } from "@/lib/slug";
import { isTemplateId } from "@/lib/templates";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.length > 0;
}

function stripUnsafeBusinessUrls(business: Record<string, unknown>): void {
  if (!("website_url" in business)) return;
  const raw = business.website_url;
  if (raw === undefined || raw === null) return;
  const safe = sanitizeHttpUrl(typeof raw === "string" ? raw : null);
  if (safe) {
    business.website_url = safe;
  } else {
    delete business.website_url;
  }
}

export function parseSiteContent(payload: unknown): SiteContent | null {
  if (!isRecord(payload)) return null;
  if (!isRecord(payload.business) || !isRecord(payload.hero)) return null;
  if (!isRecord(payload.site_config)) return null;
  if (!isNonEmptyString(payload.site_config.template_id)) return null;
  if (!isTemplateId(payload.site_config.template_id)) return null;
  if (!isNonEmptyString(payload.slug)) return null;
  if (!isValidSlug(payload.slug)) return null;
  if (!Array.isArray(payload.services)) return null;
  if (!isRecord(payload.about)) return null;
  if (!isRecord(payload.reviews)) return null;
  if (!Array.isArray(payload.faq)) return null;

  stripUnsafeBusinessUrls(payload.business);

  return payload as unknown as SiteContent;
}
