import type { SiteContent } from "@/types/SiteContent";
import { isValidSlug } from "@/lib/slug";
import { loadTemplate, type TemplateComponent } from "@/lib/templates";
import { parseSiteContent } from "@/lib/validate-site-content";

const API_URL =
  process.env.API_BASE_URL ||
  process.env.PLATFORM_API_URL ||
  "http://localhost:8000";

const API_TIMEOUT_MS = Number(process.env.API_TIMEOUT_MS ?? 10_000);

export async function getSiteContent(
  slug: string
): Promise<SiteContent | null> {
  if (!isValidSlug(slug)) {
    console.warn(`[API] Rejected invalid slug format: ${JSON.stringify(slug)}`);
    return null;
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
    if (!res.ok) {
      console.error(
        `[API] Failed to fetch site content: ${res.status} for slug: ${slug}`
      );
      return null;
    }
    const payload: unknown = await res.json();
    const content = parseSiteContent(payload);
    if (!content) {
      console.error(`[API] Invalid site content shape for slug: ${slug}`);
      return null;
    }
    return content;
  } catch (error) {
    console.error(`[API] Error fetching site content for ${slug}:`, error);
    return null;
  }
}

export async function getTemplate(
  templateId: string
): Promise<TemplateComponent | null> {
  return loadTemplate(templateId);
}
