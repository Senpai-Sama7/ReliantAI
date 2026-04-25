import Ajv from "ajv";
import brandBriefSchema from "../brand-brief.schema.json";

export type Voice = "calm" | "energetic" | "premium" | "playful" | "tech";
export type Density = "compact" | "comfortable" | "spacious";
export type Personality = "subtle" | "standard" | "expressive";
export type Intent = "hero" | "feature-grid" | "scrollytelling" | "testimonial" | "cta";

export interface BrandIdentityColors {
  bg: string;
  fg: string;
  accent: string;
  muted: string;
}

export interface BrandIdentityTypography {
  display: {
    family: string;
    weight?: number;
  };
  text: {
    family: string;
    weight?: number;
  };
}

export interface BrandIdentity {
  colors: BrandIdentityColors;
  typography: BrandIdentityTypography;
  density: Density;
}

export interface BrandIdentity {
  colors: BrandIdentityColors;
  typography: BrandIdentityTypography;
  density: Density;
}

export interface BrandVoice {
  name: string;
  voice: Voice;
}

export interface Brand {
  name: string;
  voice: Voice;
}

export interface Motion {
  personality: Personality;
}

export interface ContentModelItem {
  intent: Intent;
  payload: Record<string, unknown>;
}

export interface BrandBrief {
  brand: Brand;
  identity: BrandIdentity;
  motion: Motion;
  contentModel: ContentModelItem[];
}

export interface ValidationResult {
  valid: boolean;
  errors?: Ajv.ErrorObject[];
}

const ajv = new Ajv({ allErrors: true, verbose: true });
const validate = ajv.compile(brandBriefSchema);

export function validateBrandBrief(data: unknown): ValidationResult {
  const valid = validate(data);
  if (valid) {
    return { valid: true };
  }
  return {
    valid: false,
    errors: validate.errors || undefined,
  };
}

export function createBrandBrief(partial: Partial<BrandBrief>): BrandBrief {
  return {
    brand: {
      name: partial.brand?.name || "My Brand",
      voice: partial.brand?.voice || "calm",
    },
    identity: {
      colors: {
        bg: partial.identity?.colors?.bg || "#ffffff",
        fg: partial.identity?.colors?.fg || "#000000",
        accent: partial.identity?.colors?.accent || "#3b82f6",
        muted: partial.identity?.colors?.muted || "#6b7280",
      },
      typography: {
        display: {
          family: partial.identity?.typography?.display?.family || "Inter",
          weight: partial.identity?.typography?.display?.weight || 700,
        },
        text: {
          family: partial.identity?.typography?.text?.family || "Inter",
          weight: partial.identity?.typography?.text?.weight || 400,
        },
      },
      density: partial.identity?.density || "comfortable",
    },
    motion: {
      personality: partial.motion?.personality || "standard",
    },
    contentModel: partial.contentModel || [],
  };
}

export function brandBriefToCSS(brief: BrandBrief): Record<string, string> {
  const { colors, typography, density } = brief.identity;
  
  const spacingMap: Record<Density, string> = {
    compact: "0.5rem",
    comfortable: "1rem",
    spacious: "2rem",
  };

  return {
    "--regen-bg": colors.bg,
    "--regen-fg": colors.fg,
    "--regen-accent": colors.accent,
    "--regen-muted": colors.muted,
    "--regen-font-display": typography.display.family,
    "--regen-font-display-weight": String(typography.display.weight),
    "--regen-font-text": typography.text.family,
    "--regen-font-text-weight": String(typography.text.weight),
    "--regen-spacing": spacingMap[density],
  };
}