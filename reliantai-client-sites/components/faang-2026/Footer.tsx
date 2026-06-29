export default function Footer() {
  return (
    <footer className="px-4 sm:px-6 lg:px-10 py-10 border-t border-[var(--faang-border)]">
      <div className="mx-auto max-w-7xl flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 faang-border flex items-center justify-center">
            <span className="text-[8px] font-bold" style={{ fontFamily: "var(--faang-font-mono)" }}>
              F26
            </span>
          </div>
          <span className="archival-index">
            FAANG 2026 DESIGN SYSTEM — RELIANTAI
          </span>
        </div>
        <p className="archival-index text-center sm:text-right">
          TACTILE BRUTALISM × KINETIC TYPE × GLASS 2.0
        </p>
      </div>
    </footer>
  );
}
