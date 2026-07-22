import type { SiteContent } from "@/types/SiteContent";
import { isValidSlug } from "@/lib/slug";
import { loadTemplate, type TemplateComponent } from "@/lib/templates";
import { parseSiteContent } from "@/lib/validate-site-content";

const API_URL =
  process.env.API_BASE_URL ||
  process.env.PLATFORM_API_URL ||
  "http://localhost:8000";

const DEFAULT_API_TIMEOUT_MS = 10_000;

function resolveTimeoutMs(raw: string | undefined): number {
  if (raw === undefined || raw === "") return DEFAULT_API_TIMEOUT_MS;
  const parsed = Number(raw);
  // Blank/non-numeric values become 0/NaN: AbortSignal.timeout(0) aborts
  // instantly and timeout(NaN) throws, turning every slug into a 404.
  if (!Number.isFinite(parsed) || parsed <= 0) {
    console.warn(
      `[API] Ignoring invalid API_TIMEOUT_MS=${JSON.stringify(raw)}; using ${DEFAULT_API_TIMEOUT_MS}ms`
    );
    return DEFAULT_API_TIMEOUT_MS;
  }
  return parsed;
}

const API_TIMEOUT_MS = resolveTimeoutMs(process.env.API_TIMEOUT_MS);

/**
 * Distinguishes permanent misses from transient upstream failures.
 * Callers must throw on `upstream_error` so Next.js does NOT ISR-cache a 404
 * for a temporary API outage (revalidate=3600 would pin that 404 for an hour).
 */
export type SiteContentResult =
  | { status: "ok"; content: SiteContent }
  | { status: "not_found" }
  | { status: "upstream_error"; cause: unknown };

export async function fetchSiteContent(
  slug: string
): Promise<SiteContentResult> {
  if (!isValidSlug(slug)) {
    console.warn(`[API] Rejected invalid slug format: ${JSON.stringify(slug)}`);
    return { status: "not_found" };
  }
  try {
    const res = await fetch(
      `${API_URL}/api/v2/generated-sites/${encodeURIComponent(slug)}`,
      {
        // Note: This endpoint is public (no auth required) per AGENTS.md
        next: { revalidate: 3600 },
        signal: AbortSignal.timeout(API_TIMEOUT_MS),
      }
    );
    if (res.status === 404 || res.status === 400) {
      console.error(
        `[API] Site not available: ${res.status} for slug: ${slug}`
      );
      return { status: "not_found" };
    }
    if (!res.ok) {
      const cause = new Error(`Upstream HTTP ${res.status} for slug: ${slug}`);
      console.error(`[API] ${cause.message}`);
      return { status: "upstream_error", cause };
    }
    const payload: unknown = await res.json();
    const content = parseSiteContent(payload);
    if (!content) {
      console.error(`[API] Invalid site content shape for slug: ${slug}`);
      // Malformed payload is treated as a permanent miss — do not thrash retries.
      return { status: "not_found" };
    }
    return { status: "ok", content };
  } catch (error) {
    console.error(`[API] Error fetching site content for ${slug}:`, error);
    return { status: "upstream_error", cause: error };
  }
}

/**
 * Resolve site content for rendering. Throws on transient upstream failures
 * so ISR does not cache a 404 for an hour.
 */
export async function getSiteContent(
  slug: string
): Promise<SiteContent | null> {
  const result = await fetchSiteContent(slug);
  if (result.status === "ok") return result.content;
  if (result.status === "not_found") return null;
  throw result.cause instanceof Error
    ? result.cause
    : new Error(`Upstream API unavailable for slug: ${slug}`);
}

export async function getTemplate(
  templateId: string
): Promise<TemplateComponent | null> {
  return loadTemplate(templateId);
}
