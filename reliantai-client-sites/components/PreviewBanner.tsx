import Link from "next/link";

interface PreviewBannerProps {
  slug: string;
  lighthouseScore: number;
  city: string;
}

const CHECKOUT_BASE_URL =
  process.env.NEXT_PUBLIC_CHECKOUT_BASE_URL || "https://reliantai.org";

export default function PreviewBanner({
  slug,
  lighthouseScore,
  city,
}: PreviewBannerProps) {
  const starterUrl = `${CHECKOUT_BASE_URL}/checkout?slug=${encodeURIComponent(slug)}&package=starter`;
  const growthUrl = `${CHECKOUT_BASE_URL}/checkout?slug=${encodeURIComponent(slug)}&package=growth`;

  return (
    <div className="fixed bottom-0 inset-x-0 z-50 bg-slate-950 border-t border-slate-700 px-4 sm:px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4">
        <div className="min-w-0">
          <p className="text-white font-semibold text-sm">
            This is your free preview site. It expires in 30 days.
          </p>
          <p className="text-slate-400 text-xs mt-0.5">
            Lighthouse score: {lighthouseScore ?? "--"} &middot; Built for {city}
          </p>
        </div>
        <div className="flex gap-3 flex-shrink-0 w-full sm:w-auto">
          <Link
            href={starterUrl}
            className="flex-1 sm:flex-initial px-4 py-2 bg-blue-700 text-white font-semibold text-sm rounded-md hover:bg-blue-600 transition-colors whitespace-nowrap text-center"
          >
            Get This Site &mdash; $497
          </Link>
          <Link
            href={growthUrl}
            className="flex-1 sm:flex-initial px-4 py-2 border border-blue-500/40 text-blue-300 font-medium text-sm rounded-md hover:border-blue-400 transition-colors whitespace-nowrap text-center"
          >
            Growth &mdash; $297/mo
          </Link>
        </div>
      </div>
    </div>
  );
}
