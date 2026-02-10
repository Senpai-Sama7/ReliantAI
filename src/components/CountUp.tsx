import { useEffect, useMemo, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

interface CountUpProps {
  end: number | string;
  prefix?: string;
  suffix?: string;
  duration?: number;
  className?: string;
  decimals?: number;
}

const CountUp = ({
  end,
  prefix = '',
  suffix = '',
  duration = 2,
  className = '',
  decimals = 0,
}: CountUpProps) => {
  const elementRef = useRef<HTMLSpanElement>(null);
  const hasAnimatedRef = useRef(false);

  // Parse the end value
  const { numericValue, displayPrefix, displaySuffix } = useMemo(() => {
    let numericValue = 0;
    let displaySuffix = suffix;
    let displayPrefix = prefix;

    if (typeof end === 'string') {
      const match = end.match(/[-+]?[\d.]+/);
      if (match) {
        numericValue = parseFloat(match[0]);
      }
      if (end.startsWith('+')) displayPrefix = '+';
      else if (end.startsWith('-')) displayPrefix = '-';
      else if (end.startsWith('$')) displayPrefix = '$';
      
      const suffixMatch = end.match(/[^-+\d.\s]+$/);
      if (suffixMatch && !suffix) {
        displaySuffix = suffixMatch[0];
      }
    } else {
      numericValue = end;
    }

    return { numericValue, displayPrefix, displaySuffix };
  }, [end, prefix, suffix]);

  // Compute initial display value
  const initialDisplay = useMemo(() => {
    const formatted = decimals > 0
      ? numericValue.toFixed(decimals)
      : Math.round(numericValue).toString();
    return `${displayPrefix}${formatted}${displaySuffix}`;
  }, [numericValue, displayPrefix, displaySuffix, decimals]);

  const [displayValue, setDisplayValue] = useState<string>(initialDisplay);

  useEffect(() => {
    const element = elementRef.current;
    if (!element || hasAnimatedRef.current) return;

    const obj = { value: 0 };

    const trigger = ScrollTrigger.create({
      trigger: element,
      start: 'top 90%',
      once: true,
      onEnter: () => {
        if (hasAnimatedRef.current) return;
        hasAnimatedRef.current = true;

        gsap.to(obj, {
          value: numericValue,
          duration: duration,
          ease: 'power2.out',
          onUpdate: () => {
            const formatted = decimals > 0 
              ? obj.value.toFixed(decimals)
              : Math.round(obj.value).toString();
            setDisplayValue(`${displayPrefix}${formatted}${displaySuffix}`);
          },
        });
      },
    });

    return () => {
      trigger.kill();
    };
  }, [numericValue, displayPrefix, displaySuffix, duration, decimals]);

  return (
    <span ref={elementRef} className={className}>
      {displayValue || `${displayPrefix}${numericValue}${displaySuffix}`}
    </span>
  );
};

export default CountUp;
