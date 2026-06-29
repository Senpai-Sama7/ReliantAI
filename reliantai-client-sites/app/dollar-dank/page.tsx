import Nav from "@/components/dollar-dank/Nav";
import Hero from "@/components/dollar-dank/Hero";
import TimerChallenge from "@/components/dollar-dank/TimerChallenge";
import StoreStory from "@/components/dollar-dank/StoreStory";
import ReelsGallery from "@/components/dollar-dank/ReelsGallery";
import VisitBlock from "@/components/dollar-dank/VisitBlock";
import MobileCTA from "@/components/dollar-dank/MobileCTA";

export default function DollarDankPage() {
  return (
    <>
      <Nav />
      <main className="pb-20 md:pb-0">
        <Hero />

        <section id="challenge" className="dd-section px-4 sm:px-6 py-16 sm:py-20">
          <div className="max-w-5xl mx-auto">
            <div className="mb-8 max-w-xl">
              <p className="dd-label">Timer challenge</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                Warm up before you walk in.
              </h2>
              <p className="mt-3 text-[var(--dd-muted)] leading-relaxed">
                Same game from the Reels — stop the clock at 10.00. Then do it on camera at
                the shop.
              </p>
            </div>
            <TimerChallenge />
          </div>
        </section>

        <StoreStory />
        <ReelsGallery />
        <VisitBlock />
      </main>

      <footer className="dd-section px-4 sm:px-6 py-10">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 text-sm text-[var(--dd-muted)]">
          <p>© {new Date().getFullYear()} Dollar Dank Dispensary</p>
          <a
            href="https://instagram.com/dollardankdispensary"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[var(--dd-text)] hover:text-[var(--dd-green)] transition-colors"
          >
            @dollardankdispensary
          </a>
        </div>
      </footer>

      <MobileCTA />
    </>
  );
}
