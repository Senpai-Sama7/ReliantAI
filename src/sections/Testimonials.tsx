import { useCallback, useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Quote, ChevronLeft, ChevronRight, Star } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

interface Testimonial {
  id: number;
  name: string;
  role: string;
  company: string;
  industry: string;
  image: string;
  quote: string;
  rating: number;
}

const testimonials: Testimonial[] = [
  {
    id: 1,
    name: 'Michael Richardson',
    role: 'Owner',
    company: 'Richardson Metal Works',
    industry: 'Metal Fabrication',
    image: '/testimonial-1.jpg',
    quote:
      "NexGen transformed our online presence completely. Within three months of launching our new website, we saw a 40% increase in quote requests. Their understanding of the metal fabrication industry is unmatched.",
    rating: 5,
  },
  {
    id: 2,
    name: 'Sarah Chen',
    role: 'Practice Manager',
    company: 'Westside Medical Group',
    industry: 'Healthcare',
    image: '/testimonial-2.jpg',
    quote:
      "Working with NexGen was a breeze. They understood our HIPAA requirements and built a patient-friendly website that has significantly reduced our front-desk call volume. Online booking is now 60% of our appointments.",
    rating: 5,
  },
  {
    id: 3,
    name: 'David Martinez',
    role: 'Operations Director',
    company: 'Martinez HVAC Services',
    industry: 'Home Services',
    image: '/testimonial-3.jpg',
    quote:
      "The team at NexGen delivered beyond our expectations. Our new website not only looks professional but actually brings in qualified leads. The monthly retainer keeps everything running smoothly.",
    rating: 5,
  },
];

