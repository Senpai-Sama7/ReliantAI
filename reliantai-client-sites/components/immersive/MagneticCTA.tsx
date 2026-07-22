"use client";

import { useRef, type ReactNode, type MouseEvent } from "react";

interface MagneticCTAProps {
  href: string;
  children: ReactNode;
  className?: string;
  strength?: number;
}

/**
 * Pointer-tracking magnetic CTA — desktop only.
 * Respects reduced motion; phones get the plain link.
 */
export default function MagneticCTA({
  href,
  children,
  className = "btn-trade",
  strength = 0.35,
}: MagneticCTAProps) {
  const ref = useRef<HTMLAnchorElement>(null);

  const onMove = (e: MouseEvent<HTMLAnchorElement>) => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (window.matchMedia("(max-width: 639px)").matches) return;
    const rect = el.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    el.style.transform = `translate3d(${x * strength}px, ${y * strength}px, 0)`;
  };

  const onLeave = () => {
    const el = ref.current;
    if (!el) return;
    el.style.transform = "translate3d(0,0,0)";
  };

  return (
    <a
      ref={ref}
      href={href}
      className={`magnetic-cta ${className}`}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
    >
      {children}
    </a>
  );
}
