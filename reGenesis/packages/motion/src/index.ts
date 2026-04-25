
import { motion, type Variants, useInView } from "framer-motion";
import gsap from "gsap";
import ScrollTrigger from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export function reduce(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function reveal(el: Element, variant: "fade"|"rise"="fade"){
  if (typeof window === "undefined" || reduce()) return;
  const base: any = { opacity: 0, y: variant === "rise" ? 12 : 0 };
  const to: any = { opacity: 1, y: 0, duration: 0.6, ease: "power2.out" };
  gsap.fromTo(el, base, to);
}

export function parallax(el: Element, factor = 0.2){
  if (typeof window === "undefined" || reduce()) return;
  gsap.to(el, { yPercent: -factor*100, ease: "none", scrollTrigger: { trigger: el, scrub: true } });
}

export function scrollPin(tl: gsap.core.Timeline | null, opts: { start?: string; end?: string; scrub?: boolean|number; pin?: Element|boolean } = {}){
  if (typeof window === "undefined" || reduce()) return;
  ScrollTrigger.create({ animation: tl || undefined, start: opts.start ?? "top top", end: opts.end ?? "bottom top", scrub: opts.scrub ?? true, pin: opts.pin ?? true });
}

export { motion, useInView };
