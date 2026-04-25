import tokens from "./tokens.json";

export const colors = tokens.colors;
export const typography = tokens.typography;
export const spacing = tokens.spacing;
export const breakpoints = tokens.breakpoints;
export const shadows = tokens.shadows;
export const radius = tokens.radius;

export function getColor(color: string): string {
  return tokens.colors[color as keyof typeof tokens.colors] || color;
}

export function getFont(font: "display" | "text"): string {
  return tokens.typography[font].family;
}

export function getSpacing(size: string): string {
  return tokens.spacing[size as keyof typeof tokens.spacing] || size;
}

export function getBreakpoint(name: string): number {
  return tokens.breakpoints[name as keyof typeof tokens.breakpoints] || 0;
}

export const theme = tokens;
export default tokens;