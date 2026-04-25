
import Lenis from "@studio-freight/lenis";
import gsap from "gsap";
import ScrollTrigger from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export function reduced(){
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function initLenis(opts: { smooth?: boolean; duration?: number } = {}){
  if (typeof window === "undefined" || reduced()) return null;
  const lenis = new Lenis({ duration: Math.max(0.6, Math.min(2, (opts.duration ?? 1.2))), smooth: opts.smooth ?? true } as any);
  function raf(time: number){ lenis.raf(time); requestAnimationFrame(raf); }
  requestAnimationFrame(raf);
  return lenis;
}

export function syncWithScrollTrigger(lenis: any | null){
  if (typeof window === "undefined" || !lenis) return;
  lenis.on("scroll", ScrollTrigger.update);
  ScrollTrigger.addEventListener("refresh", () => lenis.update());
  ScrollTrigger.refresh();
}
