import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Quote, Star, BadgeCheck } from 'lucide-react';
import CountUp from '../components/CountUp';

gsap.registerPlugin(ScrollTrigger);

const testimonials = [
  {
    id: 1,
    quote: "NexGen transformed our online presence completely. Within three months of launching our new website, we saw a 340% increase in quote requests. Their understanding of the metal fabrication industry is unmatched.",
    author: 'Michael Torres',
    role: 'CEO',
    company: 'Richardson Metal Works',
    industry: 'Metal Fabrication',
    rating: 5,
    verified: true,
    metric: '+340%',
    metricLabel: 'Lead increase',
  },
  {
    id: 2,
    quote: "Working with NexGen was a game-changer. They understood our HIPAA requirements and built a patient-friendly website that has significantly reduced our front-desk call volume by 40%. Online booking is now 60% of our appointments.",
    author: 'Sarah Chen',
    role: 'Practice Manager',
    company: 'Westside Medical Group',
    industry: 'Healthcare',
    rating: 5,
    verified: true,
    metric: '-40%',
    metricLabel: 'Call volume',
  },
  {
    id: 3,
    quote: "The team at NexGen delivered beyond our expectations. Our new website not only looks professional but actually brings in qualified leads. The monthly retainer keeps everything running smoothly—we've never had a single technical issue.",
    author: 'David Martinez',
    role: 'Operations Director',
    company: 'Martinez HVAC Services',
    industry: 'Home Services',
    rating: 5,
    verified: true,
    metric: '60%',
    metricLabel: 'Online bookings',
  },
];

const clientLogos = [
  'Richardson Metal',
  'Westside Medical',
  'Martinez HVAC',
  'Houston Oil Airs',
  'Texas Fabrication',
  'Premier Services',
];

