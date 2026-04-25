interface SectionDividerProps {
  variant?: "wave" | "angle" | "dots" | "line";
  flip?: boolean;
  light?: boolean;
}

export default function SectionDivider({ variant = "wave", flip = false, light = false }: SectionDividerProps) {
  if (variant === "line") {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className={`border-t ${light ? "border-stone-200" : "border-slate-800/30"}`} />
      </div>
    );
  }

  if (variant === "dots") {
    return (
      <div className="flex items-center justify-center gap-3 py-3">
        <span className={`w-1.5 h-1.5 rounded-full ${light ? "bg-stone-300" : "bg-slate-700/40"}`} />
        <span className={`w-1.5 h-1.5 rounded-full ${light ? "bg-stone-400" : "bg-slate-600/60"}`} />
        <span className={`w-1.5 h-1.5 rounded-full ${light ? "bg-stone-300" : "bg-slate-700/40"}`} />
      </div>
    );
  }

  if (variant === "angle") {
    return (
      <div className={`h-16 overflow-hidden ${flip ? "rotate-180" : ""}`}>
        <svg viewBox="0 0 1200 120" preserveAspectRatio="none" className="w-full h-full">
          <path
            d="M0,80 L1200,0 L1200,120 L0,120 Z"
            className={light ? "fill-stone-100" : "fill-slate-900"}
            fillOpacity="0.5"
          />
        </svg>
      </div>
    );
  }

  return (
    <div className={`h-16 overflow-hidden ${flip ? "rotate-180" : ""}`}>
      <svg viewBox="0 0 1200 120" preserveAspectRatio="none" className="w-full h-full">
        <path
          d="M0,60 C200,120 400,0 600,60 C800,120 1000,0 1200,60 L1200,120 L0,120 Z"
          className={light ? "fill-stone-200" : "fill-slate-900"}
          fillOpacity="0.4"
        />
      </svg>
    </div>
  );
}