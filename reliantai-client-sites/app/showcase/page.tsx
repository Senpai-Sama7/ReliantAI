"use client";

import { useState, useEffect, useCallback, useRef, useMemo, type ComponentType } from "react";
import dynamic from "next/dynamic";
import MOCK_DATA from "@/lib/mock-data";
import { TEMPLATES, type TemplateMeta } from "@/lib/template-meta";
import type { SiteContent } from "@/types/SiteContent";
import DeviceFrame from "@/components/showcase/DeviceFrame";
import CodeBlock from "@/components/showcase/CodeBlock";

const slugify = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
type TemplateId = (typeof TEMPLATES)[number]["id"];
type View = "preview" | "grid" | "prompt" | "compare";
type Device = "desktop" | "tablet" | "mobile";

// ─── Dynamic template loader ─────────────────────────────────────────
const LOADER_CONTENT = Object.freeze({} as unknown as SiteContent);

const Loader = () => (
  <div className="flex items-center justify-center h-[60vh] bg-zinc-950">
    <div className="flex flex-col items-center gap-3">
      <div className="w-8 h-8 border-2 border-zinc-700 border-t-white rounded-full animate-spin" />
      <span className="text-xs text-zinc-500 tracking-widest uppercase">Rendering</span>
    </div>
  </div>
);

const DynamicTemplates: Record<string, ComponentType<{ content: SiteContent }>> = {};
for (const t of TEMPLATES) {
  DynamicTemplates[t.id] = dynamic(() => import(`@/templates/${t.id}`), { loading: Loader });
}

// ─── SVG Icons ────────────────────────────────────────────────────────
function IconDesktop({ className = "w-4 h-4" }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 17.25v1.007a3 3 0 0 1-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0 1 15 18.257V17.25m-6-12h6m-3-3v3M3.75 17.25h16.5a1.5 1.5 0 0 0 1.5-1.5V5.25a1.5 1.5 0 0 0-1.5-1.5H3.75a1.5 1.5 0 0 0-1.5 1.5v10.5a1.5 1.5 0 0 0 1.5 1.5Z" /></svg>;
}
function IconTablet({ className = "w-4 h-4" }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5h3m-6.75 2.25h10.5a2.25 2.25 0 0 0 2.25-2.25V4.5a2.25 2.25 0 0 0-2.25-2.25H6.75A2.25 2.25 0 0 0 4.5 4.5v15a2.25 2.25 0 0 0 2.25 2.25Z" /></svg>;
}
function IconPhone({ className = "w-4 h-4" }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M10.5 1.5H8.25A2.25 2.25 0 0 0 6 3.75v16.5a2.25 2.25 0 0 0 2.25 2.25h7.5A2.25 2.25 0 0 0 18 20.25V3.75a2.25 2.25 0 0 0-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18.75h3" /></svg>;
}
function IconChevronLeft({ className = "w-4 h-4" }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>;
}
function IconChevronRight({ className = "w-4 h-4" }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>;
}
function IconX({ className = "w-4 h-4" }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>;
}
function IconSparkles({ className = "w-4 h-4" }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" /></svg>;
}
function IconCode({ className = "w-4 h-4" }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" /></svg>;
}
function IconGrid({ className = "w-4 h-4" }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" /></svg>;
}
function IconColumns({ className = "w-4 h-4" }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0h9m-9 0a9 9 0 1 0 9 9m-9 9v4.5m0-4.5h9m-9 4.5a9 9 0 0 1 9-9m0 9v4.5m0-4.5h-9m9 0a9 9 0 0 1-9 9" /></svg>;
}

