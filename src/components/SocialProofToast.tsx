import { useState, useEffect, useRef, useCallback } from 'react';
import { MapPin, Building2, Clock, TrendingUp, Star, Users, Zap, X } from 'lucide-react';
import { usePopupTrigger } from '../hooks/usePopupTrigger';

// Influencer Matrix: Social Proof Stack
// - Volume: "150+ websites built"
// - Authority: Specific results and metrics
// - Peer Match: Industry-specific testimonials

interface ToastData {
  id: number;
  type: 'inquiry' | 'result' | 'review' | 'metric';
  message: string;
  location: string;
  time: string;
  industry: string;
  metric?: string;
  icon: typeof MapPin;
}

const toastSequence: ToastData[] = [
  {
    id: 1,
    type: 'inquiry',
    message: "A metal fabricator just requested a website quote",
    location: "Houston, TX",
    time: "Just now",
    industry: "Metal Fabrication",
    icon: Building2
  },
  {
    id: 2,
    type: 'result',
    message: "Martinez HVAC increased leads by 340%",
    metric: "+340% leads",
    location: "Dallas, TX",
    time: "2 hours ago",
    industry: "Home Services",
    icon: TrendingUp
  },
  {
    id: 3,
    type: 'review',
    message: "'Reliant AI delivered beyond our expectations' - Richardson Metal",
    location: "Houston, TX",
    time: "3 hours ago",
    industry: "Metal Fabrication",
    icon: Star
  },
  {
    id: 4,
    type: 'metric',
    message: "150+ websites launched since 2020",
    location: "Texas",
    time: "This week",
    industry: "All Industries",
    icon: Users
  },
  {
    id: 5,
    type: 'result',
    message: "Westside Medical reduced call volume by 40%",
    metric: "-40% calls",
    location: "Austin, TX",
    time: "5 hours ago",
    industry: "Healthcare",
    icon: Zap
  },
  {
    id: 6,
    type: 'inquiry',
    message: "An oilfield service company is viewing pricing",
    location: "Midland, TX",
    time: "Just now",
    industry: "Oilfield Services",
    icon: Building2
  }
];

// Timing pattern: First 3 toasts have shorter gaps, then 20s after the 3rd
// Toast display duration: 3.5 seconds
const DISPLAY_DURATION = 3500; // 3.5 seconds each toast is visible

const getNextInterval = (cycleCount: number): number => {
  // First 2 transitions (toasts 1→2 and 2→3): 5 seconds
  if (cycleCount < 2) return 5000; // 5 seconds
  // After 3rd toast (cycleCount >= 2): 20 seconds
  return 20000; // 20 seconds
};

const SocialProofToast = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [visible, setVisible] = useState(false);
  const startedRef = useRef(false);
  const cycleCountRef = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { canShow, markDismissed } = usePopupTrigger({ popupType: 'social' });

  const scheduleRef = useRef<() => void>(undefined);

  // Handle the cycling with variable timing
  const scheduleNextToast = useCallback(() => {
    // Get interval based on current cycle count
    const interval = getNextInterval(cycleCountRef.current);
    
    timeoutRef.current = setTimeout(() => {
      // Hide current toast
      setVisible(false);
      
      // Wait for exit animation, then show next
      setTimeout(() => {
        setCurrentIndex((prev) => (prev + 1) % toastSequence.length);
        setVisible(true);
        
        // Increment cycle count for next interval calculation
        cycleCountRef.current += 1;
        
        // Schedule the next one
        scheduleRef.current?.();
      }, 500); // Exit animation time
    }, interval + DISPLAY_DURATION); // Add display duration to interval
  }, []);

  useEffect(() => {
    scheduleRef.current = scheduleNextToast;
  }, [scheduleNextToast]);

  // Auto-hide each toast after DISPLAY_DURATION
  useEffect(() => {
    if (!visible) return;
    const hideTimer = setTimeout(() => setVisible(false), DISPLAY_DURATION);
    return () => clearTimeout(hideTimer);
  }, [visible]);

  // Start showing toasts when allowed
  useEffect(() => {
    if (!canShow || startedRef.current) return;
    startedRef.current = true;
    // Small delay before first toast appears
    setTimeout(() => setVisible(true), 500);
  }, [canShow]);

  // Start the cycling when component mounts
  useEffect(() => {
    if (!startedRef.current) return;

    // Schedule the first cycle
    scheduleNextToast();

    // Cleanup
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [scheduleNextToast]);

  const handleDismiss = () => {
    setVisible(false);
    markDismissed();
    // Clear any pending timeouts
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  };

  const toast = toastSequence[currentIndex];
  const Icon = toast.icon;

  if (!canShow && !visible) return null;

  return (
    <div 
      role="status"
      aria-live="polite"
      className={`fixed bottom-24 left-6 z-50 max-w-sm transition-all duration-500 ${
        visible 
          ? 'opacity-100 translate-x-0' 
          : 'opacity-0 -translate-x-4 pointer-events-none'
      }`}
    >
      <div className="bg-white dark:bg-dark-100 border border-gray-200 dark:border-white/10 rounded-xl shadow-xl p-4 hover:shadow-2xl transition-shadow cursor-default relative">
        {/* Dismiss Button */}
        <button
          onClick={handleDismiss}
          className="absolute top-2 right-2 p-1 text-gray-300 hover:text-gray-500 dark:hover:text-white/60 transition-colors"
          aria-label="Dismiss notifications"
        >
          <X size={14} />
        </button>

        <div className="flex items-start gap-3">
          {/* Icon with dynamic background */}
          <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
            toast.type === 'result' ? 'bg-green-100 dark:bg-green-500/20' :
            toast.type === 'review' ? 'bg-yellow-100 dark:bg-yellow-500/20' :
            toast.type === 'metric' ? 'bg-blue-100 dark:bg-blue-500/20' :
            'bg-orange/10'
          }`}>
            <Icon size={20} className={
              toast.type === 'result' ? 'text-green-600 dark:text-green-400' :
              toast.type === 'review' ? 'text-yellow-600 dark:text-yellow-400' :
              toast.type === 'metric' ? 'text-blue-600 dark:text-blue-400' :
              'text-orange'
            } />
          </div>
          
          <div className="flex-1 min-w-0 pr-4">
            {/* Message */}
            <p className="font-opensans text-sm text-gray-900 dark:text-white leading-snug">
              {toast.message}
            </p>
            
            {/* Metric Badge */}
            {toast.metric && (
              <span className="inline-block mt-1 px-2 py-0.5 bg-green-100 dark:bg-green-500/20 text-green-700 dark:text-green-300 text-xs font-semibold rounded">
                {toast.metric}
              </span>
            )}
            
            {/* Meta Info */}
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
              <span className="flex items-center gap-1">
                <MapPin size={12} />
                {toast.location}
              </span>
              <span className="flex items-center gap-1">
                <Clock size={12} />
                {toast.time}
              </span>
            </div>
            
            {/* Industry Tag */}
            <span className="inline-block mt-2 px-2 py-0.5 bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-white/60 text-xs rounded-full">
              {toast.industry}
            </span>
          </div>
        </div>
        
        {/* Verification Badge */}
        <div className="mt-3 pt-2 border-t border-gray-100 dark:border-white/5 flex items-center gap-2">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-xs text-gray-400">Verified activity</span>
        </div>
      </div>
    </div>
  );
};

export default SocialProofToast;
