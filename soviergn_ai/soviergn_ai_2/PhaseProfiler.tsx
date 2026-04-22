// src/islands/PhaseProfiler.tsx
//
// Phase boundary profiler island — flamegraph-style visualization of the
// AoS→SoA latency distribution across the document processing pipeline's
// Phase 1 (parse tree traversal) and Phase 2 (field batch scoring).

import { useState, useCallback, useRef } from "react";
import { PhaseProfiler as Profiler, formatLatency } from "../lib/phase-profiler.ts";
import type { PhaseBenchmarkResult, TimingDistribution } from "../lib/phase-profiler.ts";

type RunState =
  | { status: "idle" }
  | { status: "warming_up" }
  | { status: "running"; progress: number }
  | { status: "done"; result: PhaseBenchmarkResult }
  | { status: "error"; message: string };

interface Props {
  wasmUrl?: string;
}

export default function PhaseProfilerIsland({
  wasmUrl = "/wasm/nexus_engine_doc_viz_bg.wasm",
}: Props) {
  const [state, setState] = useState<RunState>({ status: "idle" });
  const [fieldCount, setFieldCount] = useState(4096);
  const profilerRef = useRef<Profiler | null>(null);

  const run = useCallback(async () => {
    try {
      setState({ status: "warming_up" });

      if (!profilerRef.current) {
        profilerRef.current = await Profiler.fromUrl(wasmUrl, { fieldCount });
      }

      setState({ status: "running", progress: 0 });

      const result = await profilerRef.current.runBenchmark((p) => {
        setState({ status: "running", progress: p });
      });

      setState({ status: "done", result });
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : String(err),
      });
    }
  }, [wasmUrl, fieldCount]);

  return (
    <div style={styles.root}>
      <style>{css}</style>

      {/* Header */}
      <div style={styles.header}>
        <div>
          <div style={styles.title}>03 · AOS → SOA PHASE BOUNDARY PROFILER</div>
          <div style={styles.subtitle}>
            Statistical microbenchmark · 200 trials · Tukey fence outlier rejection · IQR-based dispersion
          </div>
        </div>
        <div style={styles.controls}>
          <select
            value={fieldCount}
            onChange={(e) => {
              setFieldCount(Number(e.target.value));
              profilerRef.current = null; // Force re-instantiation with new count
            }}
            style={styles.select}
            disabled={state.status === "running" || state.status === "warming_up"}
          >
            {[512, 1024, 2048, 4096, 8192].map((n) => (
              <option key={n} value={n}>
                {n.toLocaleString()} fields
              </option>
            ))}
          </select>
          <button
            onClick={run}
            disabled={state.status === "running" || state.status === "warming_up"}
            style={{
              ...styles.btn,
              opacity: state.status === "running" || state.status === "warming_up" ? 0.5 : 1,
            }}
          >
            {state.status === "warming_up"
              ? "WARMING JIT…"
              : state.status === "running"
              ? `MEASURING… ${Math.round((state as any).progress * 100)}%`
              : state.status === "done"
              ? "RE-RUN"
              : "RUN BENCHMARK"}
          </button>
        </div>
      </div>

      {/* Progress bar */}
      {(state.status === "warming_up" || state.status === "running") && (
        <div style={styles.progressTrack}>
          <div
            style={{
              ...styles.progressFill,
              width:
                state.status === "warming_up"
                  ? "15%"
                  : `${(state as any).progress * 100}%`,
            }}
          />
          <div style={styles.progressLabel}>
            {state.status === "warming_up"
              ? "Triggering Turbofan compilation (3000 warm-up iterations)…"
              : `Trial ${Math.round((state as any).progress * 200)} / 200`}
          </div>
        </div>
      )}

      {/* Error */}
      {state.status === "error" && (
        <div style={styles.errorBox}>
          <span style={{ color: "#F87171", fontWeight: 700 }}>BENCHMARK ERROR</span>
          <pre style={{ marginTop: 6, color: "#94A3B8", fontSize: 11 }}>
            {(state as any).message}
          </pre>
        </div>
      )}

      {/* Idle placeholder */}
      {state.status === "idle" && <IdlePlaceholder />}

      {/* Results */}
      {state.status === "done" && (
        <BenchmarkResults result={(state as any).result} />
      )}
    </div>
  );
}

// ── Results panel ────────────────────────────────────────────────────────────

