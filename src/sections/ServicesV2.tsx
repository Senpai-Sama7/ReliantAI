import { useEffect, useRef, useState, useCallback } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Code2, Palette, TrendingUp, Box, ArrowRight } from 'lucide-react';

// Animated background SVG per service
const CardBackground = ({ index, mousePos }: { index: number; mousePos: { x: number; y: number } }) => {
  const ox = mousePos.x * 15;
  const oy = mousePos.y * 15;

  const patterns = [
    // Code - circuit board traces
    <g key="code" opacity="0.08">
      {[...Array(6)].map((_, i) => (
        <line key={i} x1={50 + i * 60 + ox * 0.3} y1="0" x2={80 + i * 60 + ox * 0.5} y2="300" stroke="#ff6e00" strokeWidth="1" />
      ))}
      {[...Array(4)].map((_, i) => (
        <circle key={`c${i}`} cx={100 + i * 80 + ox} cy={80 + i * 50 + oy} r="4" fill="#ff6e00" />
      ))}
    </g>,
    // Palette - color swatches / gradients
    <g key="palette" opacity="0.06">
      {[...Array(5)].map((_, i) => (
        <rect key={i} x={30 + i * 70 + ox * (0.2 + i * 0.1)} y={40 + i * 40 + oy * 0.3} width="40" height="40" rx="8" fill="#ff6e00" />
      ))}
    </g>,
    // Growth - ascending bars
    <g key="growth" opacity="0.07">
      {[...Array(7)].map((_, i) => (
        <rect key={i} x={30 + i * 50 + ox * 0.2} y={280 - (i + 1) * 35 + oy * 0.3} width="30" height={(i + 1) * 35} rx="4" fill="#ff6e00" />
      ))}
    </g>,
    // 3D - wireframe cube
    <g key="3d" opacity="0.08" transform={`translate(${ox * 0.5}, ${oy * 0.5})`}>
      <rect x="120" y="80" width="120" height="120" fill="none" stroke="#ff6e00" strokeWidth="1.5" />
      <rect x="160" y="50" width="120" height="120" fill="none" stroke="#ff6e00" strokeWidth="1" />
      <line x1="120" y1="80" x2="160" y2="50" stroke="#ff6e00" strokeWidth="1" />
      <line x1="240" y1="80" x2="280" y2="50" stroke="#ff6e00" strokeWidth="1" />
      <line x1="240" y1="200" x2="280" y2="170" stroke="#ff6e00" strokeWidth="1" />
      <line x1="120" y1="200" x2="160" y2="170" stroke="#ff6e00" strokeWidth="1" />
    </g>,
  ];

  return (
    <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 400 300" preserveAspectRatio="none">
      {patterns[index]}
    </svg>
  );
};

// Tilt card wrapper
const TiltCard = ({ children, index }: { children: React.ReactNode; index: number }) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setMousePos({
      x: ((e.clientX - rect.left) / rect.width - 0.5) * 2,
      y: ((e.clientY - rect.top) / rect.height - 0.5) * 2,
    });
  }, []);

  const tiltX = isHovered ? mousePos.y * -4 : 0;
  const tiltY = isHovered ? mousePos.x * 4 : 0;

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => { setIsHovered(false); setMousePos({ x: 0, y: 0 }); }}
      style={{
        transform: `perspective(800px) rotateX(${tiltX}deg) rotateY(${tiltY}deg)`,
        transition: isHovered ? 'transform 0.1s ease-out' : 'transform 0.4s ease-out',
      }}
      className="relative will-change-transform"
    >
      <CardBackground index={index} mousePos={isHovered ? mousePos : { x: 0, y: 0 }} />
      {/* Mouse glow */}
      {isHovered && (
        <div
          className="absolute w-48 h-48 rounded-full pointer-events-none z-0"
          style={{
            left: `${(mousePos.x + 1) * 50}%`,
            top: `${(mousePos.y + 1) * 50}%`,
            transform: 'translate(-50%, -50%)',
            background: 'radial-gradient(circle, rgba(255,110,0,0.08) 0%, transparent 70%)',
          }}
        />
      )}
      {children}
    </div>
  );
};

gsap.registerPlugin(ScrollTrigger);

const services = [
  {
    number: '01',
    icon: Code2,
    title: 'Custom Development',
    description: 'Hand-coded websites built from scratch. No templates, no compromises. Every line optimized for performance and conversions.',
    features: ['React/TypeScript', 'Headless CMS', 'API Integration', 'Performance Tuning'],
  },
  {
    number: '02',
    icon: Palette,
    title: 'Brand Identity',
    description: 'Visual systems that communicate prestige. From logo refinement to complete brand guidelines.',
    features: ['Visual Identity', 'Brand Guidelines', 'Asset Libraries', 'Style Systems'],
  },
  {
    number: '03',
    icon: TrendingUp,
    title: 'Growth Strategy',
    description: 'Data-driven optimization that turns visitors into customers. SEO, CRO, and analytics implementation.',
    features: ['SEO Optimization', 'Conversion Design', 'Analytics Setup', 'A/B Testing'],
  },
  {
    number: '04',
    icon: Box,
    title: '3D & Motion',
    description: 'Immersive experiences that set you apart. WebGL, 3D product showcases, and premium animations.',
    features: ['Three.js/WebGL', '3D Configurators', 'Motion Design', 'Interactive Elements'],
  },
];

