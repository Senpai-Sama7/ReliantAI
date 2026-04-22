import { useEffect, useRef, useLayoutEffect } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { zigZagGridConfig, type ZigZagGridItem } from '../config';

gsap.registerPlugin(ScrollTrigger);

interface GridItemProps {
  item: ZigZagGridItem;
  index: number;
}

const GridItem = ({ item, index }: GridItemProps) => {
  const itemRef = useRef<HTMLDivElement>(null);
  const imageContainerRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const textRef = useRef<HTMLDivElement>(null);
  const goldLineRef = useRef<HTMLDivElement>(null);
  const triggersRef = useRef<ScrollTrigger[]>([]);

  const prefersReducedMotion = typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Set initial states
  useLayoutEffect(() => {
    const text = textRef.current;
    const goldLine = goldLineRef.current;

    if (!text || !goldLine) return;

    gsap.set(text.children, { opacity: 0, y: 40 });
    gsap.set(goldLine, { scaleX: 0 });
  }, []);

  useEffect(() => {
    const itemEl = itemRef.current;
    const imageContainer = imageContainerRef.current;
    const image = imageRef.current;
    const text = textRef.current;
    const goldLine = goldLineRef.current;

    if (!itemEl || !imageContainer || !image || !text || !goldLine) return;

    // Clean up previous triggers
    triggersRef.current.forEach(t => t.kill());
    triggersRef.current = [];

    if (prefersReducedMotion) {
      gsap.set(text.children, { opacity: 1, y: 0 });
      gsap.set(goldLine, { scaleX: 1 });
      return;
    }

    // Text reveal animation with stagger
    const textTrigger = ScrollTrigger.create({
      trigger: text,
      start: 'top 80%',
      once: true,
      onEnter: () => {
        const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
        
        tl.fromTo(text.children, 
          { opacity: 0, y: 40 },
          { opacity: 1, y: 0, duration: 0.8, stagger: 0.1 }
        )
        .fromTo(goldLine,
          { scaleX: 0 },
          { scaleX: 1, duration: 0.6, ease: 'power2.out' },
          '-=0.4'
        );
      },
    });
    triggersRef.current.push(textTrigger);

    // Internal parallax on image - scrub for reversibility
    const imageTrigger = ScrollTrigger.create({
      trigger: imageContainer,
      start: 'top bottom',
      end: 'bottom top',
      scrub: 0.6,
      onUpdate: (self) => {
        const yPercent = (self.progress - 0.5) * 15;
        gsap.set(image, { yPercent });
      },
    });
    triggersRef.current.push(imageTrigger);

    return () => {
      triggersRef.current.forEach(t => t.kill());
      triggersRef.current = [];
    };
  }, [prefersReducedMotion]);

  const isReversed = item.reverse;

  return (
    <div
      ref={itemRef}
      className={`grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-16 items-center ${
        index > 0 ? 'mt-24 md:mt-32' : ''
      }`}
    >
      {/* Image Column */}
      <div
        ref={imageContainerRef}
        className={`relative overflow-hidden ${
          isReversed ? 'lg:order-2' : 'lg:order-1'
        }`}
        style={{ clipPath: 'polygon(0 0, calc(100% - 32px) 0, 100% 32px, 100% 100%, 0 100%)' }}
      >
        <div className="relative aspect-[4/3] overflow-hidden bg-genh-charcoal">
          <img
            ref={imageRef}
            src={item.image}
            alt={item.imageAlt}
            className="w-full h-[120%] object-cover"
            style={{
              willChange: 'transform',
            }}
            loading="lazy"
          />
          {/* Image Overlay */}
          <div className="absolute inset-0 bg-genh-black/20" />
        </div>
      </div>

      {/* Text Column */}
      <div
        ref={textRef}
        className={`${isReversed ? 'lg:order-1 lg:pr-8' : 'lg:order-2 lg:pl-8'}`}
      >
        {/* Gold Label */}
        <span className="text-label" style={{ willChange: 'transform, opacity' }}>
          {item.subtitle}
        </span>
        
        {/* Headline - ALL CAPS */}
        <h3 
          className="font-display text-headline text-genh-white mt-4 uppercase tracking-tight"
          style={{ 
            willChange: 'transform, opacity',
            lineHeight: 0.95,
            letterSpacing: '-0.02em',
          }}
        >
          {item.title}
        </h3>
        
        {/* Description */}
        <p 
          className="font-body text-sm md:text-base text-genh-gray/80 leading-relaxed mt-6"
          style={{ willChange: 'transform, opacity' }}
        >
          {item.description}
        </p>

        {/* Decorative gold line - 2px height per spec */}
        <div 
          ref={goldLineRef}
          className="w-16 bg-genh-gold/50 mt-8 origin-left"
          style={{ 
            willChange: 'transform',
            height: '2px'
          }}
        />
      </div>
    </div>
  );
};

const ZigZagGrid = () => {
  const sectionRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const triggersRef = useRef<ScrollTrigger[]>([]);

  const prefersReducedMotion = typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Set initial states
  useLayoutEffect(() => {
    const header = headerRef.current;
    if (!header) return;

    gsap.set(header.children, { opacity: 0, y: 40 });
  }, []);

  useEffect(() => {
    const header = headerRef.current;
    if (!header) return;

    // Clean up previous triggers
    triggersRef.current.forEach(t => t.kill());
    triggersRef.current = [];

    if (prefersReducedMotion) {
      gsap.set(header.children, { opacity: 1, y: 0 });
      return;
    }

    // Header reveal with stagger
    const trigger = ScrollTrigger.create({
      trigger: header,
      start: 'top 80%',
      once: true,
      onEnter: () => {
        gsap.fromTo(header.children, 
          { opacity: 0, y: 40 },
          { opacity: 1, y: 0, duration: 0.8, stagger: 0.15, ease: 'power3.out' }
        );
      },
    });
    triggersRef.current.push(trigger);

    return () => {
      triggersRef.current.forEach(t => t.kill());
      triggersRef.current = [];
    };
  }, [prefersReducedMotion]);

  if (!zigZagGridConfig.sectionTitle && zigZagGridConfig.items.length === 0) return null;

  return (
    <section
      ref={sectionRef}
      className="relative w-full py-24 md:py-32 lg:py-40 bg-genh-black"
      aria-label="How It Works"
    >
      <div className="max-w-7xl mx-auto px-6 md:px-8 lg:px-12">
        {/* Section Header */}
        <div ref={headerRef} className="text-center mb-20 md:mb-28">
          <span className="text-label" style={{ willChange: 'transform, opacity' }}>
            {zigZagGridConfig.sectionLabel}
          </span>
          <h2 
            className="font-display text-headline text-genh-white mt-4 uppercase tracking-tight"
            style={{ 
              willChange: 'transform, opacity',
              lineHeight: 0.95,
              letterSpacing: '-0.02em',
            }}
          >
            {zigZagGridConfig.sectionTitle}
          </h2>
          <div className="w-24 h-0.5 bg-genh-gold mx-auto mt-6" style={{ height: '2px' }} />
        </div>

        {/* Grid Items */}
        {zigZagGridConfig.items.map((item, index) => (
          <GridItem key={item.id} item={item} index={index} />
        ))}
      </div>
    </section>
  );
};

export default ZigZagGrid;
