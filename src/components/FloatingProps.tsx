import { useLayoutEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

interface Prop {
  src: string;
  className: string;
  alt?: string;
}

interface FloatingPropsProps {
  props: Prop[];
  className?: string;
}

export function FloatingProps({ props, className = '' }: FloatingPropsProps) {
  const ref = useRef<HTMLDivElement | null>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;

    const items = gsap.utils.toArray<HTMLElement>('[data-float]', el);

    items.forEach((node, i) => {
      // Random starting position offset
      const randomY = Math.random() * 20 - 10;
      const randomRotate = Math.random() * 4 - 2;
      
      gsap.set(node, { y: randomY, rotate: randomRotate });

      // Parallax on scroll
      gsap.to(node, {
        y: i % 2 === 0 ? -40 : 30,
        rotate: i % 2 === 0 ? -3 : 3,
        ease: 'none',
        scrollTrigger: {
          trigger: el,
          start: 'top bottom',
          end: 'bottom top',
          scrub: 0.8,
        },
      });

      // Gentle idle animation
      gsap.to(node, {
        y: `+=${Math.random() * 10 - 5}`,
        x: `+=${Math.random() * 6 - 3}`,
        rotation: `+=${Math.random() * 2 - 1}`,
        duration: 3 + Math.random() * 2,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
      });
    });
  }, []);

  return (
    <div ref={ref} className={`absolute inset-0 pointer-events-none overflow-hidden ${className}`} aria-hidden="true">
      {props.map((prop, i) => (
        <img
          key={i}
          data-float
          src={prop.src}
          alt={prop.alt || ''}
          className={`absolute will-change-transform ${prop.className}`}
          style={{ transformOrigin: 'center center' }}
        />
      ))}
    </div>
  );
}

export default FloatingProps;
