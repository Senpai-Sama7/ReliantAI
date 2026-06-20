type BrandLogoProps = {
  size?: "sm" | "md" | "lg";
  showWordmark?: boolean;
};

const SIZES = {
  sm: { ring: "w-10 h-10", leaf: "w-5 h-5", text: "text-sm" },
  md: { ring: "w-16 h-16", leaf: "w-8 h-8", text: "text-lg" },
  lg: { ring: "w-28 h-28 sm:w-32 sm:h-32", leaf: "w-14 h-14 sm:w-16 sm:h-16", text: "text-xl sm:text-2xl" },
};

export default function BrandLogo({ size = "md", showWordmark = true }: BrandLogoProps) {
  const s = SIZES[size];

  return (
    <div className="flex flex-col items-center text-center">
      <div
        className={`${s.ring} rounded-full border-2 border-[var(--dd-green)] flex items-center justify-center bg-black`}
      >
        <svg viewBox="0 0 48 48" className={s.leaf} aria-hidden>
          <path
            fill="none"
            stroke="var(--dd-green)"
            strokeWidth="2"
            d="M24 6c-6 10-12 12-12 20 0 6.6 5.4 12 12 12s12-5.4 12-12c0-8-6-10-12-20z"
          />
        </svg>
      </div>
      {showWordmark && (
        <span className={`dd-brand ${s.text} text-[var(--dd-gold)] mt-2 leading-none`}>
          DOLLAR DANK
        </span>
      )}
    </div>
  );
}
