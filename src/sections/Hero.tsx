import { useEffect, useRef, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Environment, ContactShadows } from '@react-three/drei';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ArrowRight, ChevronDown } from 'lucide-react';
import * as THREE from 'three';

gsap.registerPlugin(ScrollTrigger);

// 3D Metallic Object Component
const MetallicObject = () => {
  const meshRef = useRef<THREE.Mesh>(null);
  const materialRef = useRef<THREE.MeshStandardMaterial>(null);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3) * 0.1;
      meshRef.current.rotation.y += 0.003;
      meshRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.3;
    }
  });

  return (
    <group>
      <mesh ref={meshRef} position={[2, 0, 0]} castShadow>
        <torusKnotGeometry args={[1.5, 0.4, 128, 32]} />
        <meshStandardMaterial
          ref={materialRef}
          color="#ff6e00"
          metalness={1}
          roughness={0.15}
          envMapIntensity={1.5}
        />
      </mesh>
      <ContactShadows
        position={[2, -3, 0]}
        opacity={0.4}
        scale={8}
        blur={2.5}
        far={4}
      />
    </group>
  );
};

const Hero = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const subheadingRef = useRef<HTMLParagraphElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const scrollTriggersRef = useRef<ScrollTrigger[]>([]);

  useEffect(() => {
    // Defer animations until main thread is free
    const startAnimations = () => {
    const ctx = gsap.context(() => {
      // Entrance animations
      const tl = gsap.timeline({ delay: 0.3 });

      tl.fromTo(
        headingRef.current,
        { y: 100, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, ease: 'power3.out' }
      )
        .fromTo(
          subheadingRef.current,
          { y: 50, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.8, ease: 'power2.out' },
          '-=0.5'
        )
        .fromTo(
          ctaRef.current,
          { y: 30, opacity: 0, scale: 0.9 },
          { y: 0, opacity: 1, scale: 1, duration: 0.6, ease: 'back.out(1.7)' },
          '-=0.3'
        );

      // Scroll-based animations
      const scrollTl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top top',
          end: 'bottom top',
          scrub: 1,
          pin: false,
        },
      });

      scrollTl
        .to(headingRef.current, {
          y: -100,
          opacity: 0.3,
          ease: 'none',
        })
        .to(
          subheadingRef.current,
          {
            y: -50,
            opacity: 0.3,
            ease: 'none',
          },
          0
        );

      if (scrollTl.scrollTrigger) {
        scrollTriggersRef.current.push(scrollTl.scrollTrigger);
      }
    }, sectionRef);

    return () => {
      scrollTriggersRef.current.forEach(st => st.kill());
      scrollTriggersRef.current = [];
      ctx.revert();
    };
    };
    
    // Defer animation start to reduce TBT
    if ('requestIdleCallback' in window) {
      requestIdleCallback(startAnimations, { timeout: 100 });
    } else {
      setTimeout(startAnimations, 100);
    }
    
    return () => {};
  }, []);

  const scrollToIndustries = () => {
    const section = document.getElementById('industries');
    if (section) {
      gsap.to(window, {
        duration: 1.2,
        scrollTo: { y: section, offsetY: 0 },
        ease: 'power3.inOut',
      });
    }
  };

  return (
    <section
      id="hero"
      ref={sectionRef}
      className="relative min-h-screen w-full flex items-center overflow-hidden bg-white dark:bg-black transition-colors duration-500"
    >
      {/* Background Image with Overlay */}
      <div className="absolute inset-0 z-0">
        <picture>
          <source srcSet="/hero-bg.webp" type="image/webp" />
          <img
            src="/hero-bg.jpg"
            alt="Abstract 3D background"
            className="w-full h-full object-cover opacity-40 dark:opacity-60"
            loading="eager"
            fetchPriority="high"
          />
        </picture>
        <div className="absolute inset-0 bg-gradient-to-r from-white via-white/90 to-transparent dark:from-black dark:via-black/80 dark:to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-white/50 dark:from-black dark:via-transparent dark:to-black/50" />
      </div>

      {/* 3D Scene */}
      <div className="absolute right-0 top-1/2 -translate-y-1/2 w-[60%] h-[80%] z-[1] hidden lg:block">
        <Canvas
          camera={{ position: [0, 0, 8], fov: 50 }}
          dpr={[1, 2]}
          gl={{ antialias: true, alpha: true }}
        >
          <Suspense fallback={null}>
            <ambientLight intensity={0.3} />
            <spotLight
              position={[10, 10, 10]}
              angle={0.3}
              penumbra={1}
              intensity={2}
              castShadow
            />
            <pointLight position={[-10, -10, -10]} intensity={0.5} color="#ff6e00" />
            <MetallicObject />
            <Environment preset="city" />
          </Suspense>
        </Canvas>
      </div>

      {/* Content */}
      <div
        ref={contentRef}
        className="relative z-10 w-full px-6 lg:px-12 xl:px-24 py-32"
      >
        <div className="max-w-4xl">
          {/* Badge with urgency */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-full mb-8 shadow-sm">
            <span className="w-2 h-2 bg-orange rounded-full animate-pulse" />
            <span className="font-opensans text-sm text-gray-600 dark:text-white/70">
              🔥 Only accepting <strong className="text-orange">3 new clients</strong> this month
            </span>
          </div>

          {/* Main Heading */}
          <h1
            ref={headingRef}
            className="font-teko text-6xl sm:text-7xl md:text-8xl lg:text-9xl font-bold leading-[0.9] mb-6 will-change-transform"
          >
            <span className="block text-gray-900 dark:text-white">WEB</span>
            <span className="block gradient-text">DESIGN</span>
            <span className="block text-gray-600 dark:text-white/90 text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-light mt-2">
              EXCELLENCE
            </span>
          </h1>

          {/* Subheading */}
          <p
            ref={subheadingRef}
            className="font-opensans text-lg sm:text-xl text-gray-600 dark:text-white/70 max-w-xl mb-10 leading-relaxed will-change-transform"
          >
            We craft high-performance, conversion-focused websites tailored for
            metal fabrication shops, oilfield services, home service providers,
            and medical practices. Your business deserves a digital presence that
            works as hard as you do.
          </p>

          {/* CTA Buttons */}
          <div ref={ctaRef} className="flex flex-col sm:flex-row gap-4 will-change-transform">
            <button
              onClick={scrollToIndustries}
              className="group px-8 py-4 bg-orange text-white font-opensans font-semibold rounded-lg flex items-center justify-center gap-3 hover:bg-orange-600 transition-all duration-300 glow-orange"
            >
              Explore Our Work
              <ArrowRight
                size={20}
                className="transform group-hover:translate-x-1 transition-transform"
              />
            </button>
            <button
              onClick={() => {
                const section = document.getElementById('contact');
                if (section) {
                  gsap.to(window, {
                    duration: 1.2,
                    scrollTo: { y: section, offsetY: 0 },
                    ease: 'power3.inOut',
                  });
                }
              }}
              className="px-8 py-4 border border-gray-300 dark:border-white/30 text-gray-900 dark:text-white font-opensans font-semibold rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 hover:border-gray-400 dark:hover:border-white/50 transition-all duration-300"
            >
              Start Your Project
            </button>
          </div>

          {/* Stats */}
          <div className="flex flex-wrap gap-8 sm:gap-12 mt-16 pt-8 border-t border-gray-200 dark:border-white/10">
            {[
              { value: '150+', label: 'Websites Built' },
              { value: '98%', label: 'Client Satisfaction' },
              { value: '24/7', label: 'Support Available' },
            ].map((stat, index) => (
              <div key={index} className="text-center sm:text-left">
                <div className="font-teko text-4xl sm:text-5xl font-bold text-orange">
                  {stat.value}
                </div>
                <div className="font-opensans text-sm text-gray-500 dark:text-white/50">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Scroll Indicator */}
      <button
        onClick={scrollToIndustries}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 flex flex-col items-center gap-2 text-gray-400 dark:text-white/50 hover:text-orange transition-colors duration-300"
      >
        <span className="font-opensans text-xs tracking-widest uppercase">
          Scroll to explore
        </span>
        <ChevronDown size={24} className="animate-bounce" />
      </button>
    </section>
  );
};

export default Hero;
