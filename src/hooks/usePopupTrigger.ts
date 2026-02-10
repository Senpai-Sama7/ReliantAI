import { useState, useEffect, useRef, useCallback } from 'react';

const TIME_THRESHOLD = 30000; // 30 seconds
const SCROLL_TIME_THRESHOLD = 10000; // 10 seconds of scrolling
const SESSION_KEYS = {
  exitPopup: 'exit_popup_dismissed',
  socialToast: 'social_toast_dismissed'
};

interface UsePopupTriggerOptions {
  popupType: 'exit' | 'social';
}

export const usePopupTrigger = ({ popupType }: UsePopupTriggerOptions) => {
  const sessionKey = SESSION_KEYS[popupType === 'exit' ? 'exitPopup' : 'socialToast'];
  const [canShow, setCanShow] = useState(false);
  const [dismissed, setDismissed] = useState(
    () => sessionStorage.getItem(sessionKey) === 'true'
  );
  const scrollTimeRef = useRef(0);
  const lastScrollTimeRef = useRef<number | null>(null);
  const rafIdRef = useRef<number | null>(null);

  const checkAndEnable = useCallback(() => {
    if (!dismissed && !canShow) {
      setCanShow(true);
    }
  }, [dismissed, canShow]);

  // Track scroll time
  useEffect(() => {
    if (dismissed) return;

    let isActive = true;

    const handleScrollStart = () => {
      if (lastScrollTimeRef.current === null) {
        lastScrollTimeRef.current = Date.now();
      }
    };

    const handleScrollEnd = () => {
      if (lastScrollTimeRef.current !== null) {
        const duration = Date.now() - lastScrollTimeRef.current;
        scrollTimeRef.current += duration;
        lastScrollTimeRef.current = null;
        
        // Check if we've met the scroll time threshold
        if (scrollTimeRef.current >= SCROLL_TIME_THRESHOLD) {
          checkAndEnable();
        }
      }
    };

    const handleScroll = () => {
      handleScrollStart();
      
      // Clear existing timeout
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
      
      // Set new timeout to detect scroll end
      rafIdRef.current = requestAnimationFrame(() => {
        // Wait a bit to confirm scroll has stopped
        setTimeout(() => {
          if (isActive) {
            handleScrollEnd();
          }
        }, 150);
      });
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    
    return () => {
      isActive = false;
      window.removeEventListener('scroll', handleScroll);
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, [dismissed, checkAndEnable]);

  // Check time-based threshold
  useEffect(() => {
    if (dismissed || canShow) return;

    const timer = setTimeout(() => {
      checkAndEnable();
    }, TIME_THRESHOLD);

    return () => clearTimeout(timer);
  }, [dismissed, canShow, checkAndEnable]);

  const markDismissed = useCallback(() => {
    sessionStorage.setItem(sessionKey, 'true');
    setDismissed(true);
    setCanShow(false);
  }, [sessionKey]);

  return {
    canShow,
    dismissed,
    markDismissed,
  };
};

export default usePopupTrigger;
