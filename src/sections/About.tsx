import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Brain, Shield, GitBranch, Building2, BookOpen, Cpu } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const credentials = [
  { icon: Brain, label: 'AI Architect' },
  { icon: Shield, label: 'Cybersecurity' },
  { icon: GitBranch, label: 'Full-Stack Dev' },
  { icon: Building2, label: 'Operations' },
];

const projects = [
  {
    name: 'Houston Oil Airs',
    desc: 'AI research platform for environmental justice',
    tags: ['AI Research', '3D Visualization', 'Real-time Analytics'],
  },
  {
    name: 'C0Di3',
    desc: 'Autonomous cybersecurity threat detection agent',
    tags: ['Cybersecurity', 'AI Agent', 'Threat Analysis'],
  },
];

const About = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const leftColRef = useRef<HTMLDivElement>(null);
  const rightColRef = useRef<HTMLDivElement>(null);
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

      // Name character animation
      const nameChars = headerRef.current?.querySelectorAll('.name-char');
      if (nameChars && nameChars.length > 0) {
        gsap.set(nameChars, { opacity: 0, y: 60, rotateX: -90 });

        const nameTrigger = ScrollTrigger.create({
          trigger: headerRef.current,
          start: 'top 80%',
          onEnter: () => {
            gsap.to(nameChars, {
              opacity: 1,
              y: 0,
              rotateX: 0,
              duration: 0.6,
              stagger: 0.04,
              ease: 'back.out(1.7)',
            });
          },
        });
        triggersRef.current.push(nameTrigger);
      }

      // Left column (profile card)
      if (leftColRef.current) {
        gsap.set(leftColRef.current, { x: -40, opacity: 0 });
        
        const leftTrigger = ScrollTrigger.create({
          trigger: leftColRef.current,
          start: 'top 85%',
          onEnter: () => {
            gsap.to(leftColRef.current, {
              x: 0,
              opacity: 1,
              duration: 0.9,
              ease: 'power3.out',
            });
          },
        });
        triggersRef.current.push(leftTrigger);
      }

      // Right column sections - staggered reveal
      const rightSections = rightColRef.current?.querySelectorAll('.right-section');
      if (rightSections) {
        rightSections.forEach((section) => {
          const elements = section.querySelectorAll('.section-reveal');
          gsap.set(section, { y: 40, opacity: 0 });
          gsap.set(elements, { y: 20, opacity: 0 });

          const sectionTrigger = ScrollTrigger.create({
            trigger: section,
            start: 'top 85%',
            onEnter: () => {
              gsap.to(section, {
                y: 0,
                opacity: 1,
                duration: 0.7,
                ease: 'power3.out',
              });
              gsap.to(elements, {
                y: 0,
                opacity: 1,
                duration: 0.5,
                stagger: 0.06,
                delay: 0.15,
                ease: 'power2.out',
              });
            },
          });
          triggersRef.current.push(sectionTrigger);
        });
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
      id="about"
      ref={sectionRef}
      className="relative w-full py-24 lg:py-32 bg-white dark:bg-black transition-colors duration-500"
    >
      <div className="relative z-10 w-full px-6 lg:px-12 xl:px-24">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div ref={headerRef} className="text-center mb-16">
            <span className="reveal-item inline-block px-4 py-1.5 bg-orange/10 border border-orange/30 rounded-full text-orange font-opensans text-sm mb-6">
              The Architect
            </span>
            <h2 className="reveal-item font-teko text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 dark:text-white mb-4 overflow-hidden">
              {'DOUGLAS'.split('').map((ch, i) => (
                <span key={`d${i}`} className="name-char inline-block" style={{ opacity: 0 }}>
                  {ch === ' ' ? '\u00A0' : ch}
                </span>
              ))}
              {'\u00A0'}
              {'MITCHELL'.split('').map((ch, i) => (
                <span key={`m${i}`} className="name-char inline-block gradient-text" style={{ opacity: 0 }}>
                  {ch}
                </span>
              ))}
            </h2>
            <p className="reveal-item font-opensans text-xl text-gray-600 dark:text-white/70 max-w-2xl mx-auto">
              Operations Manager · AI Architect · Full-Stack Developer
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16">
            {/* Left Column - Profile Card */}
            <div className="lg:col-span-5" ref={leftColRef}>
              <div className="bg-gradient-to-br from-gray-50 to-white dark:from-dark-100 dark:to-black border border-gray-200 dark:border-white/10 rounded-3xl p-8 sticky top-24 transition-all duration-500 hover:shadow-xl hover:shadow-orange/5 hover:border-orange/20">
                {/* Avatar */}
                <div className="text-center mb-8">
                  <div className="w-28 h-28 mx-auto bg-gradient-to-br from-orange to-orange-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-orange/20">
                    <span className="font-teko text-5xl font-bold text-white">DM</span>
                  </div>
                  <div className="flex items-center justify-center gap-2 text-gray-500 dark:text-white/50 font-opensans text-sm">
                    <Building2 size={14} />
                    <span>Houston, Texas</span>
                  </div>
                </div>

                {/* Credentials Grid */}
                <div className="grid grid-cols-2 gap-3 mb-8">
                  {credentials.map((item, i) => (
                    <div 
                      key={i} 
                      className="flex items-center gap-2 p-3 bg-white dark:bg-black/40 rounded-xl border border-gray-100 dark:border-white/5 transition-all duration-300 hover:border-orange/30 hover:bg-orange/5"
                    >
                      <item.icon size={18} className="text-orange flex-shrink-0" />
                      <span className="font-opensans text-sm text-gray-700 dark:text-white/80">{item.label}</span>
                    </div>
                  ))}
                </div>

                {/* Education */}
                <div className="p-4 bg-white dark:bg-black/40 rounded-xl border border-gray-100 dark:border-white/5 mb-6 transition-all duration-300 hover:border-orange/20">
                  <div className="flex items-start gap-3">
                    <BookOpen size={18} className="text-orange mt-0.5" />
                    <div>
                      <p className="font-opensans font-semibold text-gray-900 dark:text-white text-sm">Louisiana State University</p>
                      <p className="font-opensans text-xs text-gray-500 dark:text-white/50">BBA, Business Administration</p>
                    </div>
                  </div>
                </div>

                {/* CTA Buttons - subtle hover effects */}
                <div className="space-y-3">
                  <a
                    href="mailto:Douglas-D-Mitchell@outlook.com"
                    className="group flex items-center justify-center gap-2 w-full px-6 py-3 bg-orange text-white font-opensans font-semibold rounded-xl transition-all duration-300 hover:shadow-lg hover:shadow-orange/25 hover:scale-[1.02]"
                  >
                    Get in Touch
                  </a>
                  <a
                    href="tel:+18329477028"
                    className="group flex items-center justify-center gap-2 w-full px-6 py-3 border border-gray-200 dark:border-white/20 text-gray-900 dark:text-white font-opensans font-semibold rounded-xl transition-all duration-300 hover:bg-gray-50 dark:hover:bg-white/5 hover:border-orange/30"
                  >
                    (832) 947-7028
                  </a>
                </div>
              </div>
            </div>

            {/* Right Column - Story */}
            <div className="lg:col-span-7 space-y-10" ref={rightColRef}>
              {/* Philosophy */}
              <div className="right-section">
                <h3 className="section-reveal font-teko text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  WHERE OPERATIONS MEETS INNOVATION
                </h3>
                <div className="section-reveal space-y-4 font-opensans text-gray-600 dark:text-white/70 leading-relaxed">
                  <p>
                    I bridge the gap between <strong className="text-gray-900 dark:text-white">business strategy and technical execution</strong>. 
                    With a foundation in business administration and deep expertise in AI architecture, 
                    I build systems that don't just work—they scale.
                  </p>
                  <p>
                    At Houston Oil Airs, I manage operations for an AI research platform that combines 
                    <strong className="text-gray-900 dark:text-white"> immersive 3D environments, real-time analytics, 
                    and interactive network analysis</strong> to accelerate scientific discovery. We collaborate 
                    with research institutions globally to promote responsible AI development.
                  </p>
                </div>
              </div>

              {/* Projects */}
              <div className="right-section">
                <h3 className="section-reveal font-teko text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  BUILDING THE FUTURE
                </h3>
                <div className="space-y-4">
                  {projects.map((project, i) => (
                    <div 
                      key={i} 
                      className="section-reveal p-5 bg-gray-50 dark:bg-dark-100 border border-gray-100 dark:border-white/5 rounded-2xl transition-all duration-300 hover:border-orange/20 hover:shadow-lg hover:shadow-orange/5"
                    >
                      <div className="flex items-start gap-3 mb-3">
                        <Cpu size={20} className="text-orange mt-0.5" />
                        <div>
                          <h4 className="font-teko text-xl font-bold text-gray-900 dark:text-white">{project.name}</h4>
                          <p className="font-opensans text-sm text-gray-600 dark:text-white/60">{project.desc}</p>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2 ml-8">
                        {project.tags.map((tag, j) => (
                          <span 
                            key={j} 
                            className="px-2.5 py-1 bg-white dark:bg-black/40 border border-gray-200 dark:border-white/10 rounded-full font-opensans text-xs text-gray-600 dark:text-white/60 transition-all duration-300 hover:border-orange/30 hover:text-orange"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Skills */}
              <div className="right-section">
                <h3 className="section-reveal font-teko text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  CORE EXPERTISE
                </h3>
                <div className="section-reveal flex flex-wrap gap-2">
                  {['Software Development', 'Front-End Development', 'Artificial Intelligence', 'Cybersecurity', 'Back-End Development', 'Data Architecture', 'Operations Management', 'Process Optimization'].map((skill, i) => (
                    <span 
                      key={i} 
                      className="px-4 py-2 bg-orange/10 border border-orange/20 rounded-full font-opensans text-sm text-orange transition-all duration-300 hover:bg-orange hover:text-white hover:shadow-md hover:shadow-orange/20"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Author Note */}
              <div className="section-reveal p-6 bg-gradient-to-r from-orange/10 to-transparent border-l-4 border-orange rounded-r-2xl transition-all duration-300 hover:from-orange/15">
                <p className="font-opensans text-sm text-gray-600 dark:text-white/70 italic">
                  "Confidence isn't about luck, genetics, or pretending you have it together. 
                  It's a skill your brain can learn, strengthen, and sustain."
                </p>
                <p className="font-opensans text-xs text-gray-500 dark:text-white/50 mt-2">
                  — From "The Confident Mind" (2025)
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;