function BenchmarkResults({ result }: { result: PhaseBenchmarkResult }) {
  const { aos, soa, speedupP50, speedupP95, fieldCount } = result;

  return (
    <div>
      {/* Summary row */}
      <div style={styles.summaryRow}>
        <StatCard
          label="Speedup (P50)"
          value={`${speedupP50.toFixed(1)}×`}
          color="#4ADE80"
          sub={`${formatLatency(aos.p50)} → ${formatLatency(soa.p50)}`}
        />
        <StatCard
          label="Speedup (P95)"
          value={`${speedupP95.toFixed(1)}×`}
          color="#FB923C"
          sub={`${formatLatency(aos.p95)} → ${formatLatency(soa.p95)}`}
        />
        <StatCard
          label="AoS L1 Hit Rate"
          value={`${aos.l1HitRatePct.toFixed(0)}%`}
          color={aos.l1HitRatePct < 50 ? "#F87171" : "#FBBF24"}
          sub={`IQR: ${formatLatency(aos.iqr)}`}
        />
        <StatCard
          label="SoA L1 Hit Rate"
          value={`${soa.l1HitRatePct.toFixed(0)}%`}
          color={soa.l1HitRatePct > 80 ? "#4ADE80" : "#FBBF24"}
          sub={`IQR: ${formatLatency(soa.iqr)}`}
        />
        <StatCard
          label="Outliers Rejected"
          value={`${aos.outliersCount + soa.outliersCount}`}
          color="#64748B"
          sub="GC pauses / OS preemptions"
        />
      </div>

      {/* Distribution charts */}
      <div style={styles.distRow}>
        <DistributionChart distrib={aos} label="Phase 1 — AoS Parse Tree" color="#94A3B8" />
        <DistributionChart distrib={soa} label="Phase 2 — SoA Field Batch" color="#FB923C" />
      </div>

      {/* Percentile comparison table */}
      <PercentileTable aos={aos} soa={soa} />

      {/* Architectural interpretation */}
      <Interpretation aos={aos} soa={soa} speedupP50={speedupP50} fieldCount={fieldCount} />
    </div>
  );
}

// ── Distribution chart ───────────────────────────────────────────────────────
// Renders a horizontal latency histogram as a series of bars, with percentile
// markers. The bin count uses Sturges' rule: k = ⌈log₂(n)⌉ + 1.

function DistributionChart({
  distrib,
  label,
  color,
}: {
  distrib: TimingDistribution;
  label: string;
  color: string;
}) {
  const samples = distrib.cleanSamples;
  if (samples.length === 0) return null;

  // Sturges' rule for bin count
  const binCount = Math.ceil(Math.log2(samples.length)) + 1;
  const binWidth = (distrib.max - distrib.min) / binCount;

  const bins: number[] = Array(binCount).fill(0);
  for (const s of samples) {
    const idx = Math.min(binCount - 1, Math.floor((s - distrib.min) / binWidth));
    bins[idx]++;
  }
  const maxBin = Math.max(...bins);

  return (
    <div style={styles.chartContainer}>
      <div style={{ ...styles.chartLabel, color }}>{label}</div>
      <div style={styles.chartBars}>
        {bins.map((count, i) => {
          const barPct = (count / maxBin) * 100;
          const binStart = distrib.min + i * binWidth;
          // Check if this bin contains a percentile marker
          const isP50 = distrib.p50 >= binStart && distrib.p50 < binStart + binWidth;
          const isP95 = distrib.p95 >= binStart && distrib.p95 < binStart + binWidth;
          return (
            <div
              key={i}
              title={`${formatLatency(binStart)} – ${formatLatency(binStart + binWidth)}: ${count} samples`}
              style={{
                ...styles.bar,
                height: `${Math.max(barPct, 1)}%`,
                background: isP95
                  ? "#F87171"
                  : isP50
                  ? "#FBBF24"
                  : color,
                opacity: 0.7 + (barPct / 100) * 0.3,
              }}
            />
          );
        })}
      </div>
      <div style={styles.chartXAxis}>
        <span style={styles.axisLabel}>{formatLatency(distrib.min)}</span>
        <span style={{ ...styles.axisLabel, color: "#FBBF24" }}>
          P50: {formatLatency(distrib.p50)}
        </span>
        <span style={{ ...styles.axisLabel, color: "#F87171" }}>
          P95: {formatLatency(distrib.p95)}
        </span>
        <span style={styles.axisLabel}>{formatLatency(distrib.max)}</span>
      </div>
    </div>
  );
}

// ── Percentile table ─────────────────────────────────────────────────────────

