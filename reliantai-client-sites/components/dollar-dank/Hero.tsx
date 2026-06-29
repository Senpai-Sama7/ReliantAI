import BrandLogo from "./BrandLogo";
import StoreStatus from "./StoreStatus";

const MAPS = "https://maps.google.com/?q=6590+SW+Freeway+Houston+TX";
const IG = "https://instagram.com/dollardankdispensary";

export default function Hero() {
  return (
    <section className="px-4 sm:px-6 pt-12 pb-16 sm:pt-16 sm:pb-20">
      <div className="max-w-5xl mx-auto">
        <div className="max-w-2xl">
          <BrandLogo size="lg" />

          <h1 className="mt-10 text-[clamp(2rem,5vw,3.25rem)] font-semibold leading-[1.1] tracking-tight">
            Can you hit{" "}
            <span className="text-[var(--dd-green)] tabular-nums">10.00</span>?
          </h1>

          <p className="mt-5 text-lg text-[var(--dd-muted)] leading-relaxed max-w-lg">
            Dollar Dank is on SW Freeway — open late, priced right, and running the timer
            challenge that keeps showing up on your feed. Pull up, try it in-store, tag us if
            you nail it.
          </p>

          <p className="mt-4 text-sm text-[var(--dd-muted)]">
            6590 SW Freeway, Houston, TX · Open daily 8AM–2AM
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <a href={MAPS} target="_blank" rel="noopener noreferrer" className="dd-btn-primary">
              Get directions
            </a>
            <a href={IG} target="_blank" rel="noopener noreferrer" className="dd-btn-secondary">
              @dollardankdispensary
            </a>
          </div>

          <dl className="mt-10 flex gap-8 text-sm">
            <div>
              <dt className="text-[var(--dd-muted)]">Followers</dt>
              <dd className="mt-1 font-semibold tabular-nums">1,187</dd>
            </div>
            <div>
              <dt className="text-[var(--dd-muted)]">Posts</dt>
              <dd className="mt-1 font-semibold tabular-nums">42</dd>
            </div>
            <div>
              <dt className="text-[var(--dd-muted)]">Hours</dt>
              <dd className="mt-1 font-semibold">8AM – 2AM</dd>
            </div>
          </dl>
        </div>

        <div className="mt-10 max-w-md md:hidden">
          <StoreStatus />
        </div>
      </div>
    </section>
  );
}
