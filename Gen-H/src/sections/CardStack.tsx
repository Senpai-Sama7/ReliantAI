import { useEffect, useRef, useLayoutEffect } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { cardStackConfig } from '../config';

gsap.registerPlugin(ScrollTrigger);

const CardStack = () => {
  const sectionRef = useRef<HTMLDivElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const cardsRef = useRef<(HTMLDivElement | null)[]>([]);
  const headerRef = useRef<HTMLDivElement>(null);
  const scrollTriggerRef = useRef<ScrollTrigger | null>(null);
  const triggersRef = useRef<ScrollTrigger[]>([]);

  const cards = cardStackConfig.cards;
  const prefersReducedMotion = typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Set initial positions
  useLayoutEffect(() => {
    const cardElements = cardsRef.current.filter(Boolean) as HTMLDivElement[];
    if (cardElements.length === 0) return;

    // Set initial states for cards
    cardElements.forEach((card, index) => {
      gsap.set(card, {
        y: index === 0 ? 0 : typeof window !== 'undefined' ? window.innerHeight : 800,
        rotation: cards[index].rotation,
        opacity: index === 0 ? 1 : 0,
        zIndex: index + 1,
      });
    });
  }, []);

  useEffect(() => {
    const section = sectionRef.current;
    const wrapper = wrapperRef.current;
    const cardElements = cardsRef.current.filter(Boolean) as HTMLDivElement[];
    const header = headerRef.current;

    if (!section || !wrapper || cardElements.length === 0) return;

    // Clean up previous triggers
    triggersRef.current.forEach(t => t.kill());
    triggersRef.current = [];

    if (prefersReducedMotion) {
      // Show all cards immediately without animation
      cardElements.forEach((card) => {
        gsap.set(card, { y: 0, opacity: 1 });
      });
      if (header) gsap.set(header, { opacity: 1 });
      return;
    }

    // Header animation - fade in when section enters
    if (header) {
      gsap.set(header, { opacity: 0, y: 30 });
      const headerTrigger = ScrollTrigger.create({
        trigger: section,
        start: 'top 80%',
        once: true,
        onEnter: () => {
          gsap.to(header, {
            opacity: 1,
            y: 0,
            duration: 0.8,
            ease: 'power3.out',
          });
        },
      });
      triggersRef.current.push(headerTrigger);
    }

    // Calculate segment size for each card
    const segmentSize = 1 / cardElements.length;

    // Create pinned scroll animation with scrub for reversibility
    const scrollTrigger = ScrollTrigger.create({
      trigger: section,
      start: 'top top',
      end: '+=130%',
      pin: wrapper,
      pinSpacing: true,
      scrub: 0.6,
      onUpdate: (self) => {
        const progress = self.progress;

        cardElements.forEach((card, index) => {
          const cardStart = index * segmentSize;
          const cardProgress = gsap.utils.clamp(0, 1, (progress - cardStart) / segmentSize);
          
          if (index === 0) {
            // First card stays with slight fade as others stack
            gsap.set(card, {
              opacity: 1 - cardProgress * 0.2,
              scale: 1 - cardProgress * 0.02,
            });
          } else {
            // Subsequent cards slide up from bottom
            const prevCardStart = (index - 1) * segmentSize;
            const prevCardProgress = gsap.utils.clamp(0, 1, (progress - prevCardStart) / segmentSize);
            
            // Smooth slide up with easing
            const easedProgress = gsap.parseEase('power2.out')(prevCardProgress);
            const startY = typeof window !== 'undefined' ? window.innerHeight * 0.8 : 600;
            
            gsap.set(card, {
              y: (1 - easedProgress) * startY,
              opacity: Math.min(1, prevCardProgress * 1.5),
              zIndex: index + 1,
            });
          }
        });
      },
    });

    scrollTriggerRef.current = scrollTrigger;
    triggersRef.current.push(scrollTrigger);

    return () => {
      triggersRef.current.forEach(t => t.kill());
      triggersRef.current = [];
    };
  }, [prefersReducedMotion]);

  if (!cardStackConfig.sectionTitle && cards.length === 0) return null;

  return (
    <section
      ref={sectionRef}
      className="relative w-full bg-genh-black"
      style={{ minHeight: '230vh' }}
      aria-label="What We Build"
    >
      {/* Section Header */}
      <div 
        ref={headerRef}
        className="absolute top-0 left-0 right-0 py-12 md:py-16 text-center z-10"
        style={{ willChange: 'transform, opacity' }}
      >
        <span className="text-label">
          {cardStackConfig.sectionSubtitle}
        </span>
        <h2 className="font-display text-headline text-genh-white mt-4 uppercase tracking-tight">
          {cardStackConfig.sectionTitle}
        </h2>
        <div className="w-24 h-0.5 bg-genh-gold mx-auto mt-6" />
      </div>

      {/* Pinned Card Wrapper */}
      <div
        ref={wrapperRef}
        className="relative w-full h-screen flex items-center justify-center overflow-hidden"
      >
        <div className="relative w-full max-w-4xl mx-auto px-6 md:px-8 aspect-[4/3]">
          {cards.map((card, index) => (
            <div
              key={card.id}
              ref={(el) => { cardsRef.current[index] = el; }}
              className="absolute inset-0"
              style={{
                willChange: 'transform, opacity',
                zIndex: index + 1,
              }}
            >
              <div 
                className="relative overflow-hidden shadow-premium bg-genh-charcoal h-full"
                style={{
                  clipPath: 'polygon(0 0, calc(100% - 44px) 0, 100% 44px, 100% 100%, 0 100%)',
                }}
              >
                {/* Image */}
                <div className="absolute inset-0 overflow-hidden">
                  <img
                    src={card.image}
                    alt={card.title}
                    className="w-full h-full object-cover"
                    loading={index === 0 ? 'eager' : 'lazy'}
                  />
                  {/* Image Overlay */}
                  <div className="absolute inset-0 bg-gradient-to-t from-genh-black/90 via-genh-black/40 to-transparent" />
                </div>

                {/* Card Content */}
                <div className="absolute bottom-0 left-0 right-0 p-6 md:p-10">
                  <h3 className="font-display text-2xl md:text-4xl text-genh-white mb-3 uppercase tracking-tight">
                    {card.title}
                  </h3>
                  <div className="w-16 h-0.5 bg-genh-gold mb-4" />
                  <p className="font-body text-sm md:text-base text-genh-gray/90 max-w-md leading-relaxed">
                    {card.description}
                  </p>
                </div>

                {/* Card Number Badge */}
                <div 
                  className="absolute top-6 right-6 w-12 h-12 border border-genh-gold/50 flex items-center justify-center"
                  style={{ clipPath: 'polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 0 100%)' }}
                >
                  <span className="font-body text-sm text-genh-gold font-semibold">
                    {String(index + 1).padStart(2, '0')}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom spacer for scroll room */}
      <div className="h-32" />
    </section>
  );
};

export default CardStack;
