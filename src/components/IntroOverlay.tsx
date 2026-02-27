import { useEffect, useState, useRef } from 'react';
import gsap from 'gsap';

const IntroOverlay = ({ onComplete }: { onComplete: () => void }) => {
  const [show, setShow] = useState(true);
  const pathsRef = useRef<SVGGElement>(null);

  useEffect(() => {
    const failsafe = setTimeout(() => {
      setShow(false);
      onComplete();
    }, 5000);

    // Set up stroke dash for drawing effect
    if (pathsRef.current) {
      const paths = pathsRef.current.querySelectorAll('path');
      paths.forEach((path) => {
        const length = path.getTotalLength();
        path.style.strokeDasharray = `${length}`;
        path.style.strokeDashoffset = `${length}`;
      });
    }

    const tl = gsap.timeline({
      onComplete: () => {
        clearTimeout(failsafe);
        setShow(false);
        onComplete();
      },
    });

    tl.fromTo('.intro-nex', { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4, ease: 'power3.out' })
      .fromTo('.intro-gen', { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4, ease: 'power3.out' }, '-=0.2')
      .fromTo('.intro-wireframe', { opacity: 0, scale: 0.95 }, { opacity: 1, scale: 1, duration: 0.4, ease: 'power2.out' }, '-=0.2')
      .to('.skyline-draw', { strokeDashoffset: 0, duration: 1.5, stagger: 0.08, ease: 'power1.inOut' }, '-=0.2')
      .to('.intro-progress', { scaleX: 1, duration: 1.2, ease: 'power2.inOut' }, '-=1.3')
      .to('.intro-content', { opacity: 0, y: -20, duration: 0.3 })
      .to('.intro-overlay', { yPercent: -100, duration: 0.4, ease: 'power3.inOut' });

    return () => clearTimeout(failsafe);
  }, [onComplete]);

  if (!show) return null;

  return (
    <div className="intro-overlay fixed inset-0 z-[9999] bg-[#0a0a0a] overflow-hidden">
      {/* Grid overlay */}
      <div className="absolute inset-0 opacity-10">
        <div className="w-full h-full" style={{
          backgroundImage: 'linear-gradient(#f9731620 1px, transparent 1px), linear-gradient(90deg, #f9731620 1px, transparent 1px)',
          backgroundSize: '40px 40px'
        }} />
      </div>

      <div className="intro-content absolute inset-0 flex flex-col items-center justify-center">
        {/* Reliant AI Typography */}
        <div className="flex items-baseline gap-3 mb-8">
          <span className="intro-nex font-teko text-6xl sm:text-8xl font-bold text-white">NEX</span>
          <span className="intro-gen font-teko text-6xl sm:text-8xl font-bold text-orange">GEN</span>
        </div>

        {/* Website wireframe with Houston skyline being sketched */}
        <div className="intro-wireframe w-[320px] sm:w-[480px] aspect-[16/10] border border-orange/30 rounded-lg overflow-hidden bg-black/60">
          {/* Browser chrome */}
          <div className="h-6 bg-white/5 border-b border-orange/20 flex items-center px-2 gap-1.5">
            <div className="w-2 h-2 rounded-full bg-red-500/60" />
            <div className="w-2 h-2 rounded-full bg-yellow-500/60" />
            <div className="w-2 h-2 rounded-full bg-green-500/60" />
            <div className="ml-2 flex-1 h-3 bg-white/5 rounded" />
          </div>
          
          {/* Content area with skyline sketch */}
          <div className="relative h-[calc(100%-24px)]">
            {/* Houston Skyline being drawn */}
            <svg className="absolute inset-0 w-full h-full" viewBox="0 0 480 240" preserveAspectRatio="xMidYMax slice">
              <defs>
                <linearGradient id="skylineGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#f97316" stopOpacity="0.9" />
                  <stop offset="100%" stopColor="#f97316" stopOpacity="0.3" />
                </linearGradient>
              </defs>
              <g ref={pathsRef} fill="none" stroke="url(#skylineGrad)" strokeWidth="1.5" strokeLinecap="round">
                {/* JPMorgan Chase Tower */}
                <path className="skyline-draw" d="M50 240 L50 90 L58 80 L66 90 L66 240" />
                {/* Wells Fargo */}
                <path className="skyline-draw" d="M85 240 L85 110 L115 110 L115 240" />
                <path className="skyline-draw" d="M90 125 L110 125 M90 145 L110 145" />
                {/* Heritage Plaza */}
                <path className="skyline-draw" d="M135 240 L135 120 L145 100 L155 120 L155 240" />
                {/* Bank of America */}
                <path className="skyline-draw" d="M180 240 L180 95 L190 75 L200 60 L210 75 L220 95 L220 240" />
                <path className="skyline-draw" d="M185 110 L215 110" />
                {/* Pennzoil Place twins */}
                <path className="skyline-draw" d="M245 240 L245 130 L265 95 L265 240" />
                <path className="skyline-draw" d="M280 240 L280 130 L300 95 L300 240" />
                {/* Williams Tower */}
                <path className="skyline-draw" d="M325 240 L325 70 L335 50 L345 70 L345 240" />
                <path className="skyline-draw" d="M330 65 L340 65" />
                {/* One Shell Plaza */}
                <path className="skyline-draw" d="M370 240 L370 105 L410 105 L410 240" />
                <path className="skyline-draw" d="M375 120 L405 120 M375 145 L405 145 M375 170 L405 170" />
                {/* Smaller buildings */}
                <path className="skyline-draw" d="M430 240 L430 150 L455 150 L455 240" />
                {/* Ground line */}
                <path className="skyline-draw" d="M30 240 L465 240" strokeWidth="2" />
              </g>
            </svg>
            
            {/* Wireframe UI elements */}
            <div className="absolute top-3 left-3 right-3">
              <div className="h-2 w-20 bg-orange/30 rounded" />
            </div>
            <div className="absolute bottom-3 left-3 flex gap-2">
              <div className="h-5 w-14 bg-orange/25 rounded" />
              <div className="h-5 w-14 bg-orange/15 rounded" />
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-6 w-32">
          <div className="h-0.5 bg-white/10 rounded-full overflow-hidden">
            <div className="intro-progress h-full bg-orange origin-left scale-x-0" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntroOverlay;
