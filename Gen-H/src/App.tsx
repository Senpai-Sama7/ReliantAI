import { useEffect, useRef, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import useLenis from './hooks/useLenis';
import { siteConfig } from './config';
import { AuthProvider } from './contexts/AuthContext';

// Lazy load admin components for code splitting
const AdminLogin = lazy(() => import('./sections/admin/AdminLogin'));
const AdminDashboard = lazy(() => import('./sections/admin/AdminDashboard'));
const ProtectedRoute = lazy(() => import('./components/ProtectedRoute'));

// Main sections
import Hero from './sections/Hero';
import NarrativeText from './sections/NarrativeText';
import CardStack from './sections/CardStack';
import BreathSection from './sections/BreathSection';
import ZigZagGrid from './sections/ZigZagGrid';
import Footer from './sections/Footer';

gsap.registerPlugin(ScrollTrigger);

// Loading fallback for admin routes
function AdminLoading() {
  return (
    <div className="min-h-screen bg-genh-black flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-genh-gold border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

// Main website component
function MainWebsite() {
  const mainRef = useRef<HTMLDivElement>(null);
  const snapTriggerRef = useRef<ScrollTrigger | null>(null);
  
  // Initialize Lenis smooth scrolling
  useLenis();

  useEffect(() => {
    if (siteConfig.language) {
      document.documentElement.lang = siteConfig.language;
    }

    // Setup global snap for pinned sections
    const setupSnap = () => {
      setTimeout(() => {
        const pinned = ScrollTrigger.getAll()
          .filter(st => st.vars.pin)
          .sort((a, b) => a.start - b.start);
        
        const maxScroll = ScrollTrigger.maxScroll(window);
        
        if (!maxScroll || pinned.length === 0) return;

        const pinnedRanges = pinned.map(st => ({
          start: st.start / maxScroll,
          end: (st.end ?? st.start) / maxScroll,
          center: (st.start + ((st.end ?? st.start) - st.start) * 0.5) / maxScroll,
        }));

        snapTriggerRef.current = ScrollTrigger.create({
          snap: {
            snapTo: (value: number) => {
              const inPinned = pinnedRanges.some(
                r => value >= r.start - 0.02 && value <= r.end + 0.02
              );
              
              if (!inPinned) return value;

              const target = pinnedRanges.reduce((closest, r) =>
                Math.abs(r.center - value) < Math.abs(closest - value) 
                  ? r.center 
                  : closest,
                pinnedRanges[0]?.center ?? 0
              );

              return target;
            },
            duration: { min: 0.18, max: 0.55 },
            delay: 0,
            ease: "power2.out",
          }
        });
      }, 100);
    };

    const handleLoad = () => {
      ScrollTrigger.refresh();
      setupSnap();
    };

    window.addEventListener('load', handleLoad);
    const setupTimeout = setTimeout(setupSnap, 500);

    return () => {
      window.removeEventListener('load', handleLoad);
      clearTimeout(setupTimeout);
      if (snapTriggerRef.current) {
        snapTriggerRef.current.kill();
      }
    };
  }, []);

  return (
    <div ref={mainRef} className="relative bg-genh-black">
      <div className="noise-overlay" aria-hidden="true" />
      <Hero />
      <NarrativeText />
      <CardStack />
      <BreathSection />
      <ZigZagGrid />
      <Footer />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Main Website */}
          <Route path="/" element={<MainWebsite />} />
          
          {/* Admin Routes */}
          <Route 
            path="/admin/login" 
            element={
              <Suspense fallback={<AdminLoading />}>
                <AdminLogin />
              </Suspense>
            } 
          />
          <Route 
            path="/admin" 
            element={
              <Suspense fallback={<AdminLoading />}>
                <ProtectedRoute>
                  <AdminDashboard />
                </ProtectedRoute>
              </Suspense>
            } 
          />
          
          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