const Testimonials = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const headingRef = useRef<HTMLDivElement>(null);
  const carouselRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const scrollTriggersRef = useRef<ScrollTrigger[]>([]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Heading animation
      gsap.fromTo(
        headingRef.current,
        { y: 60, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: headingRef.current,
            start: 'top 95%',
            toggleActions: 'play none none reverse',
          },
        }
      );

      // Carousel animation
      gsap.fromTo(
        carouselRef.current,
        { y: 80, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: carouselRef.current,
            start: 'top 90%',
            toggleActions: 'play none none reverse',
          },
        }
      );
    }, sectionRef);

    return () => {
      scrollTriggersRef.current.forEach(st => st.kill());
      scrollTriggersRef.current = [];
      ctx.revert();
    };
  }, []);

  const goToNext = useCallback(() => {
    if (isAnimating) return;
    setIsAnimating(true);
    setActiveIndex((prev) => (prev + 1) % testimonials.length);
    setTimeout(() => setIsAnimating(false), 500);
  }, [isAnimating]);

  // Auto-rotate testimonials
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isAnimating) {
        goToNext();
      }
    }, 6000);

    return () => clearInterval(interval);
  }, [activeIndex, isAnimating, goToNext]);

  const goToPrev = () => {
    if (isAnimating) return;
    setIsAnimating(true);
    setActiveIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length);
    setTimeout(() => setIsAnimating(false), 500);
  };

  const goToSlide = (index: number) => {
    if (isAnimating || index === activeIndex) return;
    setIsAnimating(true);
    setActiveIndex(index);
    setTimeout(() => setIsAnimating(false), 500);
  };

  return (
    <section
      id="testimonials"
      ref={sectionRef}
      className="relative min-h-screen w-full py-24 lg:py-32 bg-white dark:bg-black transition-colors duration-500"
    >
      {/* Background */}
      <div className="absolute inset-0 bg-white dark:bg-black z-0" />
      <div className="absolute inset-0 bg-gradient-radial from-orange/5 via-transparent to-transparent z-0" />

      <div className="relative z-10 w-full px-6 lg:px-12 xl:px-24">
        {/* Section Header */}
        <div ref={headingRef} className="text-center mb-16">
          <span className="inline-block px-4 py-1.5 bg-orange/10 border border-orange/30 rounded-full text-orange font-opensans text-sm mb-6">
            Client Success Stories
          </span>
          <h2 className="font-teko text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 dark:text-white mb-6">
            WHAT OUR
            <span className="gradient-text"> CLIENTS SAY</span>
          </h2>
          <p className="font-opensans text-lg text-gray-600 dark:text-white/60 max-w-2xl mx-auto">
            Don't just take our word for it. Here's what business owners across
            industries have to say about working with NexGen.
          </p>
        </div>

        {/* Testimonials Carousel */}
        <div ref={carouselRef} className="max-w-5xl mx-auto">
          <div className="relative">
            {/* Main Testimonial Card */}
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-gray-50 to-white dark:from-dark-100 dark:to-black border border-gray-200 dark:border-white/10 p-8 lg:p-12 shadow-lg dark:shadow-none">
              {/* Quote Icon */}
              <div className="absolute top-8 right-8 lg:top-12 lg:right-12 opacity-10">
                <Quote size={120} className="text-orange" />
              </div>

              {/* Content */}
              <div className="relative z-10">
                {testimonials.map((testimonial, index) => (
                  <div
                    key={testimonial.id}
                    className={`transition-all duration-500 ${
                      index === activeIndex
                        ? 'opacity-100 translate-x-0'
                        : 'opacity-0 absolute inset-0 translate-x-8'
                    }`}
                  >
                    {/* Rating */}
                    <div className="flex gap-1 mb-6">
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <Star
                          key={i}
                          size={20}
                          className="text-orange fill-orange"
                        />
                      ))}
                    </div>

                    {/* Quote */}
                    <blockquote className="font-opensans text-xl lg:text-2xl text-gray-800 dark:text-white/90 leading-relaxed mb-8">
                      "{testimonial.quote}"
                    </blockquote>

                    {/* Author */}
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 rounded-full overflow-hidden border-2 border-orange/30">
                        <img
                          src={testimonial.image}
                          alt={testimonial.name}
                          className="w-full h-full object-cover"
                          loading="lazy"
                          decoding="async"
                        />
                      </div>
                      <div>
                        <div className="font-teko text-xl font-bold text-gray-900 dark:text-white">
                          {testimonial.name}
                        </div>
                        <div className="font-opensans text-sm text-gray-500 dark:text-white/60">
                          {testimonial.role}, {testimonial.company}
                        </div>
                        <div className="font-opensans text-xs text-orange mt-1">
                          {testimonial.industry}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Navigation */}
            <div className="flex items-center justify-between mt-8">
              {/* Dots */}
              <div className="flex gap-2">
                {testimonials.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => goToSlide(index)}
                    className={`w-3 h-3 rounded-full transition-all duration-300 ${
                      index === activeIndex
                        ? 'bg-orange w-8'
                        : 'bg-gray-300 dark:bg-white/20 hover:bg-gray-400 dark:hover:bg-white/40'
                    }`}
                  />
                ))}
              </div>

              {/* Arrows */}
              <div className="flex gap-3">
                <button
                  onClick={goToPrev}
                  className="w-12 h-12 rounded-full border border-gray-300 dark:border-white/20 flex items-center justify-center text-gray-600 dark:text-white/60 hover:text-gray-900 dark:hover:text-white hover:border-orange hover:bg-orange/10 transition-all duration-300"
                >
                  <ChevronLeft size={24} />
                </button>
                <button
                  onClick={goToNext}
                  className="w-12 h-12 rounded-full border border-gray-300 dark:border-white/20 flex items-center justify-center text-gray-600 dark:text-white/60 hover:text-gray-900 dark:hover:text-white hover:border-orange hover:bg-orange/10 transition-all duration-300"
                >
                  <ChevronRight size={24} />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Row */}
        <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
          {[
            { value: '150+', label: 'Projects Delivered' },
            { value: '98%', label: 'Client Satisfaction' },
            { value: '85%', label: 'Repeat Business' },
            { value: '4.9/5', label: 'Average Rating' },
          ].map((stat, index) => (
            <div key={index} className="text-center">
              <div className="font-teko text-4xl lg:text-5xl font-bold text-orange mb-2">
                {stat.value}
              </div>
              <div className="font-opensans text-sm text-gray-500 dark:text-white/50">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Testimonials;
