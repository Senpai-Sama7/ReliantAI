import { useEffect, useRef, useLayoutEffect } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { heroConfig } from '../config';
import { ArrowRight } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const Hero = () => {
  const sectionRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const imageRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const goldLineRef = useRef<HTMLDivElement>(null);
  const triggersRef = useRef<ScrollTrigger[]>([]);
  
  const prefersReducedMotion = typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Set initial states
  useLayoutEffect(() => {
    const image = imageRef.current;
    const title = titleRef.current;
    const subtitle = subtitleRef.current;
    const cta = ctaRef.current;
    const goldLine = goldLineRef.current;
    const overlay = overlayRef.current;

    if (!image || !title || !subtitle || !cta || !goldLine || !overlay) return;

    // Set initial states for animations
    gsap.set(image, { scale: 1.15, opacity: 0 });
    gsap.set(title, { y: 80, opacity: 0 });
    gsap.set(goldLine, { scaleX: 0, opacity: 0 });
    gsap.set(subtitle, { y: 40, opacity: 0 });
    gsap.set(cta, { y: 30, opacity: 0 });
    gsap.set(overlay, { opacity: 0 });
  }, []);

  useEffect(() => {
    const section = sectionRef.current;
    const title = titleRef.current;
    const subtitle = subtitleRef.current;
    const image = imageRef.current;
    const overlay = overlayRef.current;
    const cta = ctaRef.current;
    const goldLine = goldLineRef.current;

    if (!section || !title || !subtitle || !image || !overlay || !cta || !goldLine) return;

    // Clean up previous triggers
    triggersRef.current.forEach(t => t.kill());
    triggersRef.current = [];

    if (prefersReducedMotion) {
      // Show everything immediately without animation
      gsap.set(image, { scale: 1, opacity: 1 });
      gsap.set(title, { y: 0, opacity: 1 });
      gsap.set(goldLine, { scaleX: 1, opacity: 1 });
      gsap.set(subtitle, { y: 0, opacity: 1 });
      gsap.set(cta, { y: 0, opacity: 1 });
      return;
    }

    // Initial load animation timeline
    const tl = gsap.timeline({ 
      defaults: { ease: 'power3.out' },
      delay: 0.3
    });

    tl.fromTo(
      image,
      { scale: 1.15, opacity: 0 },
      { scale: 1, opacity: 1, duration: 1.8 }
    )
    .fromTo(
      title,
      { y: 80, opacity: 0 },
      { y: 0, opacity: 1, duration: 1.2 },
      '-=1.2'
    )
    .fromTo(
      goldLine,
      { scaleX: 0, opacity: 0 },
      { scaleX: 1, opacity: 1, duration: 0.8, ease: 'power2.out' },
      '-=0.6'
    )
    .fromTo(
      subtitle,
      { y: 40, opacity: 0 },
      { y: 0, opacity: 1, duration: 1 },
      '-=0.5'
    )
    .fromTo(
      cta,
      { y: 30, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.8 },
      '-=0.4'
    );

    // Scroll-driven parallax with fromTo for reversibility
    const imageTrigger = ScrollTrigger.create({
      trigger: section,
      start: 'top top',
      end: 'bottom top',
      scrub: 0.6,
      animation: gsap.fromTo(image, 
        { y: 0, scale: 1 },
        { y: 150, scale: 1.1, ease: 'none' }
      ),
    });
    triggersRef.current.push(imageTrigger);

    // Content fade out on scroll
    const contentTrigger = ScrollTrigger.create({
      trigger: section,
      start: 'top top',
      end: '50% top',
      scrub: 0.6,
      onUpdate: (self) => {
        const progress = self.progress;
        gsap.set(title, { 
          opacity: 1 - progress * 1.5,
          y: -progress * 50 
        });
        gsap.set(subtitle, { 
          opacity: 1 - progress * 2,
          y: -progress * 30 
        });
        gsap.set(cta, { 
          opacity: 1 - progress * 2.5,
          y: -progress * 20 
        });
        gsap.set(goldLine, { 
          opacity: 1 - progress * 2 
        });
      },
    });
    triggersRef.current.push(contentTrigger);

    // Darkening overlay
    const overlayTrigger = ScrollTrigger.create({
      trigger: section,
      start: 'top top',
      end: 'bottom top',
      scrub: 0.6,
      animation: gsap.fromTo(overlay, 
        { opacity: 0 },
        { opacity: 0.6, ease: 'none' }
      ),
    });
    triggersRef.current.push(overlayTrigger);

    return () => {
      tl.kill();
      triggersRef.current.forEach(t => t.kill());
      triggersRef.current = [];
    };
  }, [prefersReducedMotion]);

  if (!heroConfig.title && !heroConfig.backgroundImage) return null;

  return (
    <section
      ref={sectionRef}
      className="relative h-[100svh] w-full overflow-hidden bg-genh-black"
      aria-label="Hero"
    >
      {/* Background Image with Ken Burns */}
      <div
        ref={imageRef}
        className="absolute inset-0 w-full h-full"
        style={{ willChange: 'transform' }}
      >
        <img
          src={heroConfig.backgroundImage}
          alt={heroConfig.backgroundAlt}
          className="w-full h-full object-cover"
          style={{
            animation: prefersReducedMotion ? 'none' : 'kenBurns 20s ease-in-out infinite alternate',
          }}
        />
      </div>

      {/* Dark overlay for scroll depth */}
      <div
        ref={overlayRef}
        className="absolute inset-0 bg-genh-black"
        style={{ willChange: 'opacity', opacity: 0 }}
        aria-hidden="true"
      />

      {/* Vignette effect */}
      <div 
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 30%, rgba(11, 12, 14, 0.7) 100%)'
        }}
        aria-hidden="true"
      />

      {/* Content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center px-4 sm:px-8">
        {/* Main Title - ALL CAPS per spec */}
        <h1
          ref={titleRef}
          className="font-display text-genh-white text-display uppercase tracking-tight select-none text-center max-w-6xl"
          style={{
            textShadow: '0 4px 40px rgba(0,0,0,0.5)',
            willChange: 'transform, opacity',
            lineHeight: 0.95,
            letterSpacing: '-0.02em',
          }}
        >
          {heroConfig.title}
        </h1>

        {/* Gold accent line - 2px height per spec */}
        <div 
          ref={goldLineRef}
          className="w-24 h-0.5 bg-genh-gold mt-8 mb-6"
          style={{ 
            willChange: 'transform, opacity',
            height: '2px'
          }}
        />

        {/* Subtitle */}
        <p
          ref={subtitleRef}
          className="font-body text-genh-gray text-sm md:text-base uppercase tracking-[0.25em] text-center max-w-2xl"
          style={{ willChange: 'transform, opacity' }}
        >
          {heroConfig.subtitle}
        </p>

        {/* CTA Buttons */}
        <div
          ref={ctaRef}
          className="flex flex-col sm:flex-row items-center gap-4 mt-12"
          style={{ willChange: 'transform, opacity' }}
        >
          <button 
            className="group flex items-center gap-2 px-8 py-4 bg-genh-gold text-genh-black font-body font-semibold text-sm uppercase tracking-wider transition-all duration-300 hover:bg-genh-cream hover:translate-y-[-2px]"
            style={{ clipPath: 'polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 0 100%)' }}
          >
            Start the Strategy Brief
            <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-1" />
          </button>
          <button 
            className="px-8 py-4 border border-genh-gold text-genh-gold font-body font-semibold text-sm uppercase tracking-wider transition-all duration-300 hover:bg-genh-gold hover:text-genh-black hover:translate-y-[-2px]"
          >
            Book a Discovery Call
          </button>
        </div>
      </div>

      {/* Bottom gradient for seamless transition */}
      <div 
        className="absolute bottom-0 left-0 right-0 h-40 pointer-events-none"
        style={{
          background: 'linear-gradient(to top, #0B0C0E 0%, transparent 100%)'
        }}
        aria-hidden="true"
      />
    </section>
  );
};

export default Hero;
