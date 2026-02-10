import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ArrowDown } from 'lucide-react';
import { lazy, Suspense } from 'react';
import LogoReveal from '../components/LogoReveal';
import CountUp from '../components/CountUp';

// Lazy load 3D component to reduce initial bundle and TBT
const TorusKnot3D = lazy(() => import('../components/TorusKnot3D'));

gsap.registerPlugin(ScrollTrigger);

export default function HeroV2() {
  const sectionRef = useRef<HTMLElement>(null);
  const headlineRef = useRef<HTMLHeadingElement>(null);
  const subheadRef = useRef<HTMLParagraphElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const statsRef = useRef<HTMLDivElement>(null);
  const orbit1Ref = useRef<HTMLDivElement>(null);
  const orbit2Ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      const setVisible = (element: HTMLElement | null) => {
        if (element) {
          element.style.transform = 'translateY(0)';
          element.style.opacity = '1';
        }
      };
      setVisible(headlineRef.current);
      setVisible(subheadRef.current);
      setVisible(ctaRef.current);
      if (statsRef.current) {
        Array.from(statsRef.current.children).forEach((child) => {
          const el = child as HTMLElement;
          el.style.transform = 'translateY(0)';
          el.style.opacity = '1';
        });
      }
      [orbit1Ref.current, orbit2Ref.current].forEach((orbit) => {
        if (orbit) {
          orbit.style.opacity = '1';
          orbit.style.transform = 'scale(1)';
        }
      });
      return;
    }

    const startAnimations = () => {
      const ctx = gsap.context(() => {
        const tl = gsap.timeline({ delay: 2.2 });

        tl.fromTo(
          headlineRef.current,
          { y: 80, opacity: 0 },
          { y: 0, opacity: 1, duration: 1.2, ease: 'power3.out' }
        )
          .fromTo(
            subheadRef.current,
            { y: 40, opacity: 0 },
            { y: 0, opacity: 1, duration: 0.9, ease: 'power3.out' },
            '-=0.7'
          )
          .fromTo(
            ctaRef.current,
            { y: 30, opacity: 0, scale: 0.98 },
            { y: 0, opacity: 1, scale: 1, duration: 0.7, ease: 'power2.out' },
            '-=0.5'
          )
          .fromTo(
            statsRef.current?.children || [],
            { y: 30, opacity: 0 },
            {
              y: 0,
              opacity: 1,
              duration: 0.6,
              stagger: 0.12,
              ease: 'power2.out',
            },
            '-=0.3'
          )
          .fromTo(
            [orbit1Ref.current, orbit2Ref.current],
            { opacity: 0, scale: 0.8 },
            { opacity: 1, scale: 1, duration: 1, stagger: 0.2, ease: 'power2.out' },
            '-=0.5'
          );

        gsap.to(orbit1Ref.current, {
          rotation: 360,
          duration: 30,
          ease: 'none',
          repeat: -1,
        });

        gsap.to(orbit2Ref.current, {
          rotation: -360,
          duration: 25,
          ease: 'none',
          repeat: -1,
          });
        }, sectionRef);

      return () => ctx.revert();
    };

    let cleanup: (() => void) | undefined;
    let idleId: number | undefined;
    let timerId: ReturnType<typeof setTimeout> | undefined;

    const triggerAnimations = () => {
      cleanup = startAnimations();
    };

    if ('requestIdleCallback' in window) {
      idleId = requestIdleCallback(triggerAnimations, { timeout: 200 });
    } else {
      timerId = setTimeout(triggerAnimations, 100);
    }

    return () => {
      if (idleId && 'cancelIdleCallback' in window) {
        cancelIdleCallback(idleId);
      }
      if (timerId) {
        clearTimeout(timerId);
      }
      cleanup?.();
    };
  }, []);

  const scrollToWork = () => {
    const workSection = document.getElementById('work');
    if (workSection) {
      workSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const stats = [
    { value: 100, prefix: '', suffix: '+', label: 'Projects Delivered' },
    { value: 98, prefix: '', suffix: '%', label: 'Client Satisfaction' },
    { value: 1.5, prefix: '$', suffix: 'M+', label: 'Revenue Generated', decimals: 1 },
  ];

  return (
    <section
      ref={sectionRef}
      className="relative min-h-screen w-full flex items-center justify-center overflow-hidden bg-[#f7f7f7] dark:bg-[#0a0a0a] transition-colors duration-500 pt-32 lg:pt-40"
    >
      {/* Subtle gradient background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#f7f7f7] dark:to-[#0a0a0a]" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-orange/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-orange/5 rounded-full blur-3xl" />
      </div>

      {/* 3D TorusKnot - Lazy loaded to reduce TBT */}
      <Suspense fallback={<div className="absolute right-0 top-1/2 -translate-y-1/2 w-[60%] h-[80%] hidden lg:block" />}>
        <TorusKnot3D />
      </Suspense>

      {/* Spinning Double Orbit Rings */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden flex items-center justify-center">
        {/* Outer orbit */}
        <div 
          ref={orbit1Ref}
          className="absolute w-[600px] h-[600px] lg:w-[800px] lg:h-[800px] opacity-0"
        >
          <div className="absolute inset-0 border border-orange/20 rounded-full" />
          <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 bg-orange/60 rounded-full blur-sm" />
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-3 h-3 bg-orange/40 rounded-full blur-sm" />
          <div className="absolute top-1/2 right-0 translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-orange/50 rounded-full blur-sm" />
        </div>
        
        {/* Inner orbit */}
        <div 
          ref={orbit2Ref}
          className="absolute w-[400px] h-[400px] lg:w-[500px] lg:h-[500px] opacity-0"
        >
          <div className="absolute inset-0 border border-orange/30 rounded-full" />
          <div className="absolute top-1/2 left-0 -translate-x-1/2 -translate-y-1/2 w-3 h-3 bg-orange/70 rounded-full blur-sm" />
          <div className="absolute top-1/2 right-0 translate-x-1/2 -translate-y-1/2 w-4 h-4 bg-orange/50 rounded-full blur-sm" />
        </div>
      </div>

      {/* Floating decorative props */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div 
          className="absolute top-[20%] left-[10%] w-24 h-24 border border-orange/20 rounded-full opacity-60"
          style={{ animation: 'float 8s ease-in-out infinite' }}
        />
        <div 
          className="absolute top-[30%] right-[15%] w-16 h-16 bg-orange/10 rounded-lg rotate-45 opacity-40"
          style={{ animation: 'float 10s ease-in-out infinite reverse' }}
        />
        <div 
          className="absolute bottom-[35%] left-[20%] w-32 h-1 bg-gradient-to-r from-transparent via-orange/30 to-transparent"
          style={{ animation: 'float 9s ease-in-out infinite' }}
        />
        <div 
          className="absolute bottom-[25%] right-[10%] w-20 h-20 border border-gray-300 dark:border-white/10 rounded-full opacity-30"
          style={{ animation: 'float 12s ease-in-out infinite' }}
        />
        
        {/* Grid pattern overlay */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,110,0,0.3) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255,110,0,0.3) 1px, transparent 1px)`,
            backgroundSize: '60px 60px'
          }}
        />
      </div>

      {/* Main Content - Centered - Higher z-index to stay above 3D */}
      <div className="relative z-20 text-center px-6 max-w-5xl mx-auto py-16">
        {/* Animated Logo */}
        <div className="mb-8">
          <LogoReveal />
        </div>

        {/* Main Headline - Static */}
        <h1
          ref={headlineRef}
          className="font-teko text-5xl sm:text-6xl md:text-7xl lg:text-8xl xl:text-9xl font-bold leading-[0.85] mb-8"
        >
          <span className="block text-gray-900 dark:text-white">
            LUXURY WEB
          </span>
          <span className="block text-orange">
            DESIGN
          </span>
          <span className="block text-gray-400 dark:text-white/30 text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-light mt-2">
            REDEFINED
          </span>
        </h1>

        {/* Subheadline */}
        <p
          ref={subheadRef}
          className="font-opensans text-lg sm:text-xl text-gray-600 dark:text-white/60 max-w-2xl mx-auto mb-12 leading-relaxed"
        >
          We craft conversion-focused digital experiences for Houston's 
          most ambitious businesses. No templates. No compromises.
        </p>

        {/* CTA - subtle hover effects */}
        <div ref={ctaRef}>
          <button
            onClick={scrollToWork}
            className="group relative inline-flex items-center gap-3 px-10 py-5 bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-opensans font-semibold rounded-full overflow-hidden transition-all duration-500 hover:shadow-xl hover:shadow-orange/10"
          >
            {/* Subtle shine effect on hover */}
            <span className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
            
            {/* Glow effect */}
            <span className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-r from-orange/0 via-orange/5 to-orange/0" />
            
            <span className="relative transform group-hover:scale-[1.02] transition-transform duration-300">Explore Our Work</span>
            <ArrowDown 
              size={18} 
              className="relative transform group-hover:translate-y-0.5 transition-transform duration-300" 
            />
          </button>
        </div>

        {/* Stats row - with counter animation */}
        <div className="mt-20 pt-12 border-t border-gray-200 dark:border-white/10">
          <div ref={statsRef} className="flex flex-wrap justify-center gap-12 sm:gap-16">
            {stats.map((stat, i) => (
              <div key={i} className="text-center">
                <div className="font-teko text-4xl sm:text-5xl font-bold text-gray-900 dark:text-white">
                  <CountUp 
                    end={stat.value} 
                    prefix={stat.prefix} 
                    suffix={stat.suffix}
                    decimals={stat.decimals || 0}
                    duration={2.5}
                  />
                </div>
                <div className="font-opensans text-xs uppercase tracking-[0.15em] text-gray-500 dark:text-white/40 mt-1">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Scroll hint */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-gray-400 dark:text-white/30">
        <span className="font-opensans text-xs tracking-widest uppercase">Scroll</span>
        <div className="w-px h-8 bg-gradient-to-b from-current to-transparent" />
      </div>

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          50% { transform: translateY(-15px) rotate(1deg); }
        }
      `}</style>
    </section>
  );
}
