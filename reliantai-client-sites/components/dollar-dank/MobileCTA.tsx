const MAPS = "https://maps.google.com/?q=6590+SW+Freeway+Houston+TX";

export default function MobileCTA() {
  return (
    <div className="fixed bottom-0 inset-x-0 z-50 md:hidden border-t border-[var(--dd-line)] bg-[var(--dd-bg)]/95 backdrop-blur-sm px-4 py-3">
      <a href={MAPS} target="_blank" rel="noopener noreferrer" className="dd-btn-primary w-full">
        Get directions
      </a>
    </div>
  );
}
