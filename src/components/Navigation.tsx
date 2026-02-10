import { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';
import gsap from 'gsap';
import { ScrollToPlugin } from 'gsap/ScrollToPlugin';
import ThemeToggle from './ThemeToggle';

gsap.registerPlugin(ScrollToPlugin);

const Navigation = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('hero');

  const navItems = [
    { label: 'Work', id: 'work' },
    { label: 'Services', id: 'services' },
    { label: 'About', id: 'about' },
    { label: 'FAQ', id: 'faq' },
    { label: 'Contact', id: 'contact' },
  ];

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 100);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Track active section based on scroll position
  useEffect(() => {
    const sections = navItems.map(item => document.getElementById(item.id));
    
    const handleScroll = () => {
      const scrollPos = window.scrollY + window.innerHeight / 3;
      
      sections.forEach((section, index) => {
        if (section) {
          const top = section.offsetTop;
          const bottom = top + section.offsetHeight;
          
          if (scrollPos >= top && scrollPos < bottom) {
            setActiveSection(navItems[index].id);
          }
        }
      });
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const scrollToSection = (sectionId: string) => {
    const section = document.getElementById(sectionId);
    if (section) {
      gsap.to(window, {
        duration: 1.2,
        scrollTo: { y: section, offsetY: 80 },
        ease: 'power3.inOut',
      });
    }
    setIsMobileMenuOpen(false);
  };

  return (
    <>
      <nav
        className={`fixed top-0 left-0 right-0 z-[100] transition-all duration-500 ${
          isScrolled
            ? 'bg-white/95 dark:bg-black/90 backdrop-blur-xl border-b border-gray-200 dark:border-white/10 shadow-sm'
            : 'bg-transparent'
        }`}
      >
        <div className="w-full px-6 lg:px-12">
          <div className="flex items-center justify-between h-20">
            {/* Logo */}
            <button
              onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
              className="flex items-center gap-2 group"
            >
              <div className="w-10 h-10 bg-orange rounded-lg flex items-center justify-center transition-all duration-300 group-hover:shadow-lg group-hover:shadow-orange/30">
                <span className="font-teko text-2xl font-bold text-white">N</span>
              </div>
              <span className="font-teko text-2xl font-semibold tracking-wide hidden sm:block text-gray-900 dark:text-white transition-colors duration-300">
                NEXGEN
              </span>
            </button>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center gap-8">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  className={`relative font-opensans text-sm transition-colors duration-300 group ${
                    activeSection === item.id
                      ? 'text-orange'
                      : 'text-gray-600 dark:text-white/70 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  {item.label}
                  <span className={`absolute -bottom-1 left-0 h-px bg-orange transition-all duration-300 ${
                    activeSection === item.id ? 'w-full' : 'w-0 group-hover:w-full'
                  }`} />
                </button>
              ))}
            </div>

            {/* CTA & Theme Toggle */}
            <div className="hidden lg:flex items-center gap-4">
              <ThemeToggle />
              <button
                onClick={() => scrollToSection('contact')}
                className="group relative px-6 py-2.5 bg-orange text-white font-opensans text-sm font-semibold rounded-lg overflow-hidden transition-all duration-300 hover:shadow-lg hover:shadow-orange/20"
              >
                <span className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
                <span className="relative">Get Started</span>
              </button>
            </div>

            {/* Mobile Menu Button */}
            <div className="flex items-center gap-3 lg:hidden">
              <a
                href="#contact"
                onClick={(e) => { e.preventDefault(); scrollToSection('contact'); }}
                className="px-3 py-1.5 bg-orange text-white font-opensans text-xs font-semibold rounded-lg"
              >
                Get a Quote
              </a>
              <ThemeToggle />
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="p-2 text-gray-900 dark:text-white transition-transform duration-300"
                aria-label="Toggle menu"
              >
                {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      <div
        className={`fixed inset-0 z-40 bg-white/98 dark:bg-black/98 backdrop-blur-xl transition-all duration-500 lg:hidden ${
          isMobileMenuOpen ? 'opacity-100 visible' : 'opacity-0 invisible pointer-events-none'
        }`}
      >
        <div className="flex flex-col items-center justify-center h-full gap-8">
          {navItems.map((item, index) => (
            <button
              key={item.id}
              onClick={() => scrollToSection(item.id)}
              className={`font-teko text-4xl transition-all duration-300 ${
                activeSection === item.id
                  ? 'text-orange'
                  : 'text-gray-900 dark:text-white/80 hover:text-orange'
              }`}
              style={{
                transitionDelay: isMobileMenuOpen ? `${index * 0.05}s` : '0s',
                transform: isMobileMenuOpen ? 'translateY(0)' : 'translateY(20px)',
                opacity: isMobileMenuOpen ? 1 : 0,
              }}
            >
              {item.label}
            </button>
          ))}
          <button
            onClick={() => scrollToSection('contact')}
            className="mt-8 px-8 py-3 bg-orange text-white font-opensans text-lg font-semibold rounded-lg transition-all duration-300 hover:shadow-lg hover:shadow-orange/20"
            style={{
              transitionDelay: isMobileMenuOpen ? `${navItems.length * 0.05}s` : '0s',
              transform: isMobileMenuOpen ? 'translateY(0)' : 'translateY(20px)',
              opacity: isMobileMenuOpen ? 1 : 0,
            }}
          >
            Get Started
          </button>
        </div>
      </div>
    </>
  );
};

export default Navigation;
