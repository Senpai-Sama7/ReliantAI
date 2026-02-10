import { useState, useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Calculator, TrendingDown, DollarSign, Users, ArrowRight } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

interface CalculationResult {
  monthlyLostLeads: number;
  monthlyRevenueLoss: number;
  yearlyRevenueLoss: number;
}

const LossCalculator = () => {
  const sectionRef = useRef<HTMLElement>(null);
  const [monthlyVisitors, setMonthlyVisitors] = useState(500);
  const [conversionRate, setConversionRate] = useState(1);
  const [avgDealValue, setAvgDealValue] = useState(5000);
  const [showResults, setShowResults] = useState(false);

  const calculateLoss = (): CalculationResult => {
    // Industry average conversion for optimized B2B site: 3-5%
    // Current conversion rate (input)
    const potentialConversionRate = 4; // 4% is achievable with optimization
    
    const currentLeads = Math.round(monthlyVisitors * (conversionRate / 100));
    const potentialLeads = Math.round(monthlyVisitors * (potentialConversionRate / 100));
    const monthlyLostLeads = potentialLeads - currentLeads;
    const monthlyRevenueLoss = monthlyLostLeads * avgDealValue;
    const yearlyRevenueLoss = monthlyRevenueLoss * 12;

    return {
      monthlyLostLeads,
      monthlyRevenueLoss,
      yearlyRevenueLoss
    };
  };

  const results = calculateLoss();

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        '.calculator-fade',
        { y: 60, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          stagger: 0.1,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top 80%',
          },
        }
      );
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(amount);
  };

  return (
    <section
      id="calculator"
      ref={sectionRef}
      className="relative min-h-screen w-full py-24 lg:py-32 bg-gradient-to-b from-gray-50 to-white dark:from-black dark:to-dark-100 transition-colors duration-500"
    >
      <div className="relative z-10 w-full px-6 lg:px-12 xl:px-24">
        {/* Header */}
        <div className="text-center mb-16 calculator-fade">
          <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-red-100 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 rounded-full text-red-600 dark:text-red-400 font-opensans text-sm mb-6">
            <TrendingDown size={16} />
            The Cost of Inaction
          </span>
          <h2 className="font-teko text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 dark:text-white mb-6">
            HOW MUCH IS YOUR
            <span className="text-red-600 dark:text-red-500"> WEBSITE </span>
            COSTING YOU?
          </h2>
          <p className="font-opensans text-lg text-gray-600 dark:text-white/60 max-w-2xl mx-auto">
            Most businesses don't realize how much revenue they're losing to a poorly optimized website. 
            Calculate your hidden losses below.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 max-w-6xl mx-auto">
          {/* Calculator Inputs */}
          <div className="calculator-fade p-8 bg-white dark:bg-dark-100/50 border border-gray-200 dark:border-white/10 rounded-2xl shadow-lg">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-12 h-12 bg-orange/10 rounded-xl flex items-center justify-center">
                <Calculator size={24} className="text-orange" />
              </div>
              <h3 className="font-teko text-2xl font-bold text-gray-900 dark:text-white">
                Revenue Loss Calculator
              </h3>
            </div>

            <div className="space-y-8">
              {/* Monthly Visitors */}
              <div>
                <label className="flex items-center justify-between mb-3">
                  <span className="font-opensans text-sm text-gray-600 dark:text-white/70">
                    Monthly Website Visitors
                  </span>
                  <span className="font-teko text-xl font-bold text-orange">
                    {monthlyVisitors.toLocaleString()}
                  </span>
                </label>
                <input
                  type="range"
                  min="100"
                  max="10000"
                  step="100"
                  value={monthlyVisitors}
                  onChange={(e) => setMonthlyVisitors(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 dark:bg-white/10 rounded-lg appearance-none cursor-pointer accent-orange"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>100</span>
                  <span>10,000+</span>
                </div>
              </div>

              {/* Current Conversion Rate */}
              <div>
                <label className="flex items-center justify-between mb-3">
                  <span className="font-opensans text-sm text-gray-600 dark:text-white/70">
                    Current Conversion Rate (%)
                  </span>
                  <span className="font-teko text-xl font-bold text-orange">
                    {conversionRate}%
                  </span>
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="5"
                  step="0.1"
                  value={conversionRate}
                  onChange={(e) => setConversionRate(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 dark:bg-white/10 rounded-lg appearance-none cursor-pointer accent-orange"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>0.1%</span>
                  <span>5%</span>
                </div>
                <p className="text-xs text-gray-500 dark:text-white/40 mt-2">
                  Industry average is 2-3%. Optimized sites achieve 4-6%.
                </p>
              </div>

              {/* Average Deal Value */}
              <div>
                <label className="flex items-center justify-between mb-3">
                  <span className="font-opensans text-sm text-gray-600 dark:text-white/70">
                    Average Customer Value
                  </span>
                  <span className="font-teko text-xl font-bold text-orange">
                    {formatCurrency(avgDealValue)}
                  </span>
                </label>
                <input
                  type="range"
                  min="500"
                  max="50000"
                  step="500"
                  value={avgDealValue}
                  onChange={(e) => setAvgDealValue(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 dark:bg-white/10 rounded-lg appearance-none cursor-pointer accent-orange"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>$500</span>
                  <span>$50K+</span>
                </div>
              </div>

              <button
                onClick={() => setShowResults(true)}
                className="w-full py-4 bg-orange text-white font-opensans font-semibold rounded-lg hover:bg-orange-600 transition-colors flex items-center justify-center gap-2"
              >
                Calculate My Losses
                <ArrowRight size={18} />
              </button>
            </div>
          </div>

          {/* Results Panel */}
          <div className="calculator-fade">
            {showResults ? (
              <div className="p-8 bg-gradient-to-br from-red-50 to-red-100 dark:from-red-500/10 dark:to-red-500/5 border border-red-200 dark:border-red-500/30 rounded-2xl">
                <h3 className="font-teko text-3xl font-bold text-gray-900 dark:text-white mb-6">
                  Your Estimated Losses
                </h3>

                <div className="space-y-6">
                  {/* Monthly Lost Leads */}
                  <div className="flex items-center gap-4 p-4 bg-white dark:bg-black/30 rounded-xl">
                    <div className="w-12 h-12 bg-red-100 dark:bg-red-500/20 rounded-full flex items-center justify-center">
                      <Users size={24} className="text-red-600 dark:text-red-400" />
                    </div>
                    <div>
                      <p className="font-opensans text-sm text-gray-500 dark:text-white/50">
                        Leads Lost Each Month
                      </p>
                      <p className="font-teko text-3xl font-bold text-red-600 dark:text-red-400">
                        {results.monthlyLostLeads}
                      </p>
                    </div>
                  </div>

                  {/* Monthly Revenue Loss */}
                  <div className="flex items-center gap-4 p-4 bg-white dark:bg-black/30 rounded-xl">
                    <div className="w-12 h-12 bg-red-100 dark:bg-red-500/20 rounded-full flex items-center justify-center">
                      <DollarSign size={24} className="text-red-600 dark:text-red-400" />
                    </div>
                    <div>
                      <p className="font-opensans text-sm text-gray-500 dark:text-white/50">
                        Monthly Revenue Loss
                      </p>
                      <p className="font-teko text-3xl font-bold text-red-600 dark:text-red-400">
                        {formatCurrency(results.monthlyRevenueLoss)}
                      </p>
                    </div>
                  </div>

                  {/* Yearly Revenue Loss - EMPHASIZED */}
                  <div className="p-6 bg-red-600 rounded-2xl text-white text-center">
                    <p className="font-opensans text-sm text-red-100 mb-2">
                      Annual Revenue Loss
                    </p>
                    <p className="font-teko text-5xl font-bold mb-2">
                      {formatCurrency(results.yearlyRevenueLoss)}
                    </p>
                    <p className="text-sm text-red-100">
                      That's how much your website is costing you every year.
                    </p>
                  </div>
                </div>

                <div className="mt-6 text-center">
                  <p className="font-opensans text-sm text-gray-600 dark:text-white/70 mb-4">
                    The fix? A conversion-optimized website typically pays for itself in 30-60 days.
                  </p>
                  <a
                    href="#contact"
                    onClick={(e) => {
                      e.preventDefault();
                      const section = document.getElementById('contact');
                      if (section) {
                        section.scrollIntoView({ behavior: 'smooth' });
                      }
                    }}
                    className="inline-flex items-center gap-2 px-6 py-3 bg-orange text-white font-semibold rounded-lg hover:bg-orange-600 transition-colors"
                  >
                    Stop the Bleeding - Get a Quote
                    <ArrowRight size={18} />
                  </a>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center p-8 bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-white/10 border-dashed rounded-2xl">
                <div className="text-center">
                  <Calculator size={48} className="text-gray-300 dark:text-white/20 mx-auto mb-4" />
                  <p className="font-opensans text-gray-400 dark:text-white/40">
                    Adjust the sliders and click "Calculate" to see your losses
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Trust Indicators */}
        <div className="mt-16 flex flex-wrap justify-center gap-6 calculator-fade">
          {[
            { label: "Based on 150+ client analyses" },
            { label: "Industry-standard conversion benchmarks" },
            { label: "Conservative estimates only" }
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-gray-500 dark:text-white/40">
              <span className="w-2 h-2 bg-green-500 rounded-full" />
              {item.label}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default LossCalculator;
