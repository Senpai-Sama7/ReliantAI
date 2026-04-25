import Link from "next/link";

interface PreviewBannerProps {
  slug: string;
  lighthouseScore: number;
  city: string;
}

export default function PreviewBanner({
  slug,
  lighthouseScore,
  city,
}: PreviewBannerProps) {
  return (
    <div className="fixed bottom-0 inset-x-0 z-50 bg-slate-900/95 backdrop-blur border-t border-slate-700 px-4 sm:px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4">
        <div className="min-w-0">
          <p className="text-white font-semibold text-sm">
            This is your free preview site. It expires in 30 days.
          </p>
          <p className="text-slate-400 text-xs mt-0.5">
            Lighthouse score: {lighthouseScore ?? "--"} &middot; Built for{" "}
            {city}
          </p>
        </div>
        <div className="flex gap-3 flex-shrink-0 w-full sm:w-auto">
          <Link
            href={`/checkout?slug=${slug}&package=starter`}
            className="flex-1 sm:flex-initial px-4 py-2 bg-blue-500 text-white font-semibold text-sm rounded-lg hover:bg-blue-400 transition-colors whitespace-nowrap text-center"
          >
            Get This Site &mdash; $497
          </Link>
          <Link
            href={`/checkout?slug=${slug}&package=growth`}
            className="flex-1 sm:flex-initial px-4 py-2 border border-blue-400 text-blue-300 font-medium text-sm rounded-lg hover:border-blue-300 transition-colors whitespace-nowrap text-center"
          >
            Growth &mdash; $297/mo
          </Link>
        </div>
      </div>
    </div>
  );
}