export default function TestimonialsV2() {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const logosRef = useRef<HTMLDivElement>(null);
  const triggersRef = useRef<ScrollTrigger[]>([]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Header reveal
      const headerElements = headerRef.current?.querySelectorAll('.reveal-item');
      if (headerElements) {
        gsap.set(headerElements, { y: 40, opacity: 0 });
        
        const headerTrigger = ScrollTrigger.create({
          trigger: headerRef.current,
          start: 'top 85%',
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

      // Horizontal scroll
      const track = trackRef.current;
      if (!track) return;

      const cards = gsap.utils.toArray<HTMLElement>('.testi-card', track);
      if (cards.length === 0) return;

      const scrollAmount = track.scrollWidth - window.innerWidth;

      const pinTrigger = ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top top',
        end: () => `+=${scrollAmount}`,
        pin: true,
        scrub: 1,
        anticipatePin: 1,
        onUpdate: (self) => {
          gsap.set(track, { x: -scrollAmount * self.progress });

          // Parallax on inner elements
          cards.forEach((card) => {
            const quote = card.querySelector('.parallax-quote') as HTMLElement;
            const metric = card.querySelector('.parallax-metric') as HTMLElement;
            if (quote) gsap.set(quote, { y: -30 * self.progress });
            if (metric) gsap.set(metric, { y: 20 * self.progress });
          });
        },
      });
      triggersRef.current.push(pinTrigger);

      // Logos reveal
      const logoElements = logosRef.current?.querySelectorAll('.logo-item');
      if (logoElements) {
        gsap.set(logoElements, { y: 20, opacity: 0 });

        const logosTrigger = ScrollTrigger.create({
          trigger: logosRef.current,
          start: 'top 90%',
          onEnter: () => {
            gsap.to(logoElements, {
              y: 0,
              opacity: 1,
              duration: 0.5,
              stagger: 0.08,
              ease: 'power2.out',
            });
          },
        });
        triggersRef.current.push(logosTrigger);
      }
    }, sectionRef);

    return () => {
      ctx.revert();
      triggersRef.current.forEach(t => t.kill());
      triggersRef.current = [];
    };
  }, []);

  return (
    <section
      id="testimonials"
      ref={sectionRef}
      className="relative bg-[#0a0a0a] text-white overflow-hidden"
    >
      {/* Background accent */}
      <div className="absolute inset-0">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-orange/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 h-screen flex flex-col justify-center">
        {/* Section Header */}
        <div ref={headerRef} className="text-center mb-12 px-6 pt-16">
          <span className="reveal-item text-xs uppercase tracking-[0.3em] text-white/40 font-opensans block mb-4">
            Client Success
          </span>
          <h2 className="reveal-item font-teko text-5xl sm:text-6xl lg:text-7xl font-bold leading-[0.9]">
            PROVEN
            <span className="text-orange"> RESULTS</span>
          </h2>
        </div>

        {/* Horizontal scroll track */}
        <div ref={trackRef} className="flex gap-8 pl-[10vw] pr-[10vw] will-change-transform">
          {testimonials.map((t) => (
            <div
              key={t.id}
              className="testi-card flex-shrink-0 w-[85vw] sm:w-[70vw] lg:w-[50vw] bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-8 lg:p-12 relative"
            >
              {/* Quote Icon - parallax layer */}
              <div className="parallax-quote absolute -top-6 left-8 lg:left-12 will-change-transform">
                <div className="w-12 h-12 bg-orange rounded-xl flex items-center justify-center">
                  <Quote size={24} className="text-white" />
                </div>
              </div>

              <div className="pt-4">
                {/* Rating */}
                <div className="flex gap-1 mb-6">
                  {[...Array(t.rating)].map((_, i) => (
                    <Star key={i} size={16} className="text-orange fill-orange" />
                  ))}
                </div>

                {/* Quote */}
                <blockquote className="font-opensans text-xl lg:text-2xl text-white/90 leading-relaxed mb-8">
                  "{t.quote}"
                </blockquote>

                {/* Author + Metric */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6 pt-8 border-t border-white/10">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-gradient-to-br from-orange to-orange-600 rounded-full flex items-center justify-center font-teko text-2xl font-bold">
                      {t.author.charAt(0)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-teko text-xl font-bold">{t.author}</span>
                        {t.verified && <BadgeCheck size={18} className="text-blue-400" />}
                      </div>
                      <div className="text-sm text-white/50">
                        {t.role}, {t.company}
                      </div>
                      <div className="text-xs text-orange mt-1">{t.industry}</div>
                    </div>
                  </div>

                  {/* Metric - parallax layer */}
                  <div className="parallax-metric inline-flex flex-col items-start sm:items-end gap-1 px-4 py-3 bg-orange/10 border border-orange/30 rounded-xl min-w-[100px] will-change-transform">
                    <span className="text-2xl font-teko font-bold text-orange">
                      <CountUp end={t.metric} duration={1.5} />
                    </span>
                    <span className="text-xs font-opensans text-white/50 text-right">{t.metricLabel}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Scroll hint */}
        <div className="text-center mt-8 px-6" tabIndex={0} onKeyDown={(e) => {
          const track = trackRef.current;
          if (!track) return;
          const scrollAmount = track.scrollWidth - window.innerWidth;
          const current = parseFloat(gsap.getProperty(track, 'x') as string) || 0;
          const step = window.innerWidth * 0.5;
          if (e.key === 'ArrowRight') gsap.to(track, { x: Math.max(-scrollAmount, current - step), duration: 0.5 });
          if (e.key === 'ArrowLeft') gsap.to(track, { x: Math.min(0, current + step), duration: 0.5 });
        }}>
          <span className="text-xs uppercase tracking-[0.2em] text-white/20 font-opensans">
            Scroll to explore
          </span>
        </div>

        {/* Client Logos */}
        <div ref={logosRef} className="mt-12 px-6">
          <p className="text-center text-xs uppercase tracking-[0.2em] text-white/30 font-opensans mb-8">
            Trusted by Industry Leaders
          </p>
          <div className="flex flex-wrap justify-center items-center gap-8 lg:gap-16">
            {clientLogos.map((logo, i) => (
              <div
                key={i}
                className="logo-item font-teko text-xl lg:text-2xl text-white/20 transition-all duration-300 hover:text-white/50 cursor-default"
              >
                {logo}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
