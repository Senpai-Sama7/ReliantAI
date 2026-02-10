import { useState } from 'react';
import { CheckCircle, AlertCircle, ArrowRight, Loader2, Mail } from 'lucide-react';
import { toast } from 'sonner';

interface AuditQuestion {
  id: number;
  question: string;
  options: { label: string; score: number }[];
}

const auditQuestions: AuditQuestion[] = [
  {
    id: 1,
    question: "Does your website generate leads while you sleep?",
    options: [
      { label: "Yes, consistently every week", score: 25 },
      { label: "Sometimes, but unpredictable", score: 15 },
      { label: "Rarely, maybe one a month", score: 8 },
      { label: "Not at all / I don't know", score: 0 }
    ]
  },
  {
    id: 2,
    question: "How does your site look and work on mobile phones?",
    options: [
      { label: "Perfect - looks like an app", score: 25 },
      { label: "Good - readable and functional", score: 18 },
      { label: "Okay - needs zooming sometimes", score: 10 },
      { label: "Terrible / I haven't checked", score: 0 }
    ]
  },
  {
    id: 3,
    question: "Do you show up on Google when people search for your services?",
    options: [
      { label: "First page, top results", score: 25 },
      { label: "First page, lower down", score: 18 },
      { label: "Second page or beyond", score: 8 },
      { label: "Not sure / I don't appear", score: 0 }
    ]
  },
  {
    id: 4,
    question: "How fast does your website load?",
    options: [
      { label: "Under 2 seconds", score: 25 },
      { label: "2-4 seconds", score: 15 },
      { label: "4-6 seconds", score: 8 },
      { label: "Not sure / Seems slow", score: 0 }
    ]
  }
];

const getScoreAnalysis = (score: number) => {
  if (score >= 80) {
    return {
      title: "Strong Foundation!",
      message: "Your website is performing well, but there's always room for optimization. Get a detailed roadmap to reach the top 1%.",
      color: "green",
      icon: CheckCircle
    };
  }
  if (score >= 50) {
    return {
      title: "You're Missing Opportunities",
      message: "Your site has potential, but you're likely losing leads to competitors every week. Let's fix the gaps.",
      color: "orange",
      icon: AlertCircle
    };
  }
  return {
    title: "Critical Issues Detected",
    message: "Your website is actively costing you customers. Businesses with sites like this typically lose $5K-15K monthly in missed opportunities.",
    color: "red",
    icon: AlertCircle
  };
};

const getRecommendations = (answers: string[]) => {
  const recs: string[] = [];
  
  if (answers[0]?.includes("Not at all") || answers[0]?.includes("Rarely")) {
    recs.push("Add conversion-focused contact forms and clear CTAs on every page");
  }
  if (answers[1]?.includes("Terrible") || answers[1]?.includes("zooming")) {
    recs.push("Implement true mobile-responsive design (not just shrink-to-fit)");
  }
  if (answers[2]?.includes("beyond") || answers[2]?.includes("don't appear")) {
    recs.push("Technical SEO audit and local search optimization");
  }
  if (answers[3]?.includes("slow") || answers[3]?.includes("4-6")) {
    recs.push("Performance optimization - compress images, optimize code delivery");
  }
  
  return recs.length > 0 ? recs : ["Conversion rate optimization", "Content strategy review", "User experience enhancement"];
};

