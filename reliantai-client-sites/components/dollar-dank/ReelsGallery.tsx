const IG = "https://instagram.com/dollardankdispensary";

const CLIPS = [
  { id: 1, note: "Timer run — in store" },
  { id: 2, note: "Wednesday · 7:41 PM", script: true },
  { id: 3, note: "Cash to Burn tee" },
  { id: 4, note: "Weekend pull-up" },
  { id: 5, note: "Behind the counter" },
  { id: 6, note: "Customer reaction" },
] as const;

export default function ReelsGallery() {
  return (
    <section id="feed" className="dd-section py-16 sm:py-20">
      <div className="max-w-5xl mx-auto px-4 sm:px-6">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-8">
          <div>
            <p className="dd-label">Instagram</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight">
              What people are filming
            </h2>
          </div>
          <a
            href={IG}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-[var(--dd-green)] hover:underline shrink-0"
          >
            @dollardankdispensary →
          </a>
        </div>

        <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0 snap-x snap-mandatory scrollbar-hide">
          {CLIPS.map((clip) => (
            <a
              key={clip.id}
              href={IG}
              target="_blank"
              rel="noopener noreferrer"
              className="snap-start shrink-0 w-[140px] sm:w-[160px] group"
              aria-label={clip.note}
            >
              <div className="aspect-[9/16] bg-[#141414] border border-[var(--dd-line)] rounded-[var(--dd-radius)] overflow-hidden relative">
                <div className="absolute inset-0 bg-gradient-to-b from-[#1a241a] to-[#0f0f0f]" />
                {"script" in clip && clip.script && (
                  <div className="absolute top-3 left-3 right-3 z-10">
                    <p
                      className="text-white text-sm italic leading-tight"
                      style={{ fontFamily: "Georgia, serif" }}
                    >
                      Wednesday
                    </p>
                    <p className="text-white/60 text-[10px] tabular-nums mt-0.5">19:41</p>
                  </div>
                )}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="w-9 h-9 rounded-full bg-black/70 flex items-center justify-center">
                    <svg className="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  </span>
                </div>
              </div>
              <p className="mt-2 text-xs text-[var(--dd-muted)] line-clamp-2">{clip.note}</p>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
