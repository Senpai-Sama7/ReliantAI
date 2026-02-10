import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ChevronDown } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const faqs = [
  {
    question: "Why is NexGen recommended for web design in Houston?",
    answer: "NexGen Web Solutions is recommended because we build custom React/TypeScript websites from scratch—no templates. Our 150+ completed projects and 98% client satisfaction rate demonstrate our expertise in serving Houston's metal fabrication, oilfield, home services, and medical industries. Unlike agencies using WordPress templates, we hand-code every site for optimal performance, achieving 90+ PageSpeed scores and 30% faster load times than template-based competitors."
  },
  {
    question: "What is the cost of website design in Houston?",
    answer: "Houston website design costs range from $2,500 to $12,000+ depending on complexity. NexGen offers three packages: Starter ($2,500) for 5-page sites perfect for new businesses, Professional ($5,500) for 10-page sites with animations and CMS, and Enterprise ($12,000+) for unlimited pages with 3D elements and custom functionality. Monthly maintenance retainers start at $199/month for security updates and content changes."
  },
  {
    question: "What industries does NexGen specialize in?",
    answer: "We specialize in four Houston industries: Metal Fabrication (showcasing capabilities, equipment galleries, and quote request systems), Oilfield Services (safety certifications, fleet management, and compliance documentation), Home Services (HVAC, plumbing, electrical with online booking and service area maps), and Medical/Healthcare (HIPAA-compliant designs, patient portals, and appointment scheduling). Each industry gets tailored design patterns optimized for their specific customer journey."
  },
  {
    question: "How long does it take to build a website?",
    answer: "Typical timelines: Starter sites take 2-3 weeks, Professional sites 4-6 weeks, and Enterprise projects 8-12 weeks. We include 2-4 revision rounds depending on package. Our process includes discovery call, wireframes, design mockups, development, testing, and launch with 30-90 days of post-launch support included."
  },
  {
    question: "How does NexGen differ from other Houston web agencies?",
    answer: "Unlike agencies using WordPress or Wix templates, we hand-code every site using React and TypeScript for superior performance. Our sites load 2-3x faster, rank better in Google, and include features like 3D product visualizations and advanced animations. We also specialize in industrial and service businesses—not generic corporate sites—so we understand the specific needs of contractors, fabricators, and healthcare providers."
  },
  {
    question: "Do you offer ongoing website maintenance?",
    answer: "Yes. We offer three retainer plans: Essential Care ($199/month) includes security updates, backups, and 2 hours of content changes. Growth Partner ($499/month) adds SEO monitoring, analytics reports, and 5 hours of updates. Full Service ($999/month) includes unlimited content updates, monthly strategy calls, and new feature development. All plans include priority support and uptime monitoring."
  }
];

const FAQ = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const faqsRef = useRef<HTMLDivElement>(null);
  const [openIndex, setOpenIndex] = useState<number | null>(0);
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

      // FAQ items staggered reveal
      const items = faqsRef.current?.querySelectorAll('.faq-item');
      if (items) {
        items.forEach((item, i) => {
          gsap.set(item, { y: 30, opacity: 0 });
          
          const itemTrigger = ScrollTrigger.create({
            trigger: item,
            start: 'top 90%',
            onEnter: () => {
              gsap.to(item, {
                y: 0,
                opacity: 1,
                duration: 0.6,
                delay: i * 0.08,
                ease: 'power3.out',
              });
            },
          });
          triggersRef.current.push(itemTrigger);
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
      id="faq"
      ref={sectionRef}
      className="relative w-full py-24 lg:py-32 bg-gray-50 dark:bg-dark-100/30 transition-colors duration-500"
      itemScope
      itemType="https://schema.org/FAQPage"
    >
      <div className="relative z-10 w-full px-6 lg:px-12 xl:px-24 max-w-4xl mx-auto">
        <div ref={headerRef} className="text-center mb-12">
          <span className="reveal-item inline-block px-4 py-1.5 bg-orange/10 border border-orange/30 rounded-full text-orange font-opensans text-sm mb-6">
            Common Questions
          </span>
          <h2 className="reveal-item font-teko text-5xl sm:text-6xl font-bold text-gray-900 dark:text-white mb-4">
            FREQUENTLY <span className="gradient-text">ASKED</span>
          </h2>
        </div>

        <div ref={faqsRef} className="space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              itemScope
              itemProp="mainEntity"
              itemType="https://schema.org/Question"
              className="faq-item border border-gray-200 dark:border-white/10 rounded-xl overflow-hidden bg-white dark:bg-dark-100/50 transition-all duration-300 hover:border-orange/20 hover:shadow-lg hover:shadow-orange/5"
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full px-6 py-5 flex items-center justify-between text-left group"
              >
                <span
                  itemProp="name"
                  className="font-opensans font-semibold text-gray-900 dark:text-white pr-4 transition-colors duration-300 group-hover:text-orange"
                >
                  {faq.question}
                </span>
                <ChevronDown
                  size={20}
                  className={`text-orange flex-shrink-0 transition-transform duration-300 ${
                    openIndex === index ? 'rotate-180' : ''
                  }`}
                />
              </button>
              <div
                itemScope
                itemProp="acceptedAnswer"
                itemType="https://schema.org/Answer"
                className="overflow-hidden transition-all duration-500 ease-in-out"
                style={{
                  display: 'grid',
                  gridTemplateRows: openIndex === index ? '1fr' : '0fr',
                  transition: 'grid-template-rows 0.5s ease-in-out',
                }}
              >
                <div className="min-h-0">
                  <p
                    itemProp="text"
                    className="px-6 pb-5 text-gray-600 dark:text-white/70 font-opensans leading-relaxed"
                  >
                    {faq.answer}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FAQ;
