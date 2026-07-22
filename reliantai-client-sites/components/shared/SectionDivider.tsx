interface SectionDividerProps {
  variant?: "wave" | "angle" | "dots" | "line";
  flip?: boolean;
  light?: boolean;
}

/** Quiet rhythm markers — never decorative noise. */
export default function SectionDivider({
  variant = "dots",
  flip = false,
  light = false,
}: SectionDividerProps) {
  if (variant === "line") {
    return (
      <div className="craft-container" aria-hidden>
        <div className={`border-t ${light ? "border-stone-200" : "border-white/10"}`} />
      </div>
    );
  }

  if (variant === "dots" || variant === "wave" || variant === "angle") {
    // Collapse ornate SVG dividers to a restrained beat — cohesive on mobile.
    return (
      <div
        className={`flex items-center justify-center gap-2.5 py-2 ${flip ? "" : ""}`}
        aria-hidden
      >
        <span
          className={`w-1 h-1 rounded-full ${light ? "bg-stone-300" : "bg-white/20"}`}
        />
        <span
          className={`w-1.5 h-1.5 rounded-full ${light ? "bg-stone-400" : "bg-white/35"}`}
        />
        <span
          className={`w-1 h-1 rounded-full ${light ? "bg-stone-300" : "bg-white/20"}`}
        />
      </div>
    );
  }

  return null;
}
