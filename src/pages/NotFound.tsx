import { ArrowLeft, Home } from 'lucide-react';

const NotFound = () => (
  <div className="min-h-screen bg-[#f7f7f7] dark:bg-[#0a0a0a] flex items-center justify-center px-6">
    <div className="text-center max-w-lg">
      <div className="font-teko text-[12rem] leading-none font-bold text-orange/20 select-none">
        404
      </div>
      <h1 className="font-teko text-4xl sm:text-5xl font-bold text-gray-900 dark:text-white -mt-8 mb-4">
        PAGE NOT <span className="text-orange">FOUND</span>
      </h1>
      <p className="font-opensans text-gray-600 dark:text-white/60 mb-8">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <a
          href="/"
          className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-orange text-white font-opensans font-semibold rounded-lg hover:bg-orange-600 transition-colors"
        >
          <Home size={18} />
          Back to Home
        </a>
        <button
          onClick={() => window.history.back()}
          className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-gray-200 dark:border-white/20 text-gray-900 dark:text-white font-opensans font-semibold rounded-lg hover:border-orange/30 transition-colors"
        >
          <ArrowLeft size={18} />
          Go Back
        </button>
      </div>
    </div>
  </div>
);

export default NotFound;
