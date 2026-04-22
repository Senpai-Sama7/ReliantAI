import { useEffect, useRef, useState, useCallback } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Mail, Phone, MapPin, ArrowUpRight, Instagram, Facebook, Linkedin } from 'lucide-react';
import { footerConfig } from '../config';

gsap.registerPlugin(ScrollTrigger);

// Icon mapping for social platforms
const iconMap: Record<string, typeof Instagram> = {
  instagram: Instagram,
  facebook: Facebook,
  linkedin: Linkedin,
};

// Magnetic Button Component
interface MagneticButtonProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

const MagneticButton = ({ children, className, onClick }: MagneticButtonProps) => {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const contentRef = useRef<HTMLSpanElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  
  const prefersReducedMotion = typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    if (!buttonRef.current || prefersReducedMotion) return;

    const rect = buttonRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const x = e.clientX - centerX;
    const y = e.clientY - centerY;

    // Move button slightly toward cursor
    gsap.to(buttonRef.current, {
      x: x * 0.25,
      y: y * 0.25,
      duration: 0.4,
      ease: 'power2.out',
    });

    // Move content slightly more for parallax effect
    if (contentRef.current) {
      gsap.to(contentRef.current, {
        x: x * 0.1,
        y: y * 0.1,
        duration: 0.4,
        ease: 'power2.out',
      });
    }
  }, [prefersReducedMotion]);

  const handleMouseLeave = useCallback(() => {
    if (!buttonRef.current || prefersReducedMotion) return;
    
    setIsHovered(false);
    
    // Elastic snap-back
    gsap.to(buttonRef.current, {
      x: 0,
      y: 0,
      duration: 0.8,
      ease: 'elastic.out(1, 0.3)',
    });

    if (contentRef.current) {
      gsap.to(contentRef.current, {
        x: 0,
        y: 0,
        duration: 0.8,
        ease: 'elastic.out(1, 0.3)',
      });
    }
  }, [prefersReducedMotion]);

  return (
    <button
      ref={buttonRef}
      className={`relative overflow-hidden transition-colors ${className}`}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      style={{ willChange: 'transform' }}
    >
      {/* Background fill on hover */}
      <span 
        className={`absolute inset-0 bg-genh-gold transition-transform duration-500 ease-out ${
          isHovered ? 'scale-100' : 'scale-0'
        }`}
        style={{ transformOrigin: 'center' }}
      />
      
      {/* Button content */}
      <span 
        ref={contentRef}
        className={`relative z-10 flex items-center gap-2 transition-colors duration-300 ${
          isHovered ? 'text-genh-black' : 'text-genh-gold'
        }`}
        style={{ willChange: 'transform' }}
      >
        {children}
      </span>
    </button>
  );
};

