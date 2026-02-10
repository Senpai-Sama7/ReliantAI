import { useEffect, useRef, useState, useCallback } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ArrowRight } from 'lucide-react';
import CountUp from '../components/CountUp';

// Interactive SVG overlays per industry
const IndustryAnimation = ({ index, mousePos }: { index: number; mousePos: { x: number; y: number } }) => {
  const ox = mousePos.x * 20;
  const oy = mousePos.y * 20;

  if (index === 0) {
    // Metal Fabrication - welding sparks
    return (
      <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 400 300">
        {[...Array(8)].map((_, i) => {
          const angle = (i / 8) * Math.PI * 2;
          const r = 40 + Math.abs(ox) * 0.5;
          return (
            <circle
              key={i}
              cx={200 + Math.cos(angle) * r + ox}
              cy={150 + Math.sin(angle) * r + oy}
              r={2 + (i % 3) * 0.5}
              fill="#ff6e00"
              opacity={0.6 + (i % 5) * 0.08}
            >
              <animate attributeName="opacity" values="1;0.2;1" dur={`${0.5 + i * 0.15}s`} repeatCount="indefinite" />
              <animate attributeName="r" values="2;4;2" dur={`${0.4 + i * 0.1}s`} repeatCount="indefinite" />
            </circle>
          );
        })}
        <line x1={200 + ox * 0.5} y1={150 + oy * 0.5} x2={200 + ox} y2={150 + oy} stroke="#ff6e00" strokeWidth="2" opacity="0.5">
          <animate attributeName="opacity" values="0.8;0.2;0.8" dur="0.3s" repeatCount="indefinite" />
        </line>
      </svg>
    );
  }

  if (index === 1) {
    // Oilfield - pump jack motion
    const swing = ox * 0.3;
    return (
      <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 400 300">
        {/* Derrick */}
        <line x1="200" y1="250" x2={180 + swing} y2="80" stroke="#ff6e00" strokeWidth="3" opacity="0.4" />
        <line x1="200" y1="250" x2={220 + swing} y2="80" stroke="#ff6e00" strokeWidth="3" opacity="0.4" />
        {/* Beam */}
        <line x1={140 + swing} y1={90 + oy * 0.2} x2={260 + swing} y2={90 - oy * 0.2} stroke="#ff6e00" strokeWidth="4" opacity="0.6" strokeLinecap="round" />
        {/* Head */}
        <circle cx={140 + swing} cy={90 + oy * 0.2} r="6" fill="#ff6e00" opacity="0.7">
          <animate attributeName="opacity" values="0.7;1;0.7" dur="2s" repeatCount="indefinite" />
        </circle>
        {/* Ground line */}
        <line x1="100" y1="250" x2="300" y2="250" stroke="#ff6e00" strokeWidth="1" opacity="0.2" />
      </svg>
    );
  }

  if (index === 2) {
    // Home Services - airflow particles
    return (
      <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 400 300">
        {[...Array(12)].map((_, i) => {
          const baseY = 60 + (i % 4) * 60;
          const baseX = 80 + Math.floor(i / 4) * 100;
          return (
            <g key={i}>
              <circle cx={baseX + ox * (0.3 + i * 0.05)} cy={baseY + oy * 0.2} r="3" fill="#ff6e00" opacity="0.3">
                <animate attributeName="cx" values={`${baseX};${baseX + 30};${baseX}`} dur={`${2 + i * 0.3}s`} repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.1;0.5;0.1" dur={`${2 + i * 0.3}s`} repeatCount="indefinite" />
              </circle>
              <path
                d={`M${baseX - 10 + ox * 0.2},${baseY} Q${baseX + 10},${baseY - 8 + oy * 0.1} ${baseX + 30 + ox * 0.3},${baseY}`}
                fill="none" stroke="#ff6e00" strokeWidth="1" opacity="0.2"
              >
                <animate attributeName="opacity" values="0.1;0.3;0.1" dur={`${2.5 + i * 0.2}s`} repeatCount="indefinite" />
              </path>
            </g>
          );
        })}
      </svg>
    );
  }

  // Medical - heartbeat pulse
  const pulseOffset = ox * 0.5;
  return (
    <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 400 300">
      <path
        d={`M 40,150 L ${120 + pulseOffset},150 L ${150 + pulseOffset},${100 + oy} L ${170 + pulseOffset},${200 - oy} L ${190 + pulseOffset},${120 + oy * 0.5} L ${210 + pulseOffset},150 L 360,150`}
        fill="none" stroke="#ff6e00" strokeWidth="2.5" opacity="0.5" strokeLinecap="round" strokeLinejoin="round"
      >
        <animate attributeName="opacity" values="0.3;0.7;0.3" dur="1.5s" repeatCount="indefinite" />
      </path>
      <circle cx={190 + pulseOffset} cy={120 + oy * 0.5} r="8" fill="none" stroke="#ff6e00" strokeWidth="1" opacity="0.3">
        <animate attributeName="r" values="8;20;8" dur="1.5s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.4;0;0.4" dur="1.5s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
};

gsap.registerPlugin(ScrollTrigger);

export interface Chapter {
  eyebrow: string;
  title: string;
  description: string;
  bullets: string[];
  stats: { value: string; label: string }[];
  visualSrc: string;
  visualAlt: string;
  theme: 'light' | 'warm' | 'dark';
}

interface PinnedStoryProps {
  chapters: Chapter[];
}

export default function PinnedStory({ chapters }: PinnedStoryProps) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const stageRef = useRef<HTMLDivElement | null>(null);
  const [active, setActive] = useState(0);
  const [isMobile, setIsMobile] = useState(false);
  const triggersRef = useRef<ScrollTrigger[]>([]);
  const activeRef = useRef(0);
  const chapterContentRefs = useRef<(HTMLDivElement | null)[]>([]);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePos({
      x: ((e.clientX - rect.left) / rect.width - 0.5) * 2,
      y: ((e.clientY - rect.top) / rect.height - 0.5) * 2,
    });
  }, []);

  // Detect mobile on mount
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024 || 'ontouchstart' in window);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile, { passive: true });
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    // Clear any existing triggers
    triggersRef.current.forEach(t => t.kill());
    triggersRef.current = [];

    const timer = setTimeout(() => {
      const root = rootRef.current;
      const stage = stageRef.current;
      if (!root || !stage) return;

      const ctx = gsap.context(() => {
        const chapterEls = gsap.utils.toArray<HTMLElement>('[data-chapter]');
        const stageVisuals = gsap.utils.toArray<HTMLElement>('[data-stage-visual]');

        if (chapterEls.length === 0 || stageVisuals.length === 0) return;

        // Set initial state
        gsap.set(stageVisuals, { opacity: 0, scale: 1.05 });
        gsap.set(stageVisuals[0], { opacity: 1, scale: 1 });

        // Only use pinning on desktop - NOT on mobile
        if (!isMobile) {
          const pinTrigger = ScrollTrigger.create({
            trigger: root,
            start: 'top top',
            end: () => `+=${chapterEls.length * window.innerHeight * 0.8}`,
            pin: stage,
            pinSpacing: true,
            scrub: 0.5,
          });
          triggersRef.current.push(pinTrigger);
        }

        // Create triggers for each chapter (works on both mobile and desktop)
        chapterEls.forEach((el, idx) => {
          const trigger = ScrollTrigger.create({
            trigger: el,
            start: isMobile ? 'top 60%' : 'top center',
            end: isMobile ? 'bottom 40%' : 'bottom center',
            onEnter: () => updateActive(idx),
            onEnterBack: () => updateActive(idx),
          });
          triggersRef.current.push(trigger);

          // Animate chapter content on entry
          const contentEl = chapterContentRefs.current[idx];
          if (contentEl) {
            const elements = contentEl.querySelectorAll('.reveal-item');
            gsap.set(elements, { y: 30, opacity: 0 });

            const contentTrigger = ScrollTrigger.create({
              trigger: el,
              start: 'top 85%',
              onEnter: () => {
                gsap.to(elements, {
                  y: 0,
                  opacity: 1,
                  duration: 0.6,
                  stagger: 0.06,
                  ease: 'power2.out',
                });
              },
            });
            triggersRef.current.push(contentTrigger);
          }
        });

        function updateActive(idx: number) {
          if (idx === activeRef.current) return;
          activeRef.current = idx;
          setActive(idx);

          // Animate visual transition
          gsap.to(stageVisuals, { 
            opacity: 0, 
            scale: 1.02,
            duration: 0.3,
            overwrite: true 
          });
          
          gsap.to(stageVisuals[idx], {
            opacity: 1,
            scale: 1,
            duration: 0.5,
            delay: 0.1,
            overwrite: true,
          });
        }
      }, root);

      return () => {
        ctx.revert();
      };
    }, 100);

    return () => {
      clearTimeout(timer);
      triggersRef.current.forEach(t => t.kill());
      triggersRef.current = [];
    };
  }, [chapters.length, isMobile]);

  const currentChapter = chapters[active];

  return (
    <div 
      ref={rootRef} 
      className="relative bg-[#f7f7f7] dark:bg-[#0a0a0a]"
      role="region"
      aria-label="Pinned case studies"
    >
      <div className={`grid grid-cols-1 ${isMobile ? '' : 'lg:grid-cols-2'} min-h-screen`}>
        {/* Stage - Left Side (or Top on Mobile) */}
        <div 
          ref={stageRef} 
          className={`relative ${isMobile ? 'h-[50vh]' : 'h-screen lg:h-screen'} flex items-center justify-center p-6 lg:p-16 bg-[#f7f7f7] dark:bg-[#0a0a0a]`}
        >
          {/* Background gradient based on theme */}
          <div 
            className={`absolute inset-0 transition-opacity duration-700 ${
              currentChapter?.theme === 'warm' ? 'bg-gradient-to-br from-orange-50/50 to-transparent dark:from-orange-950/20' :
              currentChapter?.theme === 'dark' ? 'bg-gradient-to-br from-gray-900 to-black' :
              'bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-black'
            }`}
          />

          {/* Stage visuals */}
          <div className="relative w-full max-w-md lg:max-w-lg aspect-[4/3] rounded-2xl overflow-hidden shadow-2xl group" onMouseMove={handleMouseMove}>
            {chapters.map((chapter, i) => (
              <div
                key={i}
                data-stage-visual
                className="absolute inset-0 will-change-transform"
                style={{ opacity: i === 0 ? 1 : 0 }}
              >
                <img
                  src={chapter.visualSrc}
                  alt={chapter.visualAlt}
                  width={512}
                  height={384}
                  className="w-full h-full object-cover transform transition-transform duration-700 group-hover:scale-[1.02]"
                  loading={i === 0 ? 'eager' : 'lazy'}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent" />
              </div>
            ))}
            <IndustryAnimation index={active} mousePos={mousePos} />
          </div>

          {/* Chapter counter - hidden on mobile */}
          <div className="hidden lg:block absolute bottom-8 left-8 font-teko text-8xl font-bold text-gray-200 dark:text-white/5 select-none">
            {String(active + 1).padStart(2, '0')}
          </div>
        </div>

        {/* Chapters - Right Side (or Below on Mobile) */}
        <div className="relative bg-[#f7f7f7] dark:bg-[#0a0a0a]">
          {chapters.map((chapter, i) => (
            <article
              key={i}
              data-chapter
              className={`${isMobile ? 'min-h-auto py-12' : 'min-h-screen'} flex items-center px-6 lg:px-16 py-12 lg:py-24 border-b border-gray-200 dark:border-white/10 last:border-b-0`}
            >
              <div 
                ref={(el) => { chapterContentRefs.current[i] = el; }}
                className="max-w-lg"
              >
                {/* Eyebrow */}
                <div className="reveal-item flex items-center gap-3 mb-6">
                  <span className="font-teko text-4xl lg:text-5xl text-orange/30">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span className="text-xs uppercase tracking-[0.2em] text-gray-500 dark:text-white/50 font-opensans">
                    {chapter.eyebrow}
                  </span>
                </div>

                {/* Title */}
                <h3 className="reveal-item font-teko text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-bold text-gray-900 dark:text-white mb-6 leading-[0.9]">
                  {chapter.title}
                </h3>

                {/* Description */}
                <p className="reveal-item font-opensans text-base lg:text-lg text-gray-600 dark:text-white/70 mb-8 lg:mb-10 leading-relaxed">
                  {chapter.description}
                </p>

                {/* Two Column Layout: Services + Stats */}
                <div className="reveal-item grid grid-cols-2 gap-6 lg:gap-8 mb-8 lg:mb-10">
                  {/* Services */}
                  <div>
                    <h4 className="text-xs uppercase tracking-[0.15em] text-gray-400 dark:text-white/40 font-opensans mb-4">
                      Services
                    </h4>
                    <ul className="space-y-2">
                      {chapter.bullets.map((bullet, j) => (
                        <li 
                          key={j} 
                          className="font-opensans text-sm text-gray-700 dark:text-white/80 flex items-start gap-2"
                        >
                          <span className="text-orange mt-1">—</span>
                          {bullet}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* ROI Stats with count-up animation */}
                  <div>
                    <h4 className="text-xs uppercase tracking-[0.15em] text-gray-400 dark:text-white/40 font-opensans mb-4">
                      Results
                    </h4>
                    <ul className="space-y-3">
                      {chapter.stats.map((stat, j) => (
                        <li key={j}>
                          <div className="font-teko text-2xl lg:text-3xl font-bold text-orange">
                            <CountUp 
                              end={stat.value}
                              duration={1.8}
                            />
                          </div>
                          <div className="font-opensans text-xs text-gray-500 dark:text-white/50">
                            {stat.label}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* CTA - subtle hover effect */}
                <a
                  href="#contact"
                  onClick={(e) => {
                    e.preventDefault();
                    document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                  className="reveal-item group inline-flex items-center gap-3 text-gray-900 dark:text-white font-opensans font-semibold transition-colors duration-300"
                >
                  <span className="relative">
                    Start Your Project
                    <span className="absolute bottom-0 left-0 w-0 h-px bg-orange group-hover:w-full transition-all duration-300" />
                  </span>
                  <ArrowRight 
                    size={18} 
                    className="transform group-hover:translate-x-1 transition-transform duration-300" 
                  />
                </a>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
