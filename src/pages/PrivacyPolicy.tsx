import { useEffect } from 'react';
import { ArrowLeft } from 'lucide-react';

const PrivacyPolicy = () => {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="min-h-screen bg-white dark:bg-black text-gray-900 dark:text-white">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-white/10">
        <div className="w-full px-6 lg:px-12 py-6">
          <a 
            href="/" 
            className="inline-flex items-center gap-2 text-gray-600 dark:text-white/70 hover:text-orange transition-colors"
          >
            <ArrowLeft size={20} />
            <span className="font-opensans">Back to Home</span>
          </a>
        </div>
      </header>

      {/* Content */}
      <main className="w-full px-6 lg:px-12 py-12 max-w-4xl mx-auto">
        <h1 className="font-teko text-5xl lg:text-6xl font-bold mb-8">Privacy Policy</h1>
        
        <div className="prose dark:prose-invert max-w-none font-opensans text-gray-600 dark:text-white/70">
          <p className="mb-6">Last updated: February 3, 2026</p>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">1. Introduction</h2>
          <p className="mb-4">
            Reliant AI ("we," "our," or "us") respects your privacy and is committed to protecting your personal data. 
            This Privacy Policy explains how we collect, use, and safeguard your information when you visit our website or use our services.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">2. Information We Collect</h2>
          <p className="mb-4">We collect the following types of information:</p>
          <ul className="list-disc pl-6 mb-6 space-y-2">
            <li><strong>Contact Information:</strong> Name, email address, phone number, and company name when you fill out our contact form.</li>
            <li><strong>Usage Data:</strong> Information about how you use our website, including IP address, browser type, and pages visited.</li>
            <li><strong>Project Information:</strong> Details about your business and project requirements when you engage our services.</li>
          </ul>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">3. How We Use Your Information</h2>
          <p className="mb-4">We use your information to:</p>
          <ul className="list-disc pl-6 mb-6 space-y-2">
            <li>Respond to your inquiries and provide requested services</li>
            <li>Communicate about project updates and deliverables</li>
            <li>Improve our website and services</li>
            <li>Send occasional marketing communications (with your consent)</li>
            <li>Comply with legal obligations</li>
          </ul>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">4. Information Sharing</h2>
          <p className="mb-4">
            We do not sell or rent your personal information. We may share your data with:
          </p>
          <ul className="list-disc pl-6 mb-6 space-y-2">
            <li>Service providers who assist in our operations (hosting, analytics, etc.)</li>
            <li>Legal authorities when required by law</li>
          </ul>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">5. Data Security</h2>
          <p className="mb-4">
            We implement appropriate technical and organizational measures to protect your personal data against 
            unauthorized access, alteration, disclosure, or destruction.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">6. Your Rights</h2>
          <p className="mb-4">You have the right to:</p>
          <ul className="list-disc pl-6 mb-6 space-y-2">
            <li>Access your personal data</li>
            <li>Correct inaccurate information</li>
            <li>Request deletion of your data</li>
            <li>Opt-out of marketing communications</li>
          </ul>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">7. Contact Us</h2>
          <p className="mb-4">
            If you have questions about this Privacy Policy, please contact us:
          </p>
          <p className="mb-4">
            <strong>Reliant AI</strong><br />
            Email: DouglasMitchell@ReliantAI.org<br />
            Phone: (832) 947-7028<br />
            Location: Houston, TX
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-white/10 py-8">
        <div className="w-full px-6 lg:px-12 text-center">
          <p className="font-opensans text-sm text-gray-500 dark:text-white/40">
            © 2026 Reliant AI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default PrivacyPolicy;
