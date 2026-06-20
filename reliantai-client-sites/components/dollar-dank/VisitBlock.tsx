const MAPS = "https://maps.google.com/?q=6590+SW+Freeway+Houston+TX";
const IG = "https://instagram.com/dollardankdispensary";

export default function VisitBlock() {
  return (
    <section id="visit" className="dd-section px-4 sm:px-6 py-16 sm:py-20">
      <div className="max-w-5xl mx-auto border border-[var(--dd-line)] rounded-[var(--dd-radius)] bg-[var(--dd-surface)] p-8 sm:p-12">
        <p className="dd-label">Visit</p>
        <h2 className="mt-3 text-2xl sm:text-3xl font-semibold tracking-tight">
          Pull up to SW Freeway.
        </h2>
        <p className="mt-4 text-[var(--dd-muted)] max-w-lg leading-relaxed">
          Run the timer in-store. Grab what you need. If you hit 10.00 on camera, tag us —
          that&apos;s the whole bit.
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <a href={MAPS} target="_blank" rel="noopener noreferrer" className="dd-btn-primary">
            Get directions
          </a>
          <a href={IG} target="_blank" rel="noopener noreferrer" className="dd-btn-secondary">
            Follow on Instagram
          </a>
        </div>

        <address className="mt-10 not-italic text-sm text-[var(--dd-muted)] leading-relaxed">
          <span className="block font-medium text-[var(--dd-text)]">Dollar Dank Dispensary</span>
          6590 SW Freeway, Houston, TX
          <br />
          Open daily 8AM – 2AM
        </address>
      </div>
    </section>
  );
}
