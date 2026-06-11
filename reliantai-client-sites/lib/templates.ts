import type { ComponentType } from "react";
import type { SiteContent } from "@/types/SiteContent";

export const TEMPLATE_IDS = [
  "hvac-reliable-blue",
  "plumbing-trustworthy-navy",
  "electrical-sharp-gold",
  "roofing-bold-copper",
  "painting-clean-minimal",
  "landscaping-earthy-green",
] as const;

export type TemplateId = (typeof TEMPLATE_IDS)[number];

export type TemplateComponent = ComponentType<{ content: SiteContent }>;

type TemplateModule = { default: TemplateComponent };

export const templateImports: Record<
  TemplateId,
  () => Promise<TemplateModule>
> = {
  "hvac-reliable-blue": () => import("@/templates/hvac-reliable-blue"),
  "plumbing-trustworthy-navy": () =>
    import("@/templates/plumbing-trustworthy-navy"),
  "electrical-sharp-gold": () => import("@/templates/electrical-sharp-gold"),
  "roofing-bold-copper": () => import("@/templates/roofing-bold-copper"),
  "painting-clean-minimal": () => import("@/templates/painting-clean-minimal"),
  "landscaping-earthy-green": () =>
    import("@/templates/landscaping-earthy-green"),
};

export function isTemplateId(value: string): value is TemplateId {
  return (TEMPLATE_IDS as readonly string[]).includes(value);
}

export async function loadTemplate(
  templateId: string
): Promise<TemplateComponent | null> {
  if (!isTemplateId(templateId)) return null;
  const mod = await templateImports[templateId]();
  return mod.default;
}
