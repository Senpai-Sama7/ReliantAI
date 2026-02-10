import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

interface RevealOptions {
  y?: number;
  x?: number;
  scale?: number;
  opacity?: number;
  duration?: number;
  delay?: number;
  stagger?: number;
  ease?: string;
  start?: string;
  scrub?: boolean | number;
  markers?: boolean;
}

const defaultOptions: RevealOptions = {
  y: 40,
  opacity: 0,
  duration: 0.8,
  ease: 'power3.out',
  start: 'top 85%',
};

export const useScrollReveal = <T extends HTMLElement>(
  options: RevealOptions = {}
) => {
  const ref = useRef<T>(null);
  const triggersRef = useRef<ScrollTrigger[]>([]);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const opts = { ...defaultOptions, ...options };
    
    const ctx = gsap.context(() => {
      // Set initial state
      gsap.set(element, {
        y: opts.y,
        x: opts.x,
        scale: opts.scale,
        opacity: opts.opacity ?? 0,
      });

      // Create animation
      gsap.to(element, {
        y: 0,
        x: 0,
        scale: 1,
        opacity: 1,
        duration: opts.duration,
        delay: opts.delay,
        ease: opts.ease,
        scrollTrigger: {
          trigger: element,
          start: opts.start,
          scrub: opts.scrub,
          markers: opts.markers,
          toggleActions: opts.scrub ? undefined : 'play none none none',
          onEnter: (self) => {
            triggersRef.current.push(self);
          },
        },
      });
    }, element);

    return () => {
      ctx.revert();
      triggersRef.current.forEach(t => t.kill());
      triggersRef.current = [];
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return ref;
};

// Hook for staggered reveals of multiple child elements
export const useStaggerReveal = <T extends HTMLElement>(
  childSelector: string,
  options: RevealOptions = {}
) => {
  const containerRef = useRef<T>(null);
  const triggersRef = useRef<ScrollTrigger[]>([]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const opts = { ...defaultOptions, ...options };
    
    const ctx = gsap.context(() => {
      const children = container.querySelectorAll(childSelector);
      if (children.length === 0) return;

      gsap.set(children, {
        y: opts.y,
        x: opts.x,
        scale: opts.scale,
        opacity: opts.opacity ?? 0,
      });

      gsap.to(children, {
        y: 0,
        x: 0,
        scale: 1,
        opacity: 1,
        duration: opts.duration,
        ease: opts.ease,
        stagger: opts.stagger ?? 0.1,
        scrollTrigger: {
          trigger: container,
          start: opts.start,
          scrub: opts.scrub,
          markers: opts.markers,
          toggleActions: opts.scrub ? undefined : 'play none none none',
          onEnter: (self) => {
            triggersRef.current.push(self);
          },
        },
      });
    }, container);

    return () => {
      ctx.revert();
      triggersRef.current.forEach(t => t.kill());
      triggersRef.current = [];
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [childSelector]);

  return containerRef;
};

export default useScrollReveal;
