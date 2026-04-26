"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import MOCK_DATA from "@/lib/mock-data";

const TEMPLATE_IDS = [
  "hvac-reliable-blue",
  "plumbing-trustworthy-navy",
  "electrical-sharp-gold",
  "roofing-bold-copper",
  "painting-clean-minimal",
  "landscaping-earthy-green",
] as const;

type TemplateId = (typeof TEMPLATE_IDS)[number];

const TEMPLATE_META: Record<string, { label: string; accent: string; accentBg: string }> = {
  "hvac-reliable-blue": { label: "HVAC — Reliable Blue", accent: "blue-400", accentBg: "bg-blue-500" },
  "plumbing-trustworthy-navy": { label: "Plumbing — Trustworthy Navy", accent: "blue-400", accentBg: "bg-blue-700" },
  "electrical-sharp-gold": { label: "Electrical — Sharp Gold", accent: "amber-400", accentBg: "bg-amber-500" },
  "roofing-bold-copper": { label: "Roofing — Bold Copper", accent: "orange-400", accentBg: "bg-orange-500" },
  "painting-clean-minimal": { label: "Painting — Clean Minimal", accent: "violet-400", accentBg: "bg-violet-500" },
  "landscaping-earthy-green": { label: "Landscaping — Earthy Green", accent: "emerald-400", accentBg: "bg-emerald-500" },
};

const templateLoader: Record<string, () => Promise<{ default: React.ComponentType<{ content: import("@/types/SiteContent").SiteContent }> }>> = {
  "hvac-reliable-blue": () => import("@/templates/hvac-reliable-blue"),
  "plumbing-trustworthy-navy": () => import("@/templates/plumbing-trustworthy-navy"),
  "electrical-sharp-gold": () => import("@/templates/electrical-sharp-gold"),
  "roofing-bold-copper": () => import("@/templates/roofing-bold-copper"),
  "painting-clean-minimal": () => import("@/templates/painting-clean-minimal"),
  "landscaping-earthy-green": () => import("@/templates/landscaping-earthy-green"),
};

const DynamicTemplates: Record<string, React.ComponentType<{ content: import("@/types/SiteContent").SiteContent }>> = {};
for (const id of TEMPLATE_IDS) {
  DynamicTemplates[id] = dynamic(templateLoader[id], {
    loading: () => (
      <div className="flex items-center justify-center min-h-[60vh] text-zinc-500">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-zinc-700 border-t-zinc-400 rounded-full animate-spin mx-auto mb-3" />
          Loading {TEMPLATE_META[id].label}...
        </div>
      </div>
    ),
  });
}

export default function PreviewPage() {
  const [active, setActive] = useState<TemplateId>("hvac-reliable-blue");
  const [showJson, setShowJson] = useState(false);
  const [layout, setLayout] = useState<"full" | "grid">("full");
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  const content = MOCK_DATA[active];

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <nav className="sticky top-0 z-50 border-b border-zinc-800 bg-zinc-950/95 backdrop-blur-md">
        <div className="mx-auto max-w-screen-2xl px-4 py-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <h1 className="text-sm font-semibold tracking-wide uppercase text-zinc-300">
              Template Preview
            </h1>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-500 font-mono">6 templates</span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center bg-zinc-900 rounded-lg p-0.5 border border-zinc-800">
              <button
                onClick={() => setLayout("full")}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  layout === "full" ? "bg-zinc-700 text-white" : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                Full Page
              </button>
              <button
                onClick={() => setLayout("grid")}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  layout === "grid" ? "bg-zinc-700 text-white" : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                Grid
              </button>
            </div>
            <button
              onClick={() => setShowJson(!showJson)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-colors ${
                showJson
                  ? "bg-violet-600 border-violet-500 text-white"
                  : "border-zinc-700 text-zinc-500 hover:text-zinc-300 hover:border-zinc-600"
              }`}
            >
              {showJson ? "Hide JSON" : "View JSON"}
            </button>
          </div>
        </div>

        <div className="mx-auto max-w-screen-2xl px-4 pb-3 flex flex-wrap gap-1.5">
          {TEMPLATE_IDS.map((id) => {
            const meta = TEMPLATE_META[id];
            return (
              <button
                key={id}
                onClick={() => setActive(id)}
                className={`inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  active === id
                    ? "bg-zinc-100 text-zinc-950"
                    : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800"
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${meta.accentBg}`} />
                {meta.label}
              </button>
            );
          })}
        </div>
      </nav>

      {showJson && (
        <div className="mx-auto max-w-5xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-zinc-300">
              Mock Data — <span className="text-zinc-500">{active}</span>
            </h2>
            <button
              onClick={() => navigator.clipboard.writeText(JSON.stringify(content, null, 2))}
              className="px-3 py-1.5 text-xs font-medium rounded-md bg-zinc-800 text-zinc-300 hover:bg-zinc-700 border border-zinc-700"
            >
              Copy JSON
            </button>
          </div>
          <pre className="overflow-auto rounded-lg bg-zinc-900 border border-zinc-800 p-4 text-[11px] text-zinc-400 leading-relaxed max-h-[70vh]">
            {JSON.stringify(content, null, 2)}
          </pre>
        </div>
      )}

      {!showJson && layout === "full" && (
        <div className="relative bg-zinc-950">
          {(() => {
            const Template = DynamicTemplates[active];
            return Template ? <Template content={content} /> : null;
          })()}
          <div className="absolute top-4 right-4 z-40">
            <span className="px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider rounded-md bg-black/70 text-white backdrop-blur-sm border border-white/10 shadow-lg">
              {TEMPLATE_META[active].label}
            </span>
          </div>
        </div>
      )}

      {!showJson && layout === "grid" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-1 p-1">
          {TEMPLATE_IDS.map((id) => {
            const Template = DynamicTemplates[id];
            const meta = TEMPLATE_META[id];
            return (
              <div key={id} className="relative group">
                <div className="absolute top-2 left-2 z-10">
                  <span className={`px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-black/70 text-white backdrop-blur-sm border border-white/10`}>
                    {meta.label}
                  </span>
                </div>
                <div className="h-[80vh] overflow-y-auto rounded-sm bg-white scrollbar-thin">
                  {Template ? <Template content={MOCK_DATA[id]} /> : null}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}