export const WebsiteAuditTool = () => {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<string[]>([]);
  const [scores, setScores] = useState<number[]>([]);
  const [email, setEmail] = useState('');
  const [showResult, setShowResult] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleAnswer = (option: { label: string; score: number }) => {
    const newAnswers = [...answers, option.label];
    const newScores = [...scores, option.score];
    setAnswers(newAnswers);
    setScores(newScores);
    
    if (step < auditQuestions.length - 1) {
      setStep(step + 1);
    } else {
      setShowResult(true);
    }
  };

  const totalScore = scores.reduce((a, b) => a + b, 0);
  const analysis = getScoreAnalysis(totalScore);
  const recommendations = getRecommendations(answers);
  const AnalysisIcon = analysis.icon;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await fetch('https://api.web3forms.com/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_key: '2b257f48-fab5-45e2-abb5-11d6ba950f94',
          subject: 'Website Audit Report Request',
          email,
          audit_score: `${totalScore}/100`,
          audit_result: analysis.title,
          recommendations: recommendations.join('; '),
        }),
      });
      if (!res.ok) throw new Error();
      setSubmitted(true);
    } catch {
      toast.error('Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="p-8 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-500/10 dark:to-green-500/5 rounded-2xl border border-green-200 dark:border-green-500/30 text-center">
        <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle size={32} className="text-white" />
        </div>
        <h3 className="font-teko text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Report Sent!
        </h3>
        <p className="font-opensans text-gray-600 dark:text-white/70">
          Check your inbox in the next 5 minutes for your personalized audit report with actionable fixes.
        </p>
      </div>
    );
  }

  if (showResult) {
    return (
      <div className={`p-6 sm:p-8 bg-gradient-to-br rounded-2xl border ${
        analysis.color === 'green' 
          ? 'from-green-50 to-green-100 dark:from-green-500/10 dark:to-green-500/5 border-green-200 dark:border-green-500/30'
          : analysis.color === 'orange'
          ? 'from-orange/5 to-orange/10 border-orange/30'
          : 'from-red-50 to-red-100 dark:from-red-500/10 dark:to-red-500/5 border-red-200 dark:border-red-500/30'
      }`}>
        <div className="text-center mb-6">
          <div className={`w-20 h-20 mx-auto rounded-full flex items-center justify-center mb-4 ${
            analysis.color === 'green' ? 'bg-green-500' 
            : analysis.color === 'orange' ? 'bg-orange' 
            : 'bg-red-500'
          }`}>
            <AnalysisIcon size={40} className="text-white" />
          </div>
          
          <h3 className="font-teko text-4xl font-bold text-gray-900 dark:text-white mb-2">
            Score: {totalScore}/100
          </h3>
          <p className={`font-teko text-xl font-medium mb-3 ${
            analysis.color === 'green' ? 'text-green-600 dark:text-green-400'
            : analysis.color === 'orange' ? 'text-orange'
            : 'text-red-600 dark:text-red-400'
          }`}>
            {analysis.title}
          </p>
          <p className="font-opensans text-gray-600 dark:text-white/70 text-sm">
            {analysis.message}
          </p>
        </div>

        {/* Score Bar */}
        <div className="w-full bg-gray-200 dark:bg-white/10 rounded-full h-3 mb-6">
          <div 
            className={`h-3 rounded-full transition-all duration-1000 ${
              analysis.color === 'green' ? 'bg-green-500'
              : analysis.color === 'orange' ? 'bg-orange'
              : 'bg-red-500'
            }`}
            style={{ width: `${totalScore}%` }}
          />
        </div>

        {/* Recommendations */}
        <div className="mb-6">
          <h4 className="font-teko text-xl font-bold text-gray-900 dark:text-white mb-3">
            Top Priorities for Your Site:
          </h4>
          <ul className="space-y-2">
            {recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-white/70">
                <span className="text-orange mt-0.5">▸</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>

        {/* Email Capture */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <p className="font-opensans text-sm text-gray-600 dark:text-white/70 mb-3">
            Get your full detailed report with step-by-step fixes:
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-200 dark:border-white/10 bg-white dark:bg-black/50 text-gray-900 dark:text-white focus:border-orange focus:outline-none transition-colors"
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-3 bg-orange text-white font-semibold rounded-lg hover:bg-orange-600 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isSubmitting ? (
                <><Loader2 size={18} className="animate-spin" /> Sending...</>
              ) : (
                <>Get Full Report <ArrowRight size={18} /></>
              )}
            </button>
          </div>
          <p className="text-xs text-gray-500 dark:text-white/40">
            ✅ Free. No spam. Unsubscribe anytime.
          </p>
        </form>
      </div>
    );
  }

  const currentQuestion = auditQuestions[step];

  return (
    <div className="p-6 sm:p-8 bg-white dark:bg-dark-100/50 rounded-2xl border border-gray-200 dark:border-white/10 shadow-lg">
      {/* Progress */}
      <div className="flex justify-between mb-6">
        {auditQuestions.map((_, i) => (
          <div 
            key={i}
            className={`h-2 flex-1 mx-1 rounded-full transition-colors duration-300 ${
              i < step ? 'bg-orange' 
              : i === step ? 'bg-orange/50' 
              : 'bg-gray-200 dark:bg-white/10'
            }`}
          />
        ))}
      </div>
      
      <div className="mb-2 text-sm text-gray-500 dark:text-white/50 font-opensans">
        Question {step + 1} of {auditQuestions.length}
      </div>
      
      <h3 className="font-teko text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-6">
        {currentQuestion.question}
      </h3>
      
      <div className="space-y-3">
        {currentQuestion.options.map((option) => (
          <button
            key={option.label}
            onClick={() => handleAnswer(option)}
            className="w-full p-4 text-left border border-gray-200 dark:border-white/10 rounded-xl hover:border-orange hover:bg-orange/5 dark:hover:bg-orange/10 transition-all group"
          >
            <span className="font-opensans text-gray-700 dark:text-white/80 group-hover:text-orange transition-colors">
              {option.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default WebsiteAuditTool;
