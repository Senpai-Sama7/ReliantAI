const MAPS = "https://maps.google.com/?q=6590+SW+Freeway+Houston+TX";

export default function StoreStory() {
  return (
    <section className="dd-section px-4 sm:px-6 py-16 sm:py-20">
      <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-12 md:gap-16">
        <div>
          <p className="dd-label">The shop</p>
          <h2 className="mt-3 text-2xl sm:text-3xl font-semibold tracking-tight leading-snug">
            SW Freeway. Open till 2AM.
          </h2>
          <div className="mt-6 space-y-4 text-[var(--dd-muted)] leading-relaxed">
            <p>
              Dollar Dank is the spot people film at — timer challenge attempts, fit checks,
              regulars pulling up after hours. The energy in the store is the brand. That&apos;s
              why the feed looks the way it does.
            </p>
            <p>
              In-store merch like the &ldquo;Cash to Burn&rdquo; tee moves quick. Deals stay
              sharp. Staff knows the regulars. If you&apos;re in Houston and you haven&apos;t
              pulled up yet, this is the address.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="border border-[var(--dd-line)] rounded-[var(--dd-radius)] p-5 bg-[var(--dd-surface)]">
            <p className="dd-label">Address</p>
            <p className="mt-2 font-medium">6590 SW Freeway</p>
            <p className="text-[var(--dd-muted)]">Houston, TX</p>
            <a
              href={MAPS}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-4 text-sm text-[var(--dd-green)] hover:underline"
            >
              Open in Maps →
            </a>
          </div>

          <div className="border border-[var(--dd-line)] rounded-[var(--dd-radius)] p-5 bg-[var(--dd-surface)]">
            <p className="dd-label">Hours</p>
            <ul className="mt-3 space-y-2 text-sm">
              <li className="flex justify-between gap-4">
                <span className="text-[var(--dd-muted)]">Every day</span>
                <span className="font-medium tabular-nums">8:00 AM – 2:00 AM</span>
              </li>
            </ul>
            <p className="mt-4 text-xs text-[var(--dd-muted)]">
              Closed 2AM–8AM. Houston (Central) time.
            </p>
          </div>

          <div className="border border-[var(--dd-line)] rounded-[var(--dd-radius)] p-5 bg-[var(--dd-surface)]">
            <p className="dd-label">21+ only</p>
            <p className="mt-2 text-sm text-[var(--dd-muted)] leading-relaxed">
              Valid government-issued ID required. Please consume responsibly and in
              accordance with Texas law.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