// ─── Template Card ────────────────────────────────────────────────────
function TemplateCard({ meta, isActive, onClick }: { meta: TemplateMeta; isActive: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      aria-label={`Select ${meta.tradeLabel} template`}
      className={`group relative w-full text-left rounded-xl transition-all duration-200 ease-out ${
        isActive
          ? "bg-gradient-to-br from-zinc-800/80 to-zinc-900 ring-1 ring-white/10 shadow-lg shadow-black/20"
          : "hover:bg-zinc-800/40"
      }`}
    >
      <div className="p-3.5">
        <div className="flex items-center gap-2.5">
          <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 transition-shadow duration-300 ${meta.accentBg} ${isActive ? `shadow-[0_0_8px_var(--tw-shadow-color)]` : ""}`}
            style={isActive ? { boxShadow: `0 0 8px ${meta.primaryColor}60` } : undefined}
          />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5">
              <span className={`text-[13px] font-semibold truncate transition-colors ${isActive ? "text-white" : "text-zinc-400 group-hover:text-zinc-200"}`}>
                {meta.tradeLabel}
              </span>
              <span className={`text-[9px] px-1.5 py-px rounded-full font-medium tracking-wide transition-colors ${
                meta.theme === "light"
                  ? isActive ? "bg-violet-500/20 text-violet-300 ring-1 ring-violet-500/30" : "bg-violet-500/10 text-violet-400/60"
                  : isActive ? "bg-zinc-700/80 text-zinc-300 ring-1 ring-zinc-600/50" : "bg-zinc-800/80 text-zinc-500"
              }`}>
                {meta.theme === "light" ? "LIGHT" : "DARK"}
              </span>
            </div>
            <p className={`text-[11px] mt-0.5 transition-colors ${isActive ? "text-zinc-300" : "text-zinc-600 group-hover:text-zinc-500"}`}>
              {meta.label}
            </p>
          </div>
          {isActive && (
            <div className="flex-shrink-0">
              <div className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center">
                <svg className="w-3 h-3 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
            </div>
          )}
        </div>
      </div>
    </button>
  );
}

// ─── View Tab ─────────────────────────────────────────────────────────
function ViewTab({ icon, label, active, onClick, ariaLabel }: { icon: React.ReactNode; label: string; active: boolean; onClick: () => void; ariaLabel?: string }) {
  return (
    <button
      onClick={onClick}
      aria-label={ariaLabel || label}
      role="tab"
      aria-selected={active}
      className={`relative flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded-lg transition-all duration-150 ${
        active ? "text-white" : "text-zinc-500 hover:text-zinc-300"
      }`}
    >
      {active && (
        <div className="absolute inset-0 bg-zinc-700/80 rounded-lg ring-1 ring-white/5" />
      )}
      <span className="relative z-10">{icon}</span>
      <span className="relative z-10">{label}</span>
    </button>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────
export default function ShowcasePage() {
  const [active, setActive] = useState<TemplateId>("hvac-reliable-blue");
  const [view, setView] = useState<View>("preview");
  const [device, setDevice] = useState<Device>("desktop");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [screenKey, setScreenKey] = useState(0);
  const [compareIds, setCompareIds] = useState<[TemplateId, TemplateId]>(["hvac-reliable-blue", "plumbing-trustworthy-navy"]);
  const [mounted, setMounted] = useState(false);
  const [overrides, setOverrides] = useState<Partial<{ business_name: string; phone: string; city: string; state: string; headline: string }>>({});

  const meta = TEMPLATES.find((t) => t.id === active)!;
  const baseContent = MOCK_DATA[active];
  const content = useMemo(() => ({
    ...baseContent,
    business: { ...baseContent.business, ...overrides },
    hero: { ...baseContent.hero, ...(overrides.headline && { headline: overrides.headline }) },
  }), [baseContent, overrides]);

  useEffect(() => setOverrides({}), [active]);

  useEffect(() => setMounted(true), []);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const idx = TEMPLATES.findIndex((t) => t.id === active);
      if (e.key === "ArrowDown" || e.key === "ArrowRight") {
        e.preventDefault();
        const next = TEMPLATES[(idx + 1) % TEMPLATES.length];
        setActive(next.id);
        setScreenKey((k) => k + 1);
      } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
        e.preventDefault();
        const prev = TEMPLATES[(idx - 1 + TEMPLATES.length) % TEMPLATES.length];
        setActive(prev.id);
        setScreenKey((k) => k + 1);
      } else if (e.key === "\\" && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        setSidebarOpen((s) => !s);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [active]);

  if (!mounted) {
    return (
      <div className="h-screen bg-zinc-950 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-zinc-700 border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  const Template = DynamicTemplates[active];

  return (
    <div className="h-screen bg-zinc-950 text-white flex flex-col overflow-hidden">
      {/* ─── Header ──────────────────────────────────────────── */}
      <header className="flex-shrink-0 border-b border-white/[0.06] bg-zinc-950/80 backdrop-blur-xl z-50">
        <div className="flex items-center justify-between px-4 h-11">
          {/* Left: Brand */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded-md bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center">
                <span className="text-[8px] font-bold text-white">R</span>
              </div>
              <div className="flex flex-col">
                <span className="text-[11px] font-semibold text-zinc-200 leading-none tracking-wide">Showcase</span>
                <span className="text-[9px] text-zinc-600 leading-none mt-0.5">Template Studio</span>
              </div>
            </div>
            <div className="w-px h-5 bg-white/[0.06]" />
            <span className="text-[10px] text-zinc-600 font-mono tabular-nums">
              {meta.tradeLabel} · {meta.theme === "light" ? "Light" : "Dark"} · {meta.heroLayout === "single" ? "1-Column" : "2-Column"}
            </span>
          </div>

          {/* Center: View tabs */}
          <div className="flex items-center bg-zinc-900/80 rounded-lg p-0.5 ring-1 ring-white/[0.06]">
<ViewTab icon={<IconSparkles className="w-3.5 h-3.5" />} label="Preview" active={view === "preview"} onClick={() => setView("preview")} aria-label="Preview view" />
              <ViewTab icon={<IconGrid className="w-3.5 h-3.5" />} label="Grid" active={view === "grid"} onClick={() => setView("grid")} aria-label="Grid view" />
              <ViewTab icon={<IconCode className="w-3.5 h-3.5" />} label="Prompt" active={view === "prompt"} onClick={() => setView("prompt")} aria-label="Prompt view" />
              <ViewTab icon={<IconColumns className="w-3.5 h-3.5" />} label="Compare" active={view === "compare"} onClick={() => setView("compare")} aria-label="Compare view" />
          </div>

          {/* Right: Device & sidebar toggle */}
          <div className="flex items-center gap-2">
            {view === "preview" && (
              <div className="flex items-center bg-zinc-900/80 rounded-lg p-0.5 ring-1 ring-white/[0.06]">
                {([["desktop", <IconDesktop className="w-3.5 h-3.5" />], ["tablet", <IconTablet className="w-3.5 h-3.5" />], ["mobile", <IconPhone className="w-3.5 h-3.5" />]] as const).map(([d, icon]) => (
                  <button
                    key={d}
                    onClick={() => { setDevice(d as Device); setScreenKey((k) => k + 1); }}
                    aria-label={`Switch to ${d} view`}
                    className={`relative p-1.5 rounded-md transition-all ${
                      device === d ? "text-white" : "text-zinc-500 hover:text-zinc-300"
                    }`}
                  >
                    {device === d && <div className="absolute inset-0 bg-zinc-700/80 rounded-md ring-1 ring-white/5" />}
                    <span className="relative z-10">{icon}</span>
                  </button>
                ))}
              </div>
            )}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className={`p-1.5 rounded-lg transition-all ${sidebarOpen ? "bg-zinc-800 text-zinc-300 ring-1 ring-white/[0.06]" : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50"}`}
              title={sidebarOpen ? "Hide sidebar (\\)" : "Show sidebar (\\)"}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* ─── Sidebar ─────────────────────────────────────────── */}
        <aside className={`flex-shrink-0 border-r border-white/[0.06] bg-zinc-950 overflow-hidden transition-all duration-300 ease-out ${sidebarOpen ? "w-72" : "w-0"}`}>
          <div className="w-72 h-full flex flex-col">
            {/* Template selector */}
            <div className="flex-1 overflow-y-auto pb-4">
              <div className="p-3 space-y-1">
                <div className="flex items-center justify-between px-1 mb-1">
                  <span className="text-[9px] font-semibold tracking-[0.15em] uppercase text-zinc-600">Templates</span>
                  <span className="text-[9px] text-zinc-700 tabular-nums">{TEMPLATES.length}</span>
                </div>
                {TEMPLATES.map((t) => (
                  <TemplateCard
                    key={t.id}
                    meta={t}
                    isActive={active === t.id}
                    onClick={() => { setActive(t.id); setScreenKey((k) => k + 1); }}
                  />
                ))}
              </div>

              {/* Divider */}
              <div className="mx-3 border-t border-white/[0.04]" />

              {/* Template details panel */}
              <div className="p-3 space-y-4">
                <div>
                  <span className="text-[9px] font-semibold tracking-[0.15em] uppercase text-zinc-600">Overview</span>
                  <p className="text-[11px] text-zinc-400 mt-2 leading-relaxed">{meta.description}</p>
                </div>

                {/* Metadata grid */}
                <div className="grid grid-cols-2 gap-1.5">
                  <DetailCell label="Personality" value={meta.personality} accent />
                  <DetailCell label="Theme" value={meta.theme === "light" ? "Light" : "Dark"} />
                  <DetailCell label="Hero" value={meta.heroLayout === "single" ? "Single" : "Dual"} />
                  <DetailCell label="Accent" value={meta.colorName}>
                    <div className="w-3 h-3 rounded-full mt-1" style={{ backgroundColor: meta.primaryColor }} />
                  </DetailCell>
                </div>

                {/* Best for */}
                <div>
                  <span className="text-[9px] font-semibold tracking-[0.15em] uppercase text-zinc-600">Best For</span>
                  <p className="text-[11px] text-zinc-400 mt-1">{meta.bestFor}</p>
                </div>

                {/* Unique features */}
                <div>
                  <span className="text-[9px] font-semibold tracking-[0.15em] uppercase text-zinc-600">Differentiators</span>
                  <div className="mt-1.5 space-y-1">
                    {meta.uniqueFeatures.slice(0, 4).map((f, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-[11px] text-zinc-500">
                        <span className={`w-1 h-1 rounded-full mt-1.5 flex-shrink-0 ${meta.accentBg}`} />
                        {f.length > 55 ? f.slice(0, 55) + "…" : f}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Live data override */}
                <div className="pt-3 border-t border-white/[0.04]">
                  <span className="text-[9px] font-semibold tracking-[0.15em] uppercase text-zinc-600">Live Data</span>
                  <div className="mt-2 space-y-2">
                    <DataInput label="Business" value={content.business.business_name} onChange={(v) => setOverrides((o) => ({ ...o, business_name: v }))} />
                    <DataInput label="Phone" value={content.business.phone} onChange={(v) => setOverrides((o) => ({ ...o, phone: v }))} />
                    <DataInput label="Location" value={`${content.business.city}, ${content.business.state}`} onChange={(v) => {
                      const p = v.split(", ");
                      if (p.length === 2) setOverrides((o) => ({ ...o, city: p[0], state: p[1] }));
                    }} />
                    <DataInput label="Headline" value={content.hero.headline} onChange={(v) => setOverrides((o) => ({ ...o, headline: v }))} />
                  </div>
                </div>

                {/* Prompt shortcut */}
                <div className="pt-3 border-t border-white/[0.04]">
                  <button
                    onClick={() => setView("prompt")}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 text-[11px] font-medium rounded-lg bg-zinc-800/80 text-zinc-300 hover:bg-zinc-700 hover:text-white ring-1 ring-white/[0.06] hover:ring-white/10 transition-all"
                  >
                    <IconCode className="w-3.5 h-3.5" />
                    View Generation Prompt
                  </button>
                </div>
              </div>
            </div>

            {/* Bottom keyboard hint */}
            <div className="flex-shrink-0 border-t border-white/[0.04] px-3 py-2.5">
              <div className="flex items-center gap-2 text-[9px] text-zinc-600">
                <kbd className="px-1 py-0.5 rounded bg-zinc-800 ring-1 ring-zinc-700 font-mono text-[9px]">↑↓</kbd>
                <span>Navigate</span>
                <kbd className="px-1 py-0.5 rounded bg-zinc-800 ring-1 ring-zinc-700 font-mono text-[9px] ml-2">\</kbd>
                <span>Toggle sidebar</span>
              </div>
            </div>
          </div>
        </aside>

        {/* ─── Main content ────────────────────────────────────── */}
        <main className="flex-1 min-w-0 relative">
          {/* Preview */}
          {view === "preview" && (
            <div key={screenKey} className="h-full">
              <DeviceFrame device={device} url={`${slugify(content.business.business_name)}.reliantai.org`}>
                {Template ? <Template content={content} /> : <Loader />}
              </DeviceFrame>
            </div>
          )}

          {/* Grid */}
          {view === "grid" && (
            <div className="h-full overflow-y-auto">
              <div className="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3">
                {TEMPLATES.map((t) => {
                  const T = DynamicTemplates[t.id];
                  return (
                    <div key={t.id} className="group relative border-b border-r border-white/[0.04]">
                      {/* Overlay on hover */}
                      <div className="absolute inset-0 z-10 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col items-center justify-center gap-3">
                        <button
                          onClick={() => { setActive(t.id); setView("preview"); setScreenKey((k) => k + 1); }}
                          className="px-5 py-2.5 text-sm font-medium bg-white text-zinc-950 rounded-xl hover:bg-zinc-100 transition-colors shadow-lg"
                        >
                          Full Preview
                        </button>
                        <button
                          onClick={() => { setActive(t.id); setView("prompt"); }}
                          className="px-4 py-1.5 text-xs font-medium bg-zinc-800/90 text-zinc-300 rounded-lg hover:bg-zinc-700 transition-colors ring-1 ring-white/10"
                        >
                          <span className="flex items-center gap-1.5"><IconCode className="w-3 h-3" /> View Prompt</span>
                        </button>
                      </div>
                      {/* Template label */}
                      <div className="absolute top-3 left-3 z-5 flex items-center gap-1.5">
                        <div className={`w-2 h-2 rounded-full ${t.accentBg}`} />
                        <span className="text-[11px] font-semibold text-white drop-shadow-lg">{t.tradeLabel}</span>
                      </div>
                      <div className="h-[70vh] overflow-hidden">
                        {T ? <T content={MOCK_DATA[t.id]} /> : <Loader />}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Prompt */}
          {view === "prompt" && (
            <div className="h-full overflow-y-auto">
              <div className="max-w-5xl mx-auto px-8 py-10 space-y-8">
                {/* Header */}
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`w-3 h-3 rounded-full ${meta.accentBg}`} />
                    <h2 className="text-xl font-semibold text-white">{meta.tradeLabel} — {meta.label}</h2>
                  </div>
                  <p className="text-sm text-zinc-500">Production-ready generation prompt. Copy and paste to recreate this template with any business.</p>
                </div>

                {/* Metadata cards */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <MetaCard label="Theme" value={meta.theme === "light" ? "Light" : "Dark"} accent={meta.primaryColor} />
                  <MetaCard label="Accent Color" value={meta.colorName} accent={meta.primaryColor} />
                  <MetaCard label="Hero Layout" value={meta.heroLayout === "single" ? "Single Column" : meta.heroLayout === "dual-card" ? "Dual + Card" : "Dual + Decorative"} />
                  <MetaCard label="Sections" value="8 — Contact, Trust, Hero, Stats, Services, About, Reviews, FAQ" />
                </div>

                {/* The code block */}
                <CodeBlock code={meta.prompt} language="prompt" maxHeight="40vh" />

                {/* Unique features */}
                <div>
                  <h3 className="text-sm font-semibold text-zinc-300 mt-6 mb-3">Key Differentiators</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {meta.uniqueFeatures.map((f, i) => (
                      <div key={i} className="flex items-start gap-2.5 p-3 rounded-lg bg-zinc-900/50 ring-1 ring-white/[0.04]">
                        <span className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${meta.accentBg}`} />
                        <span className="text-[12px] text-zinc-400 leading-relaxed">{f}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Compare */}
          {view === "compare" && (
            <div className="h-full flex flex-col">
              {/* Compare selector bar */}
              <div className="flex-shrink-0 border-b border-white/[0.06] bg-zinc-950/80 backdrop-blur-md px-4 py-2 flex items-center gap-4">
                <span className="text-[10px] text-zinc-600 uppercase tracking-wider font-semibold">Left</span>
                <select
                  value={compareIds[0]}
                  onChange={(e) => setCompareIds([e.target.value as TemplateId, compareIds[1]])}
                  className="text-[11px] bg-zinc-800 ring-1 ring-white/[0.06] rounded-md px-2 py-1 text-zinc-300 border-0 focus:ring-white/10"
                >
                  {TEMPLATES.map((t) => <option key={t.id} value={t.id}>{t.tradeLabel} — {t.label}</option>)}
                </select>
                <span className="text-[10px] text-zinc-700">vs</span>
                <span className="text-[10px] text-zinc-600 uppercase tracking-wider font-semibold">Right</span>
                <select
                  value={compareIds[1]}
                  onChange={(e) => setCompareIds([compareIds[0], e.target.value as TemplateId])}
                  className="text-[11px] bg-zinc-800 ring-1 ring-white/[0.06] rounded-md px-2 py-1 text-zinc-300 border-0 focus:ring-white/10"
                >
                  {TEMPLATES.map((t) => <option key={t.id} value={t.id}>{t.tradeLabel} — {t.label}</option>)}
                </select>
              </div>

              <div className="flex-1 flex min-h-0">
                {compareIds.map((id, i) => {
                  const T = DynamicTemplates[id];
                  const m = TEMPLATES.find((t) => t.id === id)!;
                  return (
                    <div key={id} className="flex-1 min-w-0 flex flex-col border-r border-white/[0.04] last:border-r-0">
                      <div className="flex-shrink-0 flex items-center gap-2 px-3 py-2 bg-zinc-900/80 border-b border-white/[0.04]">
                        <div className={`w-2 h-2 rounded-full ${m.accentBg}`} />
                        <span className="text-[11px] font-semibold text-zinc-200">{m.tradeLabel}</span>
                        <span className="text-[10px] text-zinc-600">{m.label}</span>
                        <span className={`text-[9px] px-1.5 py-px rounded-full ${
                          m.theme === "light" ? "bg-violet-500/15 text-violet-400" : "bg-zinc-800 text-zinc-500"
                        }`}>
                          {m.theme === "light" ? "LIGHT" : "DARK"}
                        </span>
                      </div>
                      <div className="flex-1 overflow-y-auto">
                        {T ? <T content={MOCK_DATA[id]} /> : <Loader />}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

// ─── Sub-components ────────────────────────────────────────────────────

function DetailCell({ label, value, accent, children }: { label: string; value: string; accent?: boolean; children?: React.ReactNode }) {
  return (
    <div className="p-2 rounded-lg bg-zinc-900/50 ring-1 ring-white/[0.03]">
      <div className="text-[8px] text-zinc-600 uppercase tracking-wider font-semibold">{label}</div>
      <div className="text-[11px] text-zinc-300 mt-0.5 font-medium">{value}</div>
      {children && <div className="mt-1">{children}</div>}
    </div>
  );
}

function MetaCard({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="p-3 rounded-xl bg-zinc-900 ring-1 ring-white/[0.06]">
      <div className="text-[9px] text-zinc-600 uppercase tracking-wider font-semibold mb-1">{label}</div>
      <div className="flex items-center gap-2">
        {accent && <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: accent }} />}
        <span className="text-sm font-medium text-zinc-200">{value}</span>
      </div>
    </div>
  );
}

function DataInput({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="text-[9px] font-semibold tracking-[0.1em] uppercase text-zinc-600 block mb-0.5">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-2.5 py-1.5 text-[11px] bg-zinc-900 ring-1 ring-white/[0.06] rounded-md text-zinc-300 placeholder-zinc-700 focus:outline-none focus:ring-white/10 transition-all"
      />
    </div>
  );
}