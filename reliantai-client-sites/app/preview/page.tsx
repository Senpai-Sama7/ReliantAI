"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import MOCK_DATA from "@/lib/mock-data";
import { TEMPLATE_IDS, templateImports, type TemplateId } from "@/lib/templates";

const TEMPLATE_META: Record<string, { label: string; short: string }> = {
  "hvac-reliable-blue": { label: "HVAC — Steel Ink", short: "HVAC" },
  "plumbing-trustworthy-navy": { label: "Plumbing — Ink + Copper", short: "Plumbing" },
  "electrical-sharp-gold": { label: "Electrical — Charcoal Gold", short: "Electrical" },
  "roofing-bold-copper": { label: "Roofing — Umber Copper", short: "Roofing" },
  "painting-clean-minimal": { label: "Painting — Gallery Ochre", short: "Painting" },
  "landscaping-earthy-green": { label: "Landscaping — Moss + Clay", short: "Landscaping" },
};

const DynamicTemplates: Record<
  string,
  React.ComponentType<{ content: import("@/types/SiteContent").SiteContent }>
> = {};
for (const id of TEMPLATE_IDS) {
  DynamicTemplates[id] = dynamic(templateImports[id], {
    loading: () => (
      <div className="flex items-center justify-center min-h-[50svh] text-zinc-500 text-sm">
        Loading {TEMPLATE_META[id].short}…
      </div>
    ),
  });
}

export default function PreviewPage() {
  const [active, setActive] = useState<TemplateId>("hvac-reliable-blue");
  const [showJson, setShowJson] = useState(false);
  const [layout, setLayout] = useState<"full" | "grid">("full");
  const [chromeOpen, setChromeOpen] = useState(false);

  const content = MOCK_DATA[active];
  const Template = DynamicTemplates[active];

  return (
    <div className="min-h-svh bg-zinc-950 text-white">
      {/* Compact studio chrome — one row on phones, expands on demand */}
      <nav className="sticky top-0 z-50 border-b border-zinc-800 bg-zinc-950">
        <div className="px-3 sm:px-4 h-12 flex items-center gap-2 sm:gap-3">
          <p className="text-[10px] font-semibold tracking-[0.16em] uppercase text-zinc-500 shrink-0 hidden xs:block sm:block">
            Preview
          </p>

          <label className="sr-only" htmlFor="template-select">
            Template
          </label>
          <select
            id="template-select"
            value={active}
            onChange={(e) => setActive(e.target.value as TemplateId)}
            className="flex-1 min-w-0 max-w-full sm:max-w-xs h-9 rounded-md bg-zinc-900 border border-zinc-700 text-sm text-zinc-100 px-2"
          >
            {TEMPLATE_IDS.map((id) => (
              <option key={id} value={id}>
                {TEMPLATE_META[id].label}
              </option>
            ))}
          </select>

          <div className="hidden sm:flex items-center bg-zinc-900 rounded-md p-0.5 border border-zinc-800 shrink-0">
            <button
              type="button"
              onClick={() => setLayout("full")}
              className={`px-2.5 py-1 text-xs font-medium rounded ${
                layout === "full" ? "bg-zinc-700 text-white" : "text-zinc-500"
              }`}
            >
              Full
            </button>
            <button
              type="button"
              onClick={() => setLayout("grid")}
              className={`px-2.5 py-1 text-xs font-medium rounded ${
                layout === "grid" ? "bg-zinc-700 text-white" : "text-zinc-500"
              }`}
            >
              Grid
            </button>
          </div>

          <button
            type="button"
            onClick={() => setShowJson((v) => !v)}
            className={`h-9 px-2.5 text-xs font-medium rounded-md border shrink-0 ${
              showJson
                ? "bg-zinc-100 text-zinc-950 border-zinc-100"
                : "border-zinc-700 text-zinc-400"
            }`}
          >
            JSON
          </button>

          <button
            type="button"
            onClick={() => setChromeOpen((v) => !v)}
            className="sm:hidden h-9 w-9 rounded-md border border-zinc-700 text-zinc-400 text-lg leading-none shrink-0"
            aria-expanded={chromeOpen}
            aria-label="More preview options"
          >
            ⋮
          </button>
        </div>

        {chromeOpen && (
          <div className="sm:hidden px-3 pb-3 flex gap-2">
            <button
              type="button"
              onClick={() => {
                setLayout("full");
                setChromeOpen(false);
              }}
              className={`flex-1 h-9 text-xs rounded-md border ${
                layout === "full" ? "bg-zinc-100 text-zinc-950" : "border-zinc-700 text-zinc-400"
              }`}
            >
              Full page
            </button>
            <button
              type="button"
              onClick={() => {
                setLayout("grid");
                setChromeOpen(false);
              }}
              className={`flex-1 h-9 text-xs rounded-md border ${
                layout === "grid" ? "bg-zinc-100 text-zinc-950" : "border-zinc-700 text-zinc-400"
              }`}
            >
              Grid
            </button>
          </div>
        )}

        {/* Desktop chip row */}
        <div className="hidden sm:flex mx-auto max-w-screen-2xl px-4 pb-3 flex-wrap gap-1.5">
          {TEMPLATE_IDS.map((id) => (
            <button
              key={id}
              type="button"
              onClick={() => setActive(id)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md ${
                active === id
                  ? "bg-zinc-100 text-zinc-950"
                  : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800"
              }`}
            >
              {TEMPLATE_META[id].label}
            </button>
          ))}
        </div>
      </nav>

      {showJson && (
        <div className="mx-auto max-w-5xl p-4 sm:p-6">
          <div className="flex items-center justify-between gap-3 mb-4">
            <h2 className="text-sm sm:text-lg font-semibold text-zinc-300 truncate">
              Mock — {active}
            </h2>
            <button
              type="button"
              onClick={() => navigator.clipboard.writeText(JSON.stringify(content, null, 2))}
              className="px-3 py-1.5 text-xs font-medium rounded-md bg-zinc-800 text-zinc-300 border border-zinc-700 shrink-0"
            >
              Copy
            </button>
          </div>
          <pre className="overflow-auto rounded-lg bg-zinc-900 border border-zinc-800 p-3 sm:p-4 text-[11px] text-zinc-400 leading-relaxed max-h-[70svh]">
            {JSON.stringify(content, null, 2)}
          </pre>
        </div>
      )}

      {!showJson && layout === "full" && (
        <div className="relative bg-zinc-950">
          {Template ? <Template content={content} /> : null}
          <div className="pointer-events-none absolute top-2 right-2 z-30 hidden sm:block">
            <span className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider rounded-md bg-black/70 text-white border border-white/10">
              {TEMPLATE_META[active].short}
            </span>
          </div>
        </div>
      )}

      {!showJson && layout === "grid" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-1 p-1">
          {TEMPLATE_IDS.map((id) => {
            const T = DynamicTemplates[id];
            const meta = TEMPLATE_META[id];
            return (
              <div key={id} className="relative">
                <div className="absolute top-2 left-2 z-10">
                  <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-black/70 text-white border border-white/10">
                    {meta.short}
                  </span>
                </div>
                <div className="h-[70svh] sm:h-[80vh] overflow-y-auto rounded-sm bg-white">
                  {T ? <T content={MOCK_DATA[id]} /> : null}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