const Footer = () => {
  const sectionRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const logoRef = useRef<HTMLDivElement>(null);
  const triggersRef = useRef<ScrollTrigger[]>([]);

  const prefersReducedMotion = typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Set initial states
  useEffect(() => {
    const content = contentRef.current;
    const logo = logoRef.current;

    if (!content || !logo) return;

    if (prefersReducedMotion) {
      gsap.set(content.children, { opacity: 1, y: 0 });
      gsap.set(logo, { opacity: 1, y: 0 });
      return;
    }

    gsap.set(content.children, { opacity: 0, y: 40 });
    gsap.set(logo, { opacity: 0, y: 60 });
  }, [prefersReducedMotion]);

  useEffect(() => {
    const content = contentRef.current;
    const logo = logoRef.current;

    if (!content || !logo) return;

    // Clean up previous triggers
    triggersRef.current.forEach(t => t.kill());
    triggersRef.current = [];

    if (prefersReducedMotion) {
      gsap.set(content.children, { opacity: 1, y: 0 });
      gsap.set(logo, { opacity: 1, y: 0 });
      return;
    }

    // Content reveal with stagger
    const contentTrigger = ScrollTrigger.create({
      trigger: content,
      start: 'top 85%',
      once: true,
      onEnter: () => {
        gsap.fromTo(content.children, 
          { opacity: 0, y: 40 },
          { opacity: 1, y: 0, duration: 0.8, stagger: 0.1, ease: 'power3.out' }
        );
      },
    });
    triggersRef.current.push(contentTrigger);

    // Logo reveal
    const logoTrigger = ScrollTrigger.create({
      trigger: logo,
      start: 'top 95%',
      once: true,
      onEnter: () => {
        gsap.fromTo(logo, 
          { opacity: 0, y: 60 },
          { opacity: 1, y: 0, duration: 1, ease: 'power3.out' }
        );
      },
    });
    triggersRef.current.push(logoTrigger);

    return () => {
      triggersRef.current.forEach(t => t.kill());
      triggersRef.current = [];
    };
  }, [prefersReducedMotion]);

  if (!footerConfig.heading && !footerConfig.logoText) return null;

  return (
    <footer
      ref={sectionRef}
      className="relative w-full bg-genh-charcoal text-genh-white overflow-hidden"
      aria-label="Contact"
    >
      {/* Gradient overlay */}
      <div 
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at top, rgba(215, 160, 77, 0.05) 0%, transparent 50%)'
        }}
        aria-hidden="true"
      />

      {/* Content */}
      <div className="relative z-10">
        {/* Upper Section */}
        <div className="max-w-7xl mx-auto px-6 md:px-8 lg:px-12 pt-24 md:pt-32 pb-16">
          <div
            ref={contentRef}
            className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8"
          >
            {/* Left Column - CTA */}
            <div className="lg:col-span-5">
              <h2 
                className="font-display text-headline text-genh-white uppercase tracking-tight"
                style={{ lineHeight: 0.95, letterSpacing: '-0.02em' }}
              >
                {footerConfig.heading}
              </h2>
              <p className="font-body text-sm text-genh-gray/80 mt-6 max-w-md leading-relaxed">
                {footerConfig.description}
              </p>
              {footerConfig.ctaText && (
                <MagneticButton 
                  className="mt-8 px-8 py-4 border border-genh-gold font-body text-sm uppercase tracking-wider"
                >
                  {footerConfig.ctaText}
                  <ArrowUpRight className="w-4 h-4" />
                </MagneticButton>
              )}
            </div>

            {/* Right Column - Contact Grid */}
            <div className="lg:col-span-7">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Contact */}
                {footerConfig.contact.length > 0 && (
                  <div>
                    <h4 className="text-label mb-4">
                      Contact
                    </h4>
                    <ul className="space-y-3">
                      {footerConfig.contact.map((item, index) => (
                        <li key={index}>
                          <a
                            href={item.href}
                            className="group font-body text-sm text-genh-gray/80 hover:text-genh-gold transition-colors flex items-center gap-2"
                          >
                            {item.type === 'email' ? (
                              <Mail className="w-4 h-4 transition-transform group-hover:scale-110" />
                            ) : (
                              <Phone className="w-4 h-4 transition-transform group-hover:scale-110" />
                            )}
                            {item.label}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Address */}
                {footerConfig.address.length > 0 && (
                  <div>
                    <h4 className="text-label mb-4">
                      {footerConfig.locationLabel}
                    </h4>
                    <div className="flex items-start gap-2">
                      <MapPin className="w-4 h-4 text-genh-gray/80 mt-0.5 flex-shrink-0" />
                      <p className="font-body text-sm text-genh-gray/80 leading-relaxed">
                        {footerConfig.address.map((line, i) => (
                          <span key={i}>
                            {line}
                            {i < footerConfig.address.length - 1 && <br />}
                          </span>
                        ))}
                      </p>
                    </div>
                  </div>
                )}

                {/* Social */}
                {footerConfig.socials.length > 0 && (
                  <div>
                    <h4 className="text-label mb-4">
                      {footerConfig.socialLabel}
                    </h4>
                    <div className="flex gap-3">
                      {footerConfig.socials.map((social, index) => {
                        const Icon = iconMap[social.platform.toLowerCase()] || Instagram;
                        return (
                          <a
                            key={index}
                            href={social.href}
                            className="group w-10 h-10 border border-genh-white/20 flex items-center justify-center transition-all duration-300 hover:border-genh-gold hover:bg-genh-gold/10"
                            aria-label={social.platform}
                            style={{ clipPath: 'polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 0 100%)' }}
                          >
                            <Icon className="w-4 h-4 transition-transform duration-300 group-hover:scale-110" />
                          </a>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Large Watermark Logo */}
        {footerConfig.logoText && (
          <div
            ref={logoRef}
            className="border-t border-genh-white/10 py-12 md:py-16"
            style={{ willChange: 'transform, opacity' }}
          >
            <div className="max-w-7xl mx-auto px-6 md:px-8 lg:px-12">
              <svg
                viewBox="0 0 400 80"
                className="w-full max-w-4xl mx-auto h-auto opacity-[0.08]"
                fill="currentColor"
                aria-hidden="true"
              >
                <text
                  x="50%"
                  y="50%"
                  dominantBaseline="middle"
                  textAnchor="middle"
                  style={{
                    fontSize: '72px',
                    fontFamily: 'Montserrat, sans-serif',
                    fontWeight: 800,
                    letterSpacing: '0.1em'
                  }}
                >
                  {footerConfig.logoText}
                </text>
              </svg>
            </div>
          </div>
        )}

        {/* Bottom Bar */}
        <div className="border-t border-genh-white/10 py-6">
          <div className="max-w-7xl mx-auto px-6 md:px-8 lg:px-12 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="font-body text-xs text-genh-gray/50">
              {footerConfig.copyright}
            </p>
            {footerConfig.links.length > 0 && (
              <div className="flex gap-6">
                {footerConfig.links.map((link, index) => (
                  <a 
                    key={index} 
                    href={link.href} 
                    className="font-body text-xs text-genh-gray/50 hover:text-genh-gold transition-colors"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
