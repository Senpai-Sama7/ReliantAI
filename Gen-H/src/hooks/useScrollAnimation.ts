import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

interface ScrollAnimationOptions {
  trigger?: string | Element;
  start?: string;
  end?: string;
  scrub?: boolean | number;
  markers?: boolean;
  toggleActions?: string;
  pin?: boolean;
  onEnter?: () => void;
  onLeave?: () => void;
  onEnterBack?: () => void;
  onLeaveBack?: () => void;
}

export const useScrollAnimation = (
  animation: (timeline: gsap.core.Timeline, trigger: HTMLElement) => void,
  options: ScrollAnimationOptions = {},
  dependencies: unknown[] = []
) => {
  const elementRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<gsap.core.Timeline | null>(null);
  const triggerRef = useRef<ScrollTrigger | null>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const timeline = gsap.timeline({
      scrollTrigger: {
        trigger: options.trigger || element,
        start: options.start || 'top 80%',
        end: options.end || 'bottom 20%',
        scrub: options.scrub ?? false,
        markers: options.markers ?? false,
        toggleActions: options.toggleActions || 'play none none none',
        pin: options.pin ?? false,
        onEnter: options.onEnter,
        onLeave: options.onLeave,
        onEnterBack: options.onEnterBack,
        onLeaveBack: options.onLeaveBack,
      },
    });

    timelineRef.current = timeline;
    triggerRef.current = timeline.scrollTrigger as ScrollTrigger;

    animation(timeline, element);

    return () => {
      if (triggerRef.current) {
        triggerRef.current.kill();
      }
      if (timelineRef.current) {
        timelineRef.current.kill();
      }
    };
  }, dependencies);

  return { elementRef, timelineRef, triggerRef };
};

export const useParallax = (speed: number = 0.5) => {
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const trigger = ScrollTrigger.create({
      trigger: element,
      start: 'top bottom',
      end: 'bottom top',
      scrub: true,
      onUpdate: (self) => {
        const yPos = self.progress * 100 * speed;
        gsap.set(element, { y: yPos });
      },
    });

    return () => {
      trigger.kill();
    };
  }, [speed]);

  return elementRef;
};

export const useFadeInUp = (delay: number = 0, stagger: number = 0) => {
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const children = stagger > 0 ? element.children : [element];

    gsap.set(children, { opacity: 0, y: 30 });

    const trigger = ScrollTrigger.create({
      trigger: element,
      start: 'top 85%',
      once: true,
      onEnter: () => {
        gsap.to(children, {
          opacity: 1,
          y: 0,
          duration: 0.8,
          delay,
          stagger,
          ease: 'power3.out',
        });
      },
    });

    return () => {
      trigger.kill();
    };
  }, [delay, stagger]);

  return elementRef;
};

export default useScrollAnimation;