export default function ServicesV2() {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const [activeService, setActiveService] = useState(0);
  const triggersRef = useRef<ScrollTrigger[]>([]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Header reveal
      const headerElements = headerRef.current?.querySelectorAll('.reveal-item');
      if (headerElements) {
        gsap.set(headerElements, { y: 40, opacity: 0 });
        
        const headerTrigger = ScrollTrigger.create({
          trigger: headerRef.current,
          start: 'top 92%',
          onEnter: () => {
            gsap.to(headerElements, {
              y: 0,
              opacity: 1,
              duration: 0.8,
              stagger: 0.1,
              ease: 'power3.out',
            });
          },
        });
        triggersRef.current.push(headerTrigger);
      }

      // Service items - staggered reveal
      const items = gsap.utils.toArray<HTMLElement>('[data-service-item]');
      
      items.forEach((item, i) => {
        const elements = item.querySelectorAll('.service-reveal');
        gsap.set(elements, { y: 30, opacity: 0 });
        gsap.set(item, { opacity: 0, y: 40 });

        const trigger = ScrollTrigger.create({
          trigger: item,
          start: 'top 92%',
          onEnter: () => {
            gsap.to(item, {
              opacity: 1,
              y: 0,
              duration: 0.6,
              ease: 'power3.out',
            });
            gsap.to(elements, {
              y: 0,
              opacity: 1,
              duration: 0.5,
              stagger: 0.06,
              delay: 0.1,
              ease: 'power2.out',
            });
          },
        });
        triggersRef.current.push(trigger);

        // Set active on scroll
        const activeTrigger = ScrollTrigger.create({
          trigger: item,
          start: 'top center',
          end: 'bottom center',
          onEnter: () => setActiveService(i),
          onEnterBack: () => setActiveService(i),
        });
        triggersRef.current.push(activeTrigger);
      });
    }, sectionRef);

    return () => {
      ctx.revert();
      triggersRef.current.forEach(t => t.kill());
      triggersRef.current = [];
    };
  }, []);

  return (
    <section
      id="services"
      ref={sectionRef}
      className="relative py-32 lg:py-40 bg-[#f7f7f7] dark:bg-[#0a0a0a] transition-colors duration-500"
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-12">
        {/* Section Header */}
        <div ref={headerRef} className="mb-20">
          <span className="reveal-item text-xs uppercase tracking-[0.3em] text-gray-500 dark:text-white/50 font-opensans block mb-4">
            Our Services
          </span>
          <h2 className="reveal-item font-teko text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 dark:text-white leading-[0.9]">
            WHAT WE
            <span className="text-orange"> DO</span>
          </h2>
        </div>

        {/* Services Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-px bg-gray-200 dark:bg-white/10">
          {services.map((service, i) => {
            const Icon = service.icon;
            const isActive = activeService === i;
            
            return (
              <TiltCard key={i} index={i}>
              <div
                data-service-item
                className={`group relative p-8 lg:p-12 bg-[#f7f7f7] dark:bg-[#0a0a0a] transition-all duration-500 cursor-pointer ${
                  isActive ? 'bg-white dark:bg-[#111]' : ''
                }`}
                onMouseEnter={() => setActiveService(i)}
              >
                {/* Number */}
                <span className="service-reveal absolute top-8 right-8 font-teko text-6xl font-bold text-gray-200 dark:text-white/5 group-hover:text-orange/10 transition-colors duration-500">
                  {service.number}
                </span>

                <div className="relative z-10">
                  {/* Icon - subtle hover effect */}
                  <div className="service-reveal w-12 h-12 bg-orange/10 rounded-xl flex items-center justify-center mb-6 transition-all duration-500 group-hover:bg-orange group-hover:shadow-lg group-hover:shadow-orange/20">
                    <Icon size={24} className="text-orange group-hover:text-white transition-colors duration-300" />
                  </div>

                  {/* Title */}
                  <h3 className="service-reveal font-teko text-3xl lg:text-4xl font-bold text-gray-900 dark:text-white mb-4 group-hover:text-orange transition-colors duration-300">
                    {service.title}
                  </h3>

                  {/* Description */}
                  <p className="service-reveal font-opensans text-gray-600 dark:text-white/60 mb-6 leading-relaxed">
                    {service.description}
                  </p>

                  {/* Features */}
                  <div className="service-reveal flex flex-wrap gap-2 mb-6">
                    {service.features.map((feature, j) => (
                      <span
                        key={j}
                        className="px-3 py-1 text-xs font-opensans text-gray-500 dark:text-white/50 bg-gray-100 dark:bg-white/5 rounded-full transition-all duration-300 group-hover:bg-orange/10 group-hover:text-orange"
                      >
                        {feature}
                      </span>
                    ))}
                  </div>

                  {/* Link - subtle underline hover */}
                  <a
                    href="#contact"
                    className="service-reveal inline-flex items-center gap-2 text-sm font-opensans font-semibold text-gray-900 dark:text-white transition-colors duration-300 group-hover:text-orange"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' });
                    }}
                  >
                    <span className="relative">
                      Learn more
                      <span className="absolute bottom-0 left-0 w-0 h-px bg-orange group-hover:w-full transition-all duration-300" />
                    </span>
                    <ArrowRight size={14} className="transform group-hover:translate-x-1 transition-transform duration-300" />
                  </a>
                </div>

                {/* Hover border effect */}
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-orange transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left" />
                
                {/* Subtle corner glow on hover */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-orange/0 group-hover:bg-orange/5 rounded-bl-full transition-all duration-700 pointer-events-none" />
              </div>
              </TiltCard>
            );
          })}
        </div>
      </div>
    </section>
  );
}
