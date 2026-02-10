import { useEffect, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Navigation from './components/Navigation';
import IntroOverlay from './components/IntroOverlay';
import FloatingCTA from './components/FloatingCTA';
import ExitIntentPopup from './components/ExitIntentPopup';
import SocialProofToast from './components/SocialProofToast';
import SmoothScrollProvider from './components/SmoothScrollProvider';
import PrivacyPolicy from './pages/PrivacyPolicy';
import TermsOfService from './pages/TermsOfService';
import NotFound from './pages/NotFound';
import { useTheme } from './hooks/useTheme';
import { Toaster } from 'sonner';
import './App.css';

// Import sections
import HeroV2 from './sections/HeroV2';
import PinnedStory from './sections/PinnedStory';
import ServicesV2 from './sections/ServicesV2';
import TestimonialsV2 from './sections/TestimonialsV2';
import About from './sections/About';
import FAQ from './sections/FAQ';
import Contact from './sections/Contact';

import { caseStudyChapters } from './data/chapters';

gsap.registerPlugin(ScrollTrigger);

function App() {
  const { mounted } = useTheme();
  const [introComplete, setIntroComplete] = useState(false);

  // Check current path for routing
  const path = window.location.pathname;
  const isPrivacyPolicy = path === '/privacy-policy';
  const isTermsOfService = path === '/terms-of-service';
  const isSitemap = path === '/sitemap.xml';
  const isKnownPath = path === '/' || isPrivacyPolicy || isTermsOfService || isSitemap;
  const isStandalonePage = isPrivacyPolicy || isTermsOfService || isSitemap;

  useEffect(() => {
    if (isSitemap) {
      window.location.href = '/sitemap.xml';
    }
  }, [isSitemap]);

  useEffect(() => {
    if (isStandalonePage) return;
    // Refresh ScrollTrigger after content loads
    const timer = setTimeout(() => {
      ScrollTrigger.refresh();
    }, 500);

    return () => clearTimeout(timer);
  }, [isStandalonePage]);

  // Redirect sitemap.xml to the actual sitemap file
  if (isSitemap) {
    return null;
  }

  // Render standalone pages without the main layout
  if (isPrivacyPolicy) {
    return <PrivacyPolicy />;
  }

  if (isTermsOfService) {
    return <TermsOfService />;
  }

  if (!isKnownPath) {
    return <NotFound />;
  }

  if (!mounted) {
    return (
      <div className="min-h-screen bg-[#f7f7f7] dark:bg-[#0a0a0a] flex items-center justify-center">
        <div className="w-10 h-10 bg-orange rounded-lg flex items-center justify-center">
          <span className="font-teko text-2xl font-bold text-white">N</span>
        </div>
      </div>
    );
  }

  return (
    <SmoothScrollProvider>
      <a href="#main" className="skip-link">
        Skip to main content
      </a>
      {!introComplete && <IntroOverlay onComplete={() => setIntroComplete(true)} />}
      <FloatingCTA />
      <ExitIntentPopup />
      <SocialProofToast />
      <Toaster position="top-right" richColors />
      
      <div className="relative min-h-screen bg-[#f7f7f7] dark:bg-[#0a0a0a] text-gray-900 dark:text-white overflow-x-hidden">
        {/* Navigation */}
        <Navigation />

        {/* Main Content */}
        <main id="main" role="main" aria-label="Primary content">
          {/* Hero Section */}
          <HeroV2 />
          
          {/* Pinned Story / Case Studies */}
          <section id="work" aria-label="Case studies overview">
            <PinnedStory chapters={caseStudyChapters} />
          </section>
          
          {/* Services Section */}
          <ServicesV2 />
          
          {/* Testimonials Section */}
          <TestimonialsV2 />
          
          {/* About, FAQ, Contact */}
          <About />
          <FAQ />
          <Contact />
        </main>
      </div>
    </SmoothScrollProvider>
  );
}

export default App;