function PercentileTable({
  aos,
  soa,
}: {
  aos: TimingDistribution;
  soa: TimingDistribution;
}) {
  const rows = [
    { label: "Min", aos: aos.min, soa: soa.min },
    { label: "P50", aos: aos.p50, soa: soa.p50 },
    { label: "P75", aos: aos.p75, soa: soa.p75 },
    { label: "P90", aos: aos.p90, soa: soa.p90 },
    { label: "P95", aos: aos.p95, soa: soa.p95 },
    { label: "P99", aos: aos.p99, soa: soa.p99 },
    { label: "Max", aos: aos.max, soa: soa.max },
    { label: "σ",   aos: aos.stddev, soa: soa.stddev },
  ];

  return (
    <div style={styles.table}>
      <div style={styles.tableRow}>
        <div style={{ ...styles.tableCell, ...styles.tableHeader }}>Percentile</div>
        <div style={{ ...styles.tableCell, ...styles.tableHeader, color: "#94A3B8" }}>
          AoS Parse Tree (Phase 1)
        </div>
        <div style={{ ...styles.tableCell, ...styles.tableHeader, color: "#FB923C" }}>
          SoA Field Batch (Phase 2)
        </div>
        <div style={{ ...styles.tableCell, ...styles.tableHeader }}>Speedup</div>
      </div>
      {rows.map((row) => {
        const speedup = row.aos / row.soa;
        return (
          <div key={row.label} style={styles.tableRow}>
            <div style={{ ...styles.tableCell, color: "#64748B" }}>{row.label}</div>
            <div style={{ ...styles.tableCell, color: "#94A3B8" }}>
              {formatLatency(row.aos)}
            </div>
            <div style={{ ...styles.tableCell, color: "#FB923C" }}>
              {formatLatency(row.soa)}
            </div>
            <div
              style={{
                ...styles.tableCell,
                color: speedup > 5 ? "#4ADE80" : speedup > 2 ? "#FBBF24" : "#94A3B8",
                fontWeight: 700,
              }}
            >
              {speedup.toFixed(1)}×
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Architectural interpretation ─────────────────────────────────────────────

function Interpretation({
  aos,
  soa,
  speedupP50,
  fieldCount,
}: {
  aos: TimingDistribution;
  soa: TimingDistribution;
  speedupP50: number;
  fieldCount: number;
}) {
  // Working set size estimates
  const aosBytesKB = ((fieldCount * 120) / 1024).toFixed(0); // ~120 bytes/ContentStreamNode
  const soaBytesKB = ((fieldCount * 16) / 1024).toFixed(0);  // 4 × f32 × fieldCount

  return (
    <div style={styles.interpretation}>
      <div style={{ fontSize: 11, color: "#F59E0B", fontWeight: 700, marginBottom: 8 }}>
        CACHE BEHAVIOR ANALYSIS
      </div>
      <div style={{ fontSize: 11, color: "#64748B", lineHeight: 1.7 }}>
        <p>
          <span style={{ color: "#94A3B8" }}>Phase 1 (AoS, {aosBytesKB} KiB working set):</span>{" "}
          ContentStreamNode traversal accesses each node's 120-byte struct sequentially.
          The struct layout interleaves operator discriminants, SmallVec heap pointers,
          and byte offsets. The CPU's hardware prefetcher cannot span struct boundaries —
          each field access is a potential L1 miss. At {fieldCount.toLocaleString()} nodes,
          the {aosBytesKB}KB working set exceeds most L1 caches (32-48KB), causing
          regular L2 and DRAM accesses.{" "}
          Observed σ/μ = {(aos.stddev / aos.mean).toFixed(2)} — high dispersion is
          characteristic of mixed L1/L2 hit behavior.
        </p>
        <p>
          <span style={{ color: "#FB923C" }}>Phase 2 (SoA, {soaBytesKB} KiB working set):</span>{" "}
          The bounding box scoring loop iterates over x_min[0..N], then y_min[0..N], etc.
          Each array is {((fieldCount * 4) / 1024).toFixed(1)}KB — sequential f32 values
          that the prefetcher can predict with stride-1 accuracy. One cache line (64 bytes)
          holds 16 f32 values, meaning the entire x_min array for {fieldCount.toLocaleString()} fields
          requires only {Math.ceil((fieldCount * 4) / 64)} cache line loads. At {soaBytesKB}KB
          total working set, the SoA batch fits in L1 on most CPUs.{" "}
          Observed σ/μ = {(soa.stddev / soa.mean).toFixed(2)} — low dispersion confirms
          consistent L1 residence.
        </p>
        <p>
          <span style={{ color: "#4ADE80" }}>{speedupP50.toFixed(1)}× P50 speedup</span> at the
          phase boundary. This is not a Rust-vs-JS speed comparison — it is a cache utilization
          comparison within the same WASM binary, between two data layouts applied to the same
          transformation problem. The speedup scales with field count: at 512 fields both
          layouts fit in L1; at 8192 fields the AoS layout begins spilling to DRAM. The
          optimal inflection point where SoA layout investment pays off is approximately
          where the AoS working set exceeds the L1 cache size (~32KB, or ~267 nodes at 120 bytes).
        </p>
      </div>
    </div>
  );
}

// ── Idle placeholder ─────────────────────────────────────────────────────────

function IdlePlaceholder() {
  return (
    <div style={styles.placeholder}>
      <div style={{ fontSize: 12, color: "#334155", marginBottom: 8 }}>
        Click RUN BENCHMARK to measure the cache behavior difference between the
        AoS parse tree (Phase 1) and the SoA field batch (Phase 2).
      </div>
      <div style={{ fontSize: 10, color: "#1E293B", fontFamily: "monospace" }}>
        Protocol: 3000 JIT warm-up iterations → 200 interleaved trials →
        Tukey fence outlier rejection → percentile distribution
      </div>
    </div>
  );
}

// ── Stat card ────────────────────────────────────────────────────────────────

function StatCard({
  label, value, color, sub,
}: { label: string; value: string; color: string; sub: string }) {
  return (
    <div style={{ ...styles.statCard, borderColor: color + "40" }}>
      <div style={{ fontSize: 9, color: "#475569", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 22, color, fontWeight: 700, fontFamily: "monospace" }}>{value}</div>
      <div style={{ fontSize: 9, color: "#475569", marginTop: 4 }}>{sub}</div>
    </div>
  );
}

// ── Styles ───────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  root: {
    background: "#060810",
    border: "1px solid #1E293B",
    borderTop: "2px solid #FB923C",
    borderRadius: 6,
    padding: 20,
    fontFamily: "'IBM Plex Mono', 'Courier New', monospace",
    color: "#E2E8F0",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 16,
    gap: 16,
  },
  title: {
    fontSize: 11, color: "#FB923C", fontWeight: 700, letterSpacing: "0.1em",
  },
  subtitle: {
    fontSize: 10, color: "#475569", marginTop: 3,
  },
  controls: {
    display: "flex", gap: 8, alignItems: "center",
  },
  select: {
    background: "#0D1117", border: "1px solid #334155", color: "#94A3B8",
    padding: "5px 10px", borderRadius: 3, fontFamily: "monospace", fontSize: 11,
    cursor: "pointer",
  },
  btn: {
    background: "#FB923C", color: "#000", border: "none", padding: "6px 16px",
    borderRadius: 3, fontFamily: "monospace", fontSize: 11, fontWeight: 700,
    cursor: "pointer", letterSpacing: "0.05em",
  },
  progressTrack: {
    background: "#0D1117", borderRadius: 3, height: 24, position: "relative",
    overflow: "hidden", marginBottom: 16, border: "1px solid #1E293B",
  },
  progressFill: {
    position: "absolute", top: 0, left: 0, height: "100%",
    background: "#FB923C22", transition: "width 0.3s",
  },
  progressLabel: {
    position: "absolute", top: 0, left: 0, right: 0, height: "100%",
    display: "flex", alignItems: "center", paddingLeft: 12,
    fontSize: 10, color: "#FB923C",
  },
  errorBox: {
    padding: "12px 16px", background: "#F8717112", border: "1px solid #F87171",
    borderRadius: 4, marginBottom: 16,
  },
  summaryRow: {
    display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap",
  },
  statCard: {
    flex: 1, minWidth: 110, padding: "10px 12px",
    background: "#0D1117", border: "1px solid", borderRadius: 4,
  },
  distRow: {
    display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16,
  },
  chartContainer: {
    background: "#0D1117", border: "1px solid #1E293B", borderRadius: 4, padding: 12,
  },
  chartLabel: {
    fontSize: 10, fontWeight: 700, marginBottom: 10, letterSpacing: "0.05em",
  },
  chartBars: {
    display: "flex", alignItems: "flex-end", gap: 1.5,
    height: 80, background: "#060810", borderRadius: 2, padding: "2px 2px 0",
  },
  bar: {
    flex: 1, minWidth: 2, borderRadius: "1px 1px 0 0",
    transition: "height 0.3s",
    cursor: "pointer",
  },
  chartXAxis: {
    display: "flex", justifyContent: "space-between", marginTop: 6,
  },
  axisLabel: {
    fontSize: 9, color: "#475569",
  },
  table: {
    border: "1px solid #1E293B", borderRadius: 4, overflow: "hidden", marginBottom: 16,
  },
  tableRow: {
    display: "grid", gridTemplateColumns: "80px 1fr 1fr 80px",
    borderBottom: "1px solid #0F172A",
  },
  tableCell: {
    padding: "6px 12px", fontSize: 10, color: "#94A3B8",
  },
  tableHeader: {
    background: "#0D1117", fontSize: 9, color: "#475569",
    fontWeight: 700, letterSpacing: "0.08em",
  },
  interpretation: {
    padding: "12px 16px", background: "#0D1117",
    border: "1px solid #1E293B", borderRadius: 4,
  },
  placeholder: {
    padding: "24px 16px", background: "#0D1117",
    border: "1px solid #1E293B", borderRadius: 4, textAlign: "center",
  },
};

const css = `
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&display=swap');
`;
