import { useState, useEffect } from 'react';
import { FileText, AlertTriangle, Users } from 'lucide-react';

const features = [
  { icon: FileText, label: 'Invoice & Statement Processing' },
  { icon: AlertTriangle, label: 'Escalation Detection' },
  { icon: Users, label: 'Team Visibility' },
];

export function LandingPage({ onEnter }: { onEnter: () => void }) {
  const [visible, setVisible] = useState(false);
  const [exiting, setExiting] = useState(false);

  useEffect(() => { requestAnimationFrame(() => setVisible(true)); }, []);

  const handleEnter = () => {
    setExiting(true);
    setTimeout(onEnter, 500);
  };

  return (
    <div
      role="dialog"
      aria-label="Welcome to ClearDesk"
      className="fixed inset-0 z-[99999] flex flex-col items-center justify-center transition-transform duration-500 ease-in-out"
      style={{
        background: visible ? '#0A0A0F' : '#000000',
        transform: exiting ? 'translateY(-100%)' : 'translateY(0)',
      }}
    >
      {/* Wordmark */}
      <div
        className="absolute top-6 left-8 font-heading text-xl font-bold text-accent transition-all duration-700"
        style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(-10px)' }}
      >
        ClearDesk
      </div>

      {/* Headline */}
      <h1
        className="font-heading text-4xl md:text-5xl font-bold text-center transition-transform duration-700 delay-150 bg-clip-text text-transparent bg-[length:200%_100%] animate-[shimmer_4s_ease-in-out_infinite]"
        style={{
          transform: visible ? 'translateY(0)' : 'translateY(16px)',
          backgroundImage: 'linear-gradient(90deg, var(--color-text-primary) 0%, var(--color-accent) 25%, var(--color-accent-text) 50%, var(--color-accent) 75%, var(--color-text-primary) 100%)',
        }}
      >
        Accounts Receivable Intelligence.
      </h1>

      {/* Subheading — no opacity animation, it's the LCP element */}
      <p
        className="mt-5 text-base text-[#A8A8B8] text-center max-w-[480px] leading-relaxed transition-transform duration-700 delay-300"
        style={{ transform: visible ? 'translateY(0)' : 'translateY(16px)' }}
      >
        Upload any AR document. Claude AI extracts, prioritizes, and flags what your team needs to act on.
      </p>

      {/* Features */}
      <div
        className="mt-12 flex gap-12 transition-all duration-700 delay-[450ms]"
        style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(16px)' }}
      >
        {features.map(({ icon: Icon, label }) => (
          <div key={label} className="flex flex-col items-center gap-2.5">
            <Icon className="w-5 h-5 text-text-secondary" />
            <span className="text-xs text-[#A8A8B8] text-center max-w-[140px]">{label}</span>
          </div>
        ))}
      </div>

      {/* CTA */}
      <button
        onClick={handleEnter}
        className="mt-14 px-6 py-2.5 bg-accent text-bg text-sm font-medium rounded-lg hover:bg-accent/90 transition-all duration-700 delay-600 cursor-pointer"
        style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(16px)' }}
      >
        Open Dashboard →
      </button>
    </div>
  );
}
