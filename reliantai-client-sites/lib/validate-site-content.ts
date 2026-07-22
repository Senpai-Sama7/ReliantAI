import type { SiteContent } from "@/types/SiteContent";
import { sanitizeHttpUrl } from "@/lib/safe-url";
import { isValidSlug } from "@/lib/slug";
import { isTemplateId } from "@/lib/templates";

/** Statuses the public ISR pipeline is allowed to render. */
export const PUBLIC_SITE_STATUSES = new Set([
  "preview_live",
  "live",
  "published",
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
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

function hasRequiredBusinessFields(business: Record<string, unknown>): boolean {
  return (
    isNonEmptyString(business.business_name) &&
    isNonEmptyString(business.city) &&
    isNonEmptyString(business.state) &&
    isNonEmptyString(business.phone) &&
    isNonEmptyString(business.trade)
  );
}

function hasRequiredHeroFields(hero: Record<string, unknown>): boolean {
  return isNonEmptyString(hero.headline);
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
  if (!isNonEmptyString(payload.status)) return null;
  if (!PUBLIC_SITE_STATUSES.has(payload.status)) return null;
  if (!hasRequiredBusinessFields(payload.business)) return null;
  if (!hasRequiredHeroFields(payload.hero)) return null;

  stripUnsafeBusinessUrls(payload.business);

  return payload as unknown as SiteContent;
}
