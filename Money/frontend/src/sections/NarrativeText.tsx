import { useEffect, useRef, useLayoutEffect } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { narrativeTextConfig } from '../config';
import { Sparkles } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const NarrativeText = () => {
  const sectionRef = useRef<HTMLDivElement>(null);
  const line1Ref = useRef<HTMLParagraphElement>(null);
  const line2Ref = useRef<HTMLParagraphElement>(null);
  const line3Ref = useRef<HTMLParagraphElement>(null);
  const starRef = useRef<HTMLDivElement>(null);
  const bottomLineRef = useRef<HTMLDivElement>(null);
  const triggersRef = useRef<ScrollTrigger[]>([]);

  const prefersReducedMotion = typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Set initial states
  useLayoutEffect(() => {
    const line1 = line1Ref.current;
    const line2 = line2Ref.current;
    const line3 = line3Ref.current;
    const star = starRef.current;
    const bottomLine = bottomLineRef.current;

    if (!line1 || !line2 || !line3 || !star || !bottomLine) return;

    gsap.set([line1, line2, line3], { opacity: 0, y: 40 });
    gsap.set(star, { opacity: 0, scale: 0.5, rotation: -180 });
    gsap.set(bottomLine, { scaleX: 0, opacity: 0 });
  }, []);

  useEffect(() => {
    const section = sectionRef.current;
    const line1 = line1Ref.current;
    const line2 = line2Ref.current;
    const line3 = line3Ref.current;
    const star = starRef.current;
    const bottomLine = bottomLineRef.current;

    if (!section || !line1 || !line2 || !line3 || !star || !bottomLine) return;

    // Clean up previous triggers
    triggersRef.current.forEach(t => t.kill());
    triggersRef.current = [];

    if (prefersReducedMotion) {
      // Show everything immediately
      gsap.set([line1, line2, line3], { opacity: 1, y: 0 });
      gsap.set(star, { opacity: 1, scale: 1, rotation: 0 });
      gsap.set(bottomLine, { scaleX: 1, opacity: 1 });
      return;
    }

    // Star animation with fromTo for reversibility
    const starTrigger = ScrollTrigger.create({
      trigger: star,
      start: 'top 85%',
      once: true,
      onEnter: () => {
        gsap.fromTo(star, 
          { opacity: 0, scale: 0.5, rotation: -180 },
          { 
            opacity: 1, 
            scale: 1, 
            rotation: 0,
            duration: 1, 
            ease: 'back.out(1.7)' 
          }
        );
      },
    });
    triggersRef.current.push(starTrigger);

    // Line animations with 0.1s stagger as per spec
    const lineTrigger = ScrollTrigger.create({
      trigger: line1,
      start: 'top 80%',
      once: true,
      onEnter: () => {
        const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
        
        tl.fromTo(line1, 
          { opacity: 0, y: 40 },
          { opacity: 1, y: 0, duration: 1 }
        )
        .fromTo(line2, 
          { opacity: 0, y: 40 },
          { opacity: 1, y: 0, duration: 1 },
          '-=0.9' // 0.1s stagger
        )
        .fromTo(line3, 
          { opacity: 0, y: 40 },
          { opacity: 1, y: 0, duration: 1 },
          '-=0.9' // 0.1s stagger
        )
        .fromTo(bottomLine,
          { scaleX: 0, opacity: 0 },
          { scaleX: 1, opacity: 1, duration: 0.8, ease: 'power2.out' },
          '-=0.5'
        );
      },
    });
    triggersRef.current.push(lineTrigger);

    // Continuous star rotation
    gsap.to(star, {
      rotation: 360,
      duration: 20,
      repeat: -1,
      ease: 'none',
    });

    return () => {
      triggersRef.current.forEach(t => t.kill());
      triggersRef.current = [];
    };
  }, [prefersReducedMotion]);

  // Check if content exists
  const hasContent = narrativeTextConfig.line1 || narrativeTextConfig.line2 || narrativeTextConfig.line3;
  if (!hasContent) return null;

  return (
    <section
      ref={sectionRef}
      className="relative w-full py-32 md:py-48 lg:py-56 bg-genh-black"
      aria-label="Our Approach"
    >
      <div className="max-w-4xl mx-auto px-6 md:px-8 text-center">
        {/* Gold Star Icon - Animated */}
        <div
          ref={starRef}
          className="flex justify-center mb-16"
          style={{ willChange: 'transform, opacity' }}
        >
          <div className="relative">
            <Sparkles className="w-10 h-10 md:w-12 md:h-12 text-genh-gold" />
            {/* Secondary rotating star for depth */}
            <Sparkles 
              className="absolute inset-0 w-10 h-10 md:w-12 md:h-12 text-genh-gold/30" 
              style={{ animation: prefersReducedMotion ? 'none' : 'spinSlow 15s linear infinite reverse' }}
            />
          </div>
        </div>

        {/* Narrative Text - Three Lines Centered */}
        <div className="space-y-8 md:space-y-10">
          <p
            ref={line1Ref}
            className="font-display text-headline text-genh-white uppercase tracking-tight"
            style={{ 
              willChange: 'transform, opacity',
              lineHeight: 0.95,
              letterSpacing: '-0.02em',
            }}
          >
            {narrativeTextConfig.line1}
          </p>

          <p
            ref={line2Ref}
            className="font-body text-lg md:text-xl text-genh-gray max-w-2xl mx-auto leading-relaxed"
            style={{ willChange: 'transform, opacity' }}
          >
            {narrativeTextConfig.line2}
          </p>

          <p
            ref={line3Ref}
            className="font-body text-sm md:text-base text-genh-gray/70 max-w-lg mx-auto leading-relaxed tracking-wide"
            style={{ willChange: 'transform, opacity' }}
          >
            {narrativeTextConfig.line3}
          </p>
        </div>

        {/* Bottom gold accent line */}
        <div className="flex justify-center mt-16">
          <div 
            ref={bottomLineRef}
            className="w-16 h-0.5 bg-genh-gold/50"
            style={{ 
              willChange: 'transform, opacity',
              height: '2px'
            }}
          />
        </div>
      </div>
    </section>
  );
};

export default NarrativeText;
