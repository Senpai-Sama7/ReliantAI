/** Immersive T2 helpers — Lenis/GSAP flagship craft for trade templates. */

export type TradeScene =
  | "thermal-airflow"
  | "pressure-flow"
  | "circuit-load"
  | "roof-assembly"
  | "finish-wipe"
  | "site-plan";

export const TRADE_SCENE: Record<string, TradeScene> = {
  hvac: "thermal-airflow",
  plumbing: "pressure-flow",
  electrical: "circuit-load",
  roofing: "roof-assembly",
  painting: "finish-wipe",
  landscaping: "site-plan",
};

export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return true;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function isNarrowViewport(): boolean {
  if (typeof window === "undefined") return true;
  return window.matchMedia("(max-width: 639px)").matches;
}

/** Desktop cinematic only — phones keep native scroll + light reveals. */
export function allowCinematicScroll(): boolean {
  return !prefersReducedMotion() && !isNarrowViewport();
}

export const SCENE_LABEL: Record<TradeScene, string> = {
  "thermal-airflow": "Thermal path",
  "pressure-flow": "Pressure trace",
  "circuit-load": "Circuit map",
  "roof-assembly": "Assembly layers",
  "finish-wipe": "Finish stages",
  "site-plan": "Site plan",
};
