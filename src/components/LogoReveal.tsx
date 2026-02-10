import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';

// Different complete design styles for NEX GEN
const designStyles = [
  {
    name: 'Bold Industrial',
    fontClass: 'font-teko',
    fontSize: 'text-7xl sm:text-8xl md:text-9xl lg:text-[10rem]',
    letterSpacing: '-0.03em',
    textTransform: 'uppercase',
    colorNex: 'text-gray-900 dark:text-white',
    colorGen: 'text-orange',
    weight: 'font-bold',
    extras: '',
  },
  {
    name: 'Elegant Modern',
    fontClass: 'font-opensans',
    fontSize: 'text-6xl sm:text-7xl md:text-8xl lg:text-[8rem]',
    letterSpacing: '0.15em',
    textTransform: 'uppercase',
    colorNex: 'text-orange',
    colorGen: 'text-gray-700 dark:text-gray-300',
    weight: 'font-light',
    extras: 'tracking-[0.2em]',
  },

  {
    name: 'Minimal Outline',
    fontClass: 'font-teko',
    fontSize: 'text-7xl sm:text-8xl md:text-9xl lg:text-[10rem]',
    letterSpacing: '0.05em',
    textTransform: 'uppercase',
    colorNex: 'text-transparent dark:text-transparent',
    colorGen: 'text-transparent dark:text-transparent',
    weight: 'font-bold',
    extras: 'style-text-outline',
  },
  {
    name: 'Neon Glow',
    fontClass: 'font-teko',
    fontSize: 'text-7xl sm:text-8xl md:text-9xl lg:text-[10rem]',
    letterSpacing: '-0.02em',
    textTransform: 'uppercase',
    colorNex: 'text-white',
    colorGen: 'text-orange',
    weight: 'font-bold',
    extras: 'style-neon-glow',
  },
];

const LogoReveal = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const lineRef = useRef<HTMLDivElement>(null);
  const cursorRef = useRef<HTMLSpanElement>(null);
  const [displayText, setDisplayText] = useState('');
  const [currentStyleIndex, setCurrentStyleIndex] = useState(0);
  const fullText = 'NEX GEN';

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    let currentIndex = 0;
    let isDeleting = false;
    let isActive = false;

    // Defer typewriter start to reduce TBT
    const startTyping = () => {
      isActive = true;
      typeEffect();
    };

    const typeEffect = () => {
      if (!isActive) return;
      if (!isDeleting) {
        // Typing
        if (currentIndex < fullText.length) {
          setDisplayText(fullText.slice(0, currentIndex + 1));
          currentIndex++;
          timeout = setTimeout(typeEffect, 150);
        } else {
          // Finished typing - pause then delete
          timeout = setTimeout(() => {
            isDeleting = true;
            typeEffect();
          }, 3000);
        }
      } else {
        // Deleting
        if (currentIndex > 0) {
          setDisplayText(fullText.slice(0, currentIndex - 1));
          currentIndex--;
          timeout = setTimeout(typeEffect, 80);
        } else {
          // Finished deleting - switch to completely different style
          isDeleting = false;
          setCurrentStyleIndex((prev) => (prev + 1) % designStyles.length);
          timeout = setTimeout(typeEffect, 500);
        }
      }
    };

    // Defer to reduce TBT
    timeout = setTimeout(startTyping, 1500);

    // Animate the underline
    const ctx = gsap.context(() => {
      gsap.fromTo(
        lineRef.current,
        { scaleX: 0, opacity: 0 },
        { scaleX: 1, opacity: 1, duration: 0.8, ease: 'power3.inOut', delay: 0.5 }
      );

      // Cursor blink
      gsap.to(cursorRef.current, {
        opacity: 0,
        duration: 0.5,
        repeat: -1,
        yoyo: true,
        ease: 'steps(1)',
      });
    }, containerRef);

    return () => {
      isActive = false;
      clearTimeout(timeout);
      ctx.revert();
    };
  }, []);

  const currentStyle = designStyles[currentStyleIndex];
  const nexPart = displayText.slice(0, 3);
  const genPart = displayText.slice(3);

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Logo Container - explicit height to prevent CLS */}
      <div 
        ref={containerRef}
        className="relative inline-block h-[120px] sm:h-[140px] md:h-[170px] lg:h-[180px]"
      >
        {/* Main text with typewriter effect and changing styles */}
        <div className="relative flex items-center justify-center h-full">
          <span
            className={`${currentStyle.fontClass} ${currentStyle.fontSize} ${currentStyle.weight} ${currentStyle.extras} transition-all duration-300`}
            style={{ 
              letterSpacing: currentStyle.letterSpacing,
              lineHeight: 0.85,
              textTransform: currentStyle.textTransform as React.CSSProperties['textTransform'],
            }}
          >
            {nexPart && (
              <span className={currentStyle.colorNex}>
                {nexPart}
              </span>
            )}
            {genPart && (
              <span className={currentStyle.colorGen}>
                {genPart}
              </span>
            )}
          </span>
          {/* Blinking cursor */}
          <span 
            ref={cursorRef}
            className="text-orange text-7xl sm:text-8xl md:text-9xl lg:text-[10rem] font-light ml-1"
            style={{ lineHeight: 0.85 }}
          >
            |
          </span>
        </div>
        
        {/* Animated underline */}
        <div 
          ref={lineRef}
          className="absolute -bottom-2 left-0 right-0 h-[3px] origin-left"
          style={{
            background: 'linear-gradient(90deg, transparent 0%, #f97316 20%, #f97316 80%, transparent 100%)',
            opacity: 0
          }}
        />
      </div>

      {/* Static subtitle underneath */}
      <div className="flex items-center gap-3 opacity-70">
        <div className="h-px w-8 bg-orange/50" />
        <span className="font-opensans text-xs sm:text-sm uppercase tracking-[0.25em] text-gray-500 dark:text-white/50">
          Houston Web Design Studio
        </span>
        <div className="h-px w-8 bg-orange/50" />
      </div>

      <style>{`
        .style-text-outline {
          -webkit-text-stroke: 2px #f97316;
        }
        
        .style-neon-glow {
          text-shadow: 
            0 0 10px rgba(249, 115, 22, 0.8),
            0 0 20px rgba(249, 115, 22, 0.6),
            0 0 40px rgba(249, 115, 22, 0.4),
            0 0 80px rgba(249, 115, 22, 0.2);
        }
      `}</style>
    </div>
  );
};

export default LogoReveal;
