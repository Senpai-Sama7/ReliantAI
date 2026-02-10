import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Send, Mail, Phone, MapPin, ArrowRight, CheckCircle, Loader2, Shield, Award, Building2 } from 'lucide-react';
import { z } from 'zod';
import { toast } from 'sonner';

const contactSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email'),
  company: z.string(),
  industry: z.string(),
  message: z.string().min(10, 'Message must be at least 10 characters'),
});

gsap.registerPlugin(ScrollTrigger);

const Contact = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const headingRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLFormElement>(null);
  const infoRef = useRef<HTMLDivElement>(null);
  const footerRef = useRef<HTMLElement>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    industry: '',
    message: '',
  });
  const triggersRef = useRef<ScrollTrigger[]>([]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Header reveal
      const headerElements = headingRef.current?.querySelectorAll('.reveal-item');
      if (headerElements) {
        gsap.set(headerElements, { y: 40, opacity: 0 });
        
        const headerTrigger = ScrollTrigger.create({
          trigger: headingRef.current,
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

      // Form reveal - slide from left
      if (formRef.current) {
        gsap.set(formRef.current, { x: -40, opacity: 0 });
        
        const formTrigger = ScrollTrigger.create({
          trigger: formRef.current,
          start: 'top 85%',
          onEnter: () => {
            gsap.to(formRef.current, {
              x: 0,
              opacity: 1,
              duration: 0.9,
              ease: 'power3.out',
            });
          },
        });
        triggersRef.current.push(formTrigger);
      }

      // Info reveal - slide from right
      const infoElements = infoRef.current?.querySelectorAll('.info-reveal');
      if (infoRef.current && infoElements) {
        gsap.set(infoRef.current, { x: 40, opacity: 0 });
        gsap.set(infoElements, { y: 20, opacity: 0 });
        
        const infoTrigger = ScrollTrigger.create({
          trigger: infoRef.current,
          start: 'top 85%',
          onEnter: () => {
            gsap.to(infoRef.current, {
              x: 0,
              opacity: 1,
              duration: 0.9,
              ease: 'power3.out',
            });
            gsap.to(infoElements, {
              y: 0,
              opacity: 1,
              duration: 0.5,
              stagger: 0.08,
              delay: 0.2,
              ease: 'power2.out',
            });
          },
        });
        triggersRef.current.push(infoTrigger);
      }

      // Footer reveal
      if (footerRef.current) {
        gsap.set(footerRef.current, { y: 30, opacity: 0 });
        
        const footerTrigger = ScrollTrigger.create({
          trigger: footerRef.current,
          start: 'top 95%',
          onEnter: () => {
            gsap.to(footerRef.current, {
              y: 0,
              opacity: 1,
              duration: 0.7,
              ease: 'power3.out',
            });
          },
        });
        triggersRef.current.push(footerTrigger);
      }
    }, sectionRef);

    return () => {
      triggersRef.current.forEach(st => st.kill());
      triggersRef.current = [];
      ctx.revert();
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = contactSchema.safeParse(formData);
    if (!result.success) {
      toast.error(result.error.issues[0].message);
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await fetch('https://api.web3forms.com/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_key: '2b257f48-fab5-45e2-abb5-11d6ba950f94',
          subject: 'New Contact Form Submission - NexGen',
          ...formData,
        }),
      });
      if (!res.ok) throw new Error();
      setIsSubmitted(true);
      toast.success('Message sent! We\'ll get back to you within 24 hours.');
      setTimeout(() => {
        setIsSubmitted(false);
        setFormData({ name: '', email: '', company: '', industry: '', message: '' });
      }, 3000);
    } catch {
      toast.error('Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const contactInfo = [
    { icon: Mail, label: 'Email', value: 'Douglas-D-Mitchell@outlook.com', href: 'mailto:Douglas-D-Mitchell@outlook.com' },
    { icon: Phone, label: 'Phone', value: '(832) 947-7028', href: 'tel:+18329477028' },
    { icon: MapPin, label: 'Location', value: 'Houston, TX', href: '#' },
  ];

  const trustBadges = [
    { icon: Shield, label: 'BBB Accredited', href: 'https://www.bbb.org' },
    { icon: Award, label: 'Clutch Top Agency', href: 'https://clutch.co' },
    { icon: Building2, label: 'Houston Chamber', href: 'https://www.houston.org' },
  ];

  return (
    <section
      id="contact"
      ref={sectionRef}
      className="relative min-h-screen w-full py-24 lg:py-32 bg-gray-50 dark:bg-black transition-colors duration-500"
    >
      <div className="absolute inset-0 bg-gradient-to-b from-gray-50 via-white to-gray-50 dark:from-black dark:via-dark-100 dark:to-black z-0" />

      <div className="absolute inset-0 z-0 opacity-5">
        <div
          className="w-full h-full"
          style={{
            backgroundImage: `linear-gradient(rgba(255, 110, 0, 0.3) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255, 110, 0, 0.3) 1px, transparent 1px)`,
            backgroundSize: '50px 50px',
          }}
        />
      </div>

      <div className="relative z-10 w-full px-6 lg:px-12 xl:px-24">
        <div ref={headingRef} className="text-center mb-16">
          <span className="reveal-item inline-block px-4 py-1.5 bg-orange/10 border border-orange/30 rounded-full text-orange font-opensans text-sm mb-6">
            Start Your Project
          </span>
          <h2 className="reveal-item font-teko text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 dark:text-white mb-6">
            LET'S<span className="gradient-text"> BUILD</span>
          </h2>
          <p className="reveal-item font-opensans text-lg text-gray-600 dark:text-white/60 max-w-2xl mx-auto">
            Ready to transform your online presence? Tell us about your project
            and we'll get back to you within 24 hours.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 max-w-6xl mx-auto">
          <form
            ref={formRef}
            onSubmit={handleSubmit}
            className="p-8 lg:p-10 bg-white dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 rounded-2xl backdrop-blur-sm shadow-lg dark:shadow-none transition-all duration-500 hover:shadow-xl hover:shadow-orange/5 hover:border-orange/20"
          >
            {isSubmitted ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="w-20 h-20 bg-orange/20 rounded-full flex items-center justify-center mb-6">
                  <CheckCircle size={40} className="text-orange" />
                </div>
                <h3 className="font-teko text-3xl font-bold text-gray-900 dark:text-white mb-3">Message Sent!</h3>
                <p className="font-opensans text-gray-600 dark:text-white/60">We'll get back to you within 24 hours.</p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
                  <div>
                    <label className="block font-opensans text-sm text-gray-600 dark:text-white/70 mb-2">Your Name *</label>
                    <input type="text" name="name" value={formData.name} onChange={handleChange} required
                      className="w-full px-4 py-3 bg-gray-50 dark:bg-black/50 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-white/30 focus:border-orange focus:ring-1 focus:ring-orange/20 transition-all duration-300"
                      placeholder="John Smith" />
                  </div>
                  <div>
                    <label className="block font-opensans text-sm text-gray-600 dark:text-white/70 mb-2">Email Address *</label>
                    <input type="email" name="email" value={formData.email} onChange={handleChange} required
                      className="w-full px-4 py-3 bg-gray-50 dark:bg-black/50 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-white/30 focus:border-orange focus:ring-1 focus:ring-orange/20 transition-all duration-300"
                      placeholder="john@company.com" />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
                  <div>
                    <label className="block font-opensans text-sm text-gray-600 dark:text-white/70 mb-2">Company Name</label>
                    <input type="text" name="company" value={formData.company} onChange={handleChange}
                      className="w-full px-4 py-3 bg-gray-50 dark:bg-black/50 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-white/30 focus:border-orange focus:ring-1 focus:ring-orange/20 transition-all duration-300"
                      placeholder="Your Company" />
                  </div>
                  <div>
                    <label className="block font-opensans text-sm text-gray-600 dark:text-white/70 mb-2">Industry</label>
                    <select name="industry" value={formData.industry} onChange={handleChange}
                      className="w-full px-4 py-3 bg-gray-50 dark:bg-black/50 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white focus:border-orange focus:ring-1 focus:ring-orange/20 transition-all duration-300 appearance-none cursor-pointer">
                      <option value="" className="bg-white dark:bg-dark-100">Select Industry</option>
                      <option value="metal" className="bg-white dark:bg-dark-100">Metal Fabrication</option>
                      <option value="oilfield" className="bg-white dark:bg-dark-100">Oilfield Services</option>
                      <option value="home" className="bg-white dark:bg-dark-100">Home Services</option>
                      <option value="medical" className="bg-white dark:bg-dark-100">Medical/Healthcare</option>
                      <option value="other" className="bg-white dark:bg-dark-100">Other</option>
                    </select>
                  </div>
                </div>

                <div className="mb-6">
                  <label className="block font-opensans text-sm text-gray-600 dark:text-white/70 mb-2">Tell Us About Your Project *</label>
                  <textarea name="message" value={formData.message} onChange={handleChange} required rows={5}
                    className="w-full px-4 py-3 bg-gray-50 dark:bg-black/50 border border-gray-200 dark:border-white/10 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-white/30 focus:border-orange focus:ring-1 focus:ring-orange/20 transition-all duration-300 resize-none"
                    placeholder="What are your goals? What challenges are you facing?" />
                </div>

                <button type="submit" disabled={isSubmitting}
                  className="group w-full py-4 bg-orange text-white font-opensans font-semibold rounded-lg flex items-center justify-center gap-3 transition-all duration-300 hover:bg-orange-600 hover:shadow-lg hover:shadow-orange/25 disabled:opacity-50 disabled:cursor-not-allowed">
                  {isSubmitting ? (<><Loader2 size={20} className="animate-spin" />Sending...</>) : (<>Send Message<Send size={18} className="transform group-hover:translate-x-1 transition-transform duration-300" /></>)}
                </button>
              </>
            )}
          </form>

          <div ref={infoRef} className="flex flex-col justify-between">
            <div>
              <h3 className="info-reveal font-teko text-3xl font-bold text-gray-900 dark:text-white mb-6">Get in Touch</h3>
              <p className="info-reveal font-opensans text-gray-600 dark:text-white/60 mb-8 leading-relaxed">
                Have questions about our services or want to discuss your project? We're here to help.
              </p>

              <div className="space-y-6 mb-12">
                {contactInfo.map((item, index) => {
                  const Icon = item.icon;
                  return (
                    <a key={index} href={item.href} className="info-reveal flex items-center gap-4 group">
                      <div className="w-12 h-12 bg-orange/10 rounded-xl flex items-center justify-center transition-all duration-300 group-hover:bg-orange/20 group-hover:scale-105">
                        <Icon size={20} className="text-orange" />
                      </div>
                      <div>
                        <div className="font-opensans text-sm text-gray-500 dark:text-white/50">{item.label}</div>
                        <div className="font-opensans text-gray-900 dark:text-white transition-colors duration-300 group-hover:text-orange">{item.value}</div>
                      </div>
                    </a>
                  );
                })}
              </div>
            </div>

            <div className="info-reveal p-6 bg-orange/10 border border-orange/30 rounded-xl transition-all duration-300 hover:border-orange/50 hover:shadow-lg hover:shadow-orange/10">
              <h4 className="font-teko text-xl font-bold text-gray-900 dark:text-white mb-2">Prefer to talk?</h4>
              <p className="font-opensans text-gray-600 dark:text-white/60 text-sm mb-4">
                Schedule a free 30-minute consultation to discuss your project.
              </p>
              <button onClick={() => window.location.href = 'tel:+18329477028'}
                className="group inline-flex items-center gap-2 text-orange font-opensans font-semibold text-sm transition-all duration-300">
                <span className="relative">
                  Book a Call
                  <span className="absolute bottom-0 left-0 w-0 h-px bg-orange group-hover:w-full transition-all duration-300" />
                </span>
                <ArrowRight size={16} className="transform group-hover:translate-x-1 transition-transform duration-300" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Footer with Trust Badges */}
      <footer ref={footerRef} className="relative z-10 mt-24 pt-12 border-t border-gray-200 dark:border-white/10">
        <div className="w-full px-6 lg:px-12 xl:px-24">
          {/* Trust Badges */}
          <div className="flex flex-wrap justify-center gap-6 mb-8">
            {trustBadges.map((badge, index) => {
              const Icon = badge.icon;
              return (
                <a
                  key={index}
                  href={badge.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 rounded-full transition-all duration-300 hover:border-orange/50 hover:shadow-md hover:shadow-orange/10"
                >
                  <Icon size={16} className="text-orange" />
                  <span className="font-opensans text-sm text-gray-600 dark:text-white/70">{badge.label}</span>
                </a>
              );
            })}
          </div>

          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-orange rounded-lg flex items-center justify-center">
                <span className="font-teko text-2xl font-bold text-white">N</span>
              </div>
              <span className="font-teko text-2xl font-semibold tracking-wide text-gray-900 dark:text-white">NEXGEN</span>
            </div>

            <p className="font-opensans text-sm text-gray-500 dark:text-white/40 text-center">
              © 2026 NexGen Web Solutions. All rights reserved.
            </p>

            <div className="flex gap-6">
              <a href="/privacy-policy"
                className="font-opensans text-sm text-gray-500 dark:text-white/40 hover:text-gray-900 dark:hover:text-white transition-colors duration-300 relative group">
                Privacy Policy
                <span className="absolute bottom-0 left-0 w-0 h-px bg-orange group-hover:w-full transition-all duration-300" />
              </a>
              <a href="/terms-of-service"
                className="font-opensans text-sm text-gray-500 dark:text-white/40 hover:text-gray-900 dark:hover:text-white transition-colors duration-300 relative group">
                Terms of Service
                <span className="absolute bottom-0 left-0 w-0 h-px bg-orange group-hover:w-full transition-all duration-300" />
              </a>
              <a href="/sitemap.xml"
                className="font-opensans text-sm text-gray-500 dark:text-white/40 hover:text-gray-900 dark:hover:text-white transition-colors duration-300 relative group">
                Sitemap
                <span className="absolute bottom-0 left-0 w-0 h-px bg-orange group-hover:w-full transition-all duration-300" />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </section>
  );
};

export default Contact;
