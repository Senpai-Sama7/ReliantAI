import { useEffect } from 'react';
import { ArrowLeft } from 'lucide-react';

const TermsOfService = () => {
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
        <h1 className="font-teko text-5xl lg:text-6xl font-bold mb-8">Terms of Service</h1>
        
        <div className="prose dark:prose-invert max-w-none font-opensans text-gray-600 dark:text-white/70">
          <p className="mb-6">Last updated: February 3, 2026</p>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">1. Agreement to Terms</h2>
          <p className="mb-4">
            By accessing or using the services of NexGen Web Solutions ("Company," "we," "our," or "us"), 
            you agree to be bound by these Terms of Service. If you do not agree to these terms, 
            please do not use our services.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">2. Services Description</h2>
          <p className="mb-4">
            NexGen Web Solutions provides custom web design and development services, including:
          </p>
          <ul className="list-disc pl-6 mb-6 space-y-2">
            <li>Custom website design and development</li>
            <li>3D interactive elements and animations</li>
            <li>Search engine optimization (SEO)</li>
            <li>Website maintenance and support</li>
            <li>Content management system integration</li>
          </ul>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">3. Project Engagement</h2>
          
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mt-6 mb-3">3.1 Proposal and Agreement</h3>
          <p className="mb-4">
            All projects begin with a written proposal outlining scope, timeline, and fees. 
            Work commences upon signed agreement and initial deposit.
          </p>

          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mt-6 mb-3">3.2 Payment Terms</h3>
          <ul className="list-disc pl-6 mb-6 space-y-2">
            <li><strong>Deposit:</strong> 50% of project fee due before work begins</li>
            <li><strong>Final Payment:</strong> Remaining 50% due upon project completion</li>
            <li><strong>Maintenance Plans:</strong> Billed monthly in advance</li>
            <li><strong>Late Payments:</strong> Subject to 1.5% monthly service charge</li>
          </ul>

          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mt-6 mb-3">3.3 Timeline</h3>
          <p className="mb-4">
            Project timelines are estimates based on the scope defined in the proposal. 
            Delays caused by client (content delays, revision delays, etc.) may extend the timeline.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">4. Client Responsibilities</h2>
          <p className="mb-4">The client agrees to:</p>
          <ul className="list-disc pl-6 mb-6 space-y-2">
            <li>Provide necessary content, images, and materials in a timely manner</li>
            <li>Provide timely feedback on designs and revisions</li>
            <li>Ensure all provided content does not infringe on third-party rights</li>
            <li>Secure necessary domain and hosting accounts (unless included in project)</li>
          </ul>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">5. Intellectual Property</h2>
          
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mt-6 mb-3">5.1 Ownership Transfer</h3>
          <p className="mb-4">
            Upon full payment, the client receives ownership of the final website design and code, 
            excluding third-party libraries, plugins, and proprietary tools owned by NexGen Web Solutions.
          </p>

          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mt-6 mb-3">5.2 Portfolio Rights</h3>
          <p className="mb-4">
            We reserve the right to display completed work in our portfolio and marketing materials 
            unless specifically excluded by written agreement.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">6. Revisions and Changes</h2>
          <ul className="list-disc pl-6 mb-6 space-y-2">
            <li><strong>Included Revisions:</strong> As specified in project proposal (typically 2-4 rounds)</li>
            <li><strong>Additional Revisions:</strong> Billed at hourly rate of $100/hour</li>
            <li><strong>Scope Changes:</strong> Significant changes may require a change order and additional fees</li>
          </ul>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">7. Cancellation Policy</h2>
          <ul className="list-disc pl-6 mb-6 space-y-2">
            <li><strong>Before Work Begins:</strong> Full refund minus $250 administrative fee</li>
            <li><strong>After Work Begins:</strong> Deposit retained; client receives work completed to date</li>
            <li><strong>Maintenance Plans:</strong> Cancel anytime; prorated refund for prepaid unused months</li>
          </ul>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">8. Limitation of Liability</h2>
          <p className="mb-4">
            NexGen Web Solutions' liability is limited to the total amount paid for services. 
            We are not liable for:
          </p>
          <ul className="list-disc pl-6 mb-6 space-y-2">
            <li>Loss of business or revenue</li>
            <li>Data loss (client is responsible for backups)</li>
            <li>Issues arising from third-party services or hosting</li>
            <li>Consequential or indirect damages</li>
          </ul>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">9. Warranty and Support</h2>
          <ul className="list-disc pl-6 mb-6 space-y-2">
            <li><strong>Bug Fixes:</strong> 30-90 day warranty period for bug fixes (varies by package)</li>
            <li><strong>Browser Support:</strong> Latest 2 versions of major browsers</li>
            <li><strong>Maintenance:</strong> Ongoing support available via monthly maintenance plans</li>
          </ul>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">10. Governing Law</h2>
          <p className="mb-4">
            These Terms shall be governed by the laws of the State of Texas. 
            Any disputes shall be resolved in Harris County, Texas.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-8 mb-4">11. Contact Information</h2>
          <p className="mb-4">
            For questions about these Terms of Service:
          </p>
          <p className="mb-4">
            <strong>NexGen Web Solutions</strong><br />
            Email: Douglas-D-Mitchell@outlook.com<br />
            Phone: (832) 947-7028<br />
            Location: Houston, TX
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-white/10 py-8">
        <div className="w-full px-6 lg:px-12 text-center">
          <p className="font-opensans text-sm text-gray-500 dark:text-white/40">
            © 2026 NexGen Web Solutions. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default TermsOfService;
