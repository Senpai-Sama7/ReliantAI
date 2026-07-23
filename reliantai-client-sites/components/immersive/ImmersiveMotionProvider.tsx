"use client";

import { useEffect, type ReactNode } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useGSAP } from "@gsap/react";
import Lenis from "lenis";
import { allowCinematicScroll } from "@/lib/immersive";

gsap.registerPlugin(ScrollTrigger, useGSAP);

interface ImmersiveMotionProviderProps {
  children: ReactNode;
}

/**
 * One GSAP registration + optional Lenis (desktop, reduced-motion off).
 * Mobile / coarse pointers keep native scroll — no smash, no jank.
 */
export default function ImmersiveMotionProvider({ children }: ImmersiveMotionProviderProps) {
  useEffect(() => {
    if (!allowCinematicScroll()) {
      document.documentElement.classList.remove("lenis");
      return;
    }

    const lenis = new Lenis({
      duration: 1.05,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
      touchMultiplier: 1.4,
    });

    document.documentElement.classList.add("lenis");
    document.documentElement.style.scrollBehavior = "auto";

    lenis.on("scroll", ScrollTrigger.update);

    const ticker = (time: number) => {
      lenis.raf(time * 1000);
    };
    gsap.ticker.add(ticker);
    gsap.ticker.lagSmoothing(0);

    const onResize = () => ScrollTrigger.refresh();
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      gsap.ticker.remove(ticker);
      lenis.destroy();
      document.documentElement.classList.remove("lenis");
      document.documentElement.style.scrollBehavior = "";
      ScrollTrigger.getAll().forEach((t) => t.kill());
    };
  }, []);

  return <>{children}</>;
}
