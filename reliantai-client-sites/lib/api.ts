import type { SiteContent } from "@/types/SiteContent";

const API_URL = process.env.PLATFORM_API_URL || "http://localhost:8000";

export async function getSiteContent(
  slug: string
): Promise<SiteContent | null> {
  try {
    const res = await fetch(
      `${API_URL}/api/v2/generated-sites/${slug}`,
      {
        // Note: This endpoint is public (no auth required) per AGENTS.md
        next: { revalidate: 3600 },
      }
    );
    if (!res.ok) {
      console.error(
        `[API] Failed to fetch site content: ${res.status} for slug: ${slug}`
      );
      return null;
    }
    return res.json();
  } catch (error) {
    console.error(`[API] Error fetching site content for ${slug}:`, error);
    return null;
  }
}

type TemplateComponent = React.ComponentType<{ content: SiteContent }>;

const templateImports: Record<string, () => Promise<{ default: TemplateComponent }>> = {
  "hvac-reliable-blue": () =>
    import("@/templates/hvac-reliable-blue"),
  "plumbing-trustworthy-navy": () =>
    import("@/templates/plumbing-trustworthy-navy"),
  "electrical-sharp-gold": () =>
    import("@/templates/electrical-sharp-gold"),
  "roofing-bold-copper": () =>
    import("@/templates/roofing-bold-copper"),
  "painting-clean-minimal": () =>
    import("@/templates/painting-clean-minimal"),
  "landscaping-earthy-green": () =>
    import("@/templates/landscaping-earthy-green"),
};

const fallbackTemplate = () => import("@/templates/hvac-reliable-blue");

export async function getTemplate(
  templateId: string
): Promise<TemplateComponent> {
  const loader = templateImports[templateId] || fallbackTemplate;
  const mod = await loader();
  return mod.default;
}
