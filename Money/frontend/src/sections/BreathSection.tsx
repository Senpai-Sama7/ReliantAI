import { useEffect, useRef, useLayoutEffect } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { breathSectionConfig } from '../config';
import { BarChart3, TrendingUp, Target } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

interface MetricCardProps {
  icon: React.ReactNode;
  value: string;
  label: string;
  delay: number;
}

const MetricCard = ({ icon, value, label }: MetricCardProps) => {
  return (
    <div 
      className="text-center p-6 md:p-8 border border-genh-white/10 bg-genh-black/40 backdrop-blur-sm transition-all duration-300 hover:border-genh-gold/50 hover:bg-genh-black/60"
      style={{ clipPath: 'polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 0 100%)' }}
    >
      <div className="flex justify-center mb-4">
        {icon}
      </div>
      <div className="font-display text-3xl md:text-4xl text-genh-white tracking-tight">
        {value}
      </div>
      <div className="text-label mt-2 text-genh-gold">
        {label}
      </div>
    </div>
  );
};

const BreathSection = () => {
  const sectionRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const descRef = useRef<HTMLParagraphElement>(null);
  const metricsRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const triggersRef = useRef<ScrollTrigger[]>([]);

  const prefersReducedMotion = typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Set initial states
  useLayoutEffect(() => {
    const container = containerRef.current;
    const text = textRef.current;
    const subtitle = subtitleRef.current;
    const desc = descRef.current;
    const metrics = metricsRef.current;
    const image = imageRef.current;

    if (!container || !text || !subtitle || !desc || !metrics || !image) return;

    gsap.set(container, { scale: 0.85 });
    gsap.set(text, { opacity: 0, y: 60 });
    gsap.set(subtitle, { opacity: 0, y: 30 });
    gsap.set(desc, { opacity: 0, y: 40 });
    gsap.set(metrics.children, { opacity: 0, y: 30, scale: 0.95 });
    gsap.set(image, { scale: 1.1 });
  }, []);

  useEffect(() => {
    const section = sectionRef.current;
    const container = containerRef.current;
    const text = textRef.current;
    const subtitle = subtitleRef.current;
    const desc = descRef.current;
    const metrics = metricsRef.current;
    const image = imageRef.current;

    if (!section || !container || !text || !subtitle || !desc || !metrics || !image) return;

    // Clean up previous triggers
    triggersRef.current.forEach(t => t.kill());
    triggersRef.current = [];

    if (prefersReducedMotion) {
      gsap.set(container, { scale: 1 });
      gsap.set(text, { opacity: 1, y: 0 });
      gsap.set(subtitle, { opacity: 1, y: 0 });
      gsap.set(desc, { opacity: 1, y: 0 });
      gsap.set(metrics.children, { opacity: 1, y: 0, scale: 1 });
      gsap.set(image, { scale: 1 });
      return;
    }

    // Main scale-up animation on scroll - cinematic reveal
    const mainTrigger = ScrollTrigger.create({
      trigger: section,
      start: 'top 80%',
      end: 'center center',
      scrub: 0.6,
      onUpdate: (self) => {
        const progress = self.progress;

        // Container scale from 0.85 to 1
        gsap.set(container, {
          scale: 0.85 + progress * 0.15,
        });

        // Image scale from 1.1 to 1 (counter-scale for depth)
        gsap.set(image, {
          scale: 1.1 - progress * 0.1,
        });

        // Main headline reveal with from-like behavior
        const textProgress = gsap.utils.clamp(0, 1, progress * 1.5);
        gsap.set(text, {
          opacity: textProgress,
          y: 60 - textProgress * 60,
        });

        // Subtitle reveal
        if (progress > 0.3) {
          const subtitleProgress = gsap.utils.clamp(0, 1, (progress - 0.3) * 1.43);
          gsap.set(subtitle, {
            opacity: subtitleProgress,
            y: 30 - subtitleProgress * 30,
          });
        } else {
          gsap.set(subtitle, { opacity: 0, y: 30 });
        }
      },
    });
    triggersRef.current.push(mainTrigger);

    // Description reveal
    const descTrigger = ScrollTrigger.create({
      trigger: desc,
      start: 'top 85%',
      once: true,
      onEnter: () => {
        gsap.fromTo(desc, 
          { opacity: 0, y: 40 },
          { opacity: 1, y: 0, duration: 1, ease: 'power3.out' }
        );
      },
    });
    triggersRef.current.push(descTrigger);

    // Metrics reveal with stagger
    const metricsTrigger = ScrollTrigger.create({
      trigger: metrics,
      start: 'top 85%',
      once: true,
      onEnter: () => {
        gsap.fromTo(metrics.children, 
          { opacity: 0, y: 30, scale: 0.95 },
          { 
            opacity: 1, 
            y: 0, 
            scale: 1,
            duration: 0.8, 
            stagger: 0.1,
            ease: 'power3.out' 
          }
        );
      },
    });
    triggersRef.current.push(metricsTrigger);

    return () => {
      triggersRef.current.forEach(t => t.kill());
      triggersRef.current = [];
    };
  }, [prefersReducedMotion]);

  if (!breathSectionConfig.title && !breathSectionConfig.backgroundImage) return null;

  return (
    <section
      ref={sectionRef}
      className="relative w-full py-16 md:py-24 bg-genh-black"
      aria-label="Dashboard Features"
    >
      <div className="px-4 md:px-8">
        <div
          ref={containerRef}
          className="relative w-full max-w-7xl mx-auto overflow-hidden"
          style={{ willChange: 'transform' }}
        >
          {/* Background Image Container */}
          <div className="relative aspect-[16/9] md:aspect-[21/9] overflow-hidden">
            <img
              ref={imageRef}
              src={breathSectionConfig.backgroundImage}
              alt={breathSectionConfig.backgroundAlt}
              className="w-full h-full object-cover"
              style={{ willChange: 'transform' }}
            />

            {/* Dark overlay for text contrast */}
            <div className="absolute inset-0 bg-genh-black/50" />

            {/* Vignette */}
            <div 
              className="absolute inset-0 pointer-events-none"
              style={{
                background: 'radial-gradient(ellipse at center, transparent 20%, rgba(11, 12, 14, 0.85) 100%)'
              }}
            />

            {/* Content Overlay */}
            <div className="absolute inset-0 flex flex-col items-center justify-center px-4 text-center">
              <h2
                ref={textRef}
                className="font-display text-3xl sm:text-4xl md:text-5xl lg:text-display text-genh-white uppercase tracking-tight max-w-5xl"
                style={{
                  willChange: 'transform, opacity',
                  textShadow: '0 4px 40px rgba(0,0,0,0.5)',
                  lineHeight: 0.95,
                  letterSpacing: '-0.02em',
                }}
              >
                {breathSectionConfig.title}
              </h2>
              <p
                ref={subtitleRef}
                className="font-body text-genh-gold text-sm md:text-base uppercase tracking-[0.25em] mt-6"
                style={{ willChange: 'transform, opacity' }}
              >
                {breathSectionConfig.subtitle}
              </p>
            </div>

            {/* Subtle gradient edges */}
            <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-genh-black/60 to-transparent pointer-events-none" />
            <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-genh-black/60 to-transparent pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Description and Metrics */}
      {(breathSectionConfig.description || true) && (
        <div className="max-w-4xl mx-auto px-6 md:px-8 mt-16 md:mt-24">
          {breathSectionConfig.description && (
            <p 
              ref={descRef}
              className="font-body text-base md:text-lg text-genh-gray/80 text-center leading-relaxed"
              style={{ willChange: 'transform, opacity' }}
            >
              {breathSectionConfig.description}
            </p>
          )}
          
          {/* Metric Cards - Fit Score, Urgency, Clarity */}
          <div 
            ref={metricsRef}
            className="grid grid-cols-3 gap-3 md:gap-6 mt-12"
          >
            <MetricCard 
              icon={<Target className="w-6 h-6 md:w-8 md:h-8 text-genh-gold" />}
              value="74%"
              label="Fit Score"
              delay={0}
            />
            <MetricCard 
              icon={<TrendingUp className="w-6 h-6 md:w-8 md:h-8 text-genh-gold" />}
              value="68%"
              label="Urgency"
              delay={0.1}
            />
            <MetricCard 
              icon={<BarChart3 className="w-6 h-6 md:w-8 md:h-8 text-genh-gold" />}
              value="82%"
              label="Clarity"
              delay={0.2}
            />
          </div>
        </div>
      )}
    </section>
  );
};

export default BreathSection;
