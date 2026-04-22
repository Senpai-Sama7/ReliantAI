// src/islands/NexusMemoryViz.tsx
//
// React island component for the Executable Topology Specification.
//
// This component is hydrated by Astro with the `client:visible` directive,
// meaning the WASM module does not boot until this section scrolls into the
// viewport — matching the "lazy island" pattern described in the architecture.
//
// Memory reading safety is entirely delegated to WasmMemoryBridge, which
// implements the seqlock protocol. This component's only responsibility is
// rendering the sampled state and managing the rAF loop.

import { useState, useEffect, useRef, useCallback } from "react";
import { WasmMemoryBridge } from "../lib/wasm-bridge.ts";
import type { MemorySample, MemoryLayout } from "../lib/wasm-bridge.ts";

// ── Layout constants (must match Rust doc_viz.rs) ──────────────────────────
const LAYOUT_REGIONS = [
  {
    id:    "ctrl",
    label: "Control Block",
    color: "#F59E0B",
    desc:  "Int32Array[5] — WRITE_IDX, READY_IDX, CONSUME_IDX, INPUT_WRITE, INPUT_READ",
    getOffset: (l: MemoryLayout) => l.ctrlBlockOffset,
    getBytes:  (l: MemoryLayout) => l.ctrlBlockBytes,
  },
  {
    id:    "input_ring",
    label: "Input Ring",
    color: "#818CF8",
    desc:  "Float32Array — pointerrawupdate ring, allocation-free main thread writes",
    getOffset: (l: MemoryLayout) => l.inputRingOffset,
    getBytes:  (l: MemoryLayout) => l.inputRingCapacity * 8, // 2 × f32 × capacity
  },
  {
    id:    "fb_a",
    label: "Framebuffer A",
    color: "#4ADE80",
    desc:  "Uint8ClampedArray — RGBA, written by Rust Worker, read by OffscreenCanvas",
    getOffset: (l: MemoryLayout) => l.framebuffer0Offset,
    getBytes:  (l: MemoryLayout) => l.framebufferBytes,
  },
  {
    id:    "fb_b",
    label: "Framebuffer B",
    color: "#34D399",
    desc:  "Uint8ClampedArray — double-buffer swap target",
    getOffset: (l: MemoryLayout) => l.framebuffer1Offset,
    getBytes:  (l: MemoryLayout) => l.framebufferBytes,
  },
  {
    id:    "soa_batch",
    label: "SoA FieldBatch",
    color: "#FB923C",
    desc:  "Vec<f32>×4 — x_min, y_min, x_max, y_max, SIMD-eligible Phase 2 layout",
    getOffset: (l: MemoryLayout) => l.soaBatchOffset,
    getBytes:  (l: MemoryLayout) => l.soaBatchFieldCount * 16, // 4 × f32 × fields
  },
] as const;

type BridgeState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; bridge: WasmMemoryBridge }
  | { status: "error"; message: string }
  | { status: "unavailable"; reason: string }; // SAB not available (missing COOP/COEP)

interface VizState {
  sample:       MemorySample | null;
  invariants:   number;
  sampleRate:   number;  // samples per second, measured over 60-sample window
  inconsistent: number;  // cumulative inconsistent sample count
}

interface Props {
  /**
   * URL of the doc-viz WASM artifact.
   * Produced by: wasm-pack build --features doc-viz --target web
   */
  wasmUrl?: string;
  /**
   * Polling interval in ms. Default: 16 (one rAF cycle at 60fps).
   * Setting this higher reduces the viz overhead at the cost of temporal resolution.
   */
  pollIntervalMs?: number;
}

export default function NexusMemoryViz({
  wasmUrl = "/wasm/nexus_engine_doc_viz_bg.wasm",
  pollIntervalMs = 16,
}: Props) {
  const [bridgeState, setBridgeState] = useState<BridgeState>({ status: "idle" });
  const [viz, setViz] = useState<VizState>({
    sample: null, invariants: 0, sampleRate: 0, inconsistent: 0
  });
  const [hoveredRegion, setHoveredRegion] = useState<string | null>(null);

  const bridgeRef   = useRef<WasmMemoryBridge | null>(null);
  const rafRef      = useRef<number>(0);
  const sampleTimes = useRef<number[]>([]);

  // ── Feature detection ────────────────────────────────────────────────────
  // SharedArrayBuffer availability requires COOP/COEP headers.
  // We check for it before attempting WASM instantiation — if it's absent,
  // the error message tells the developer exactly what to fix (header config),
  // not just that the module failed to load.
  const checkPrerequisites = useCallback((): string | null => {
    if (typeof SharedArrayBuffer === "undefined") {
      return "SharedArrayBuffer is unavailable. The server must respond with:\n" +
             "  Cross-Origin-Opener-Policy: same-origin\n" +
             "  Cross-Origin-Embedder-Policy: require-corp\n" +
             "See bun-server.ts for the correct header configuration.";
    }
    if (typeof WebAssembly === "undefined") {
      return "WebAssembly is not supported in this environment.";
    }
    return null;
  }, []);

  // ── WASM initialization ──────────────────────────────────────────────────
  useEffect(() => {
    const prereqError = checkPrerequisites();
    if (prereqError) {
      setBridgeState({ status: "unavailable", reason: prereqError });
      return;
    }

    setBridgeState({ status: "loading" });

    WasmMemoryBridge.fromUrl(wasmUrl)
      .then(bridge => {
        bridgeRef.current = bridge;
        setBridgeState({ status: "ready", bridge });
      })
      .catch(err => {
        const message = err instanceof Error ? err.message : String(err);
        setBridgeState({ status: "error", message });
      });

    return () => {
      cancelAnimationFrame(rafRef.current);
      bridgeRef.current = null;
    };
  }, [wasmUrl, checkPrerequisites]);

  // ── Polling loop ─────────────────────────────────────────────────────────
  // Runs at rAF cadence (nominally 60fps) to poll the WASM memory state.
  //
  // This loop is the documentation layer's only observable side effect on
  // the production Atomics protocol: it competes with the main thread's
  // Atomics.load calls in the frame consumer. The competition is a few
  // dozen nanoseconds of cache-line contention on the control block —
  // not measurable in practice, but worth noting for completeness.
  useEffect(() => {
    if (bridgeState.status !== "ready") return;

    let inconsistentCount = 0;

    const poll = () => {
      const bridge = bridgeRef.current;
      if (!bridge) return;

      const now = performance.now();
      sampleTimes.current.push(now);
      // Keep a 60-sample window for rate calculation
      if (sampleTimes.current.length > 60) sampleTimes.current.shift();

      const sample = bridge.sampleState();
      const invariants = bridge.checkInvariants();

      if (!sample.consistent) inconsistentCount++;

      // Compute sample rate from the sliding window
      const times = sampleTimes.current;
      const sampleRate = times.length > 1
        ? (times.length - 1) / ((times[times.length - 1] - times[0]) / 1000)
        : 0;

      setViz({ sample, invariants, sampleRate, inconsistent: inconsistentCount });

      rafRef.current = requestAnimationFrame(poll);
    };

    rafRef.current = requestAnimationFrame(poll);
    return () => cancelAnimationFrame(rafRef.current);
  }, [bridgeState.status]);

  // ── Render helpers ────────────────────────────────────────────────────────
  const { sample, invariants, sampleRate, inconsistent } = viz;

  if (bridgeState.status === "idle" || bridgeState.status === "loading") {
    return (
      <div style={styles.panel}>
        <div style={styles.statusLine}>
          <span style={{ ...styles.dot, background: "#F59E0B" }} />
          <span style={{ color: "#94A3B8", fontFamily: "monospace", fontSize: 12 }}>
            {bridgeState.status === "loading"
              ? "Instantiating nexus-engine (doc-viz build)…"
              : "Waiting…"}
          </span>
        </div>
      </div>
    );
  }

  if (bridgeState.status === "unavailable" || bridgeState.status === "error") {
    const isUnavail = bridgeState.status === "unavailable";
    return (
      <div style={{ ...styles.panel, borderColor: "#F87171" }}>
        <div style={{ color: "#F87171", fontFamily: "monospace", fontSize: 11 }}>
          {isUnavail ? "PREREQUISITE MISSING" : "WASM LOAD ERROR"}
        </div>
        <pre style={{ color: "#94A3B8", fontSize: 11, marginTop: 8, whiteSpace: "pre-wrap" }}>
          {isUnavail
            ? (bridgeState as { status: "unavailable"; reason: string }).reason
            : (bridgeState as { status: "error"; message: string }).message}
        </pre>
      </div>
    );
  }

  // ── Layout: live memory arena map ─────────────────────────────────────────
  const layout = sample?.layout ?? bridgeState.bridge.currentLayout;
  const totalBytes = layout.totalBytes || 1;

  return (
    <div style={styles.root}>

      {/* Header */}
      <div style={styles.header}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ ...styles.dot, background: "#4ADE80", boxShadow: "0 0 6px #4ADE8066" }} />
          <span style={styles.title}>LIVE MEMORY ARENA MAP</span>
        </div>
        <div style={styles.metaRow}>
          <span style={styles.meta}>{(totalBytes / 1024 / 1024).toFixed(1)} MiB SAB</span>
          <span style={styles.meta}>{sampleRate.toFixed(0)} samples/s</span>
          <span style={{ ...styles.meta, color: invariants !== 0 ? "#F87171" : "#4ADE80" }}>
            invariants: {invariants === 0 ? "PASS" : `FAIL 0b${invariants.toString(2).padStart(4,"0")}`}
          </span>
          {inconsistent > 0 && (
            <span style={{ ...styles.meta, color: "#FBBF24" }}>
              {inconsistent} torn reads (seqlock retried)
            </span>
          )}
        </div>
      </div>

      {/* Memory bar */}
      <div style={styles.memBar}>
        {LAYOUT_REGIONS.map(r => {
          const offset = r.getOffset(layout);
          const bytes  = r.getBytes(layout);
          const width  = (bytes / totalBytes) * 100;
          const isViolated = invariants !== 0 && (r.id === "fb_a" || r.id === "fb_b");
          return (
            <div
              key={r.id}
              onMouseEnter={() => setHoveredRegion(r.id)}
              onMouseLeave={() => setHoveredRegion(null)}
              title={`${r.label}: 0x${offset.toString(16).toUpperCase()} (${(bytes/1024).toFixed(0)} KiB)`}
              style={{
                ...styles.memRegion,
                width:      `${Math.max(width, 0.4)}%`,
                background: isViolated ? "#F87171" : r.color,
                opacity:    hoveredRegion === r.id ? 1 : 0.7,
                outline:    hoveredRegion === r.id ? `1px solid ${r.color}` : "none",
                animation:  isViolated ? "pulse 0.3s alternate infinite" : "none",
              }}
            />
          );
        })}
      </div>

      {/* Offset labels */}
      <div style={styles.offsetRow}>
        {LAYOUT_REGIONS.map(r => (
          <div
            key={r.id}
            style={{
              width: `${Math.max((r.getBytes(layout) / totalBytes) * 100, 0.4)}%`,
              color: r.color,
              fontSize: 9,
              fontFamily: "monospace",
              overflow: "hidden",
              paddingTop: 2,
            }}
          >
            0x{r.getOffset(layout).toString(16).toUpperCase()}
          </div>
        ))}
      </div>

      {/* Hovered region detail */}
      {hoveredRegion && (() => {
        const r = LAYOUT_REGIONS.find(x => x.id === hoveredRegion)!;
        const offset = r.getOffset(layout);
        const bytes  = r.getBytes(layout);
        return (
          <div style={{ ...styles.tooltip, borderColor: r.color + "60" }}>
            <span style={{ color: r.color, fontWeight: 700 }}>{r.label}</span>
            <span style={styles.meta}>
              {" "}0x{offset.toString(16).toUpperCase()} → 0x{(offset + bytes).toString(16).toUpperCase()}
              {" "}({(bytes / 1024).toFixed(1)} KiB)
            </span>
            <div style={{ marginTop: 4, color: "#64748B", fontSize: 11 }}>{r.desc}</div>
          </div>
        );
      })()}

      {/* Thread state panel */}
      {sample && (
        <div style={styles.stateRow}>
          <ThreadLane
            label="MAIN THREAD"
            state={deriveMainState(sample)}
            color={deriveMainColor(sample)}
            detail={deriveMainDetail(sample)}
          />
          <div style={styles.bridge}>
            <span style={{ fontSize: 9, color: "#475569" }}>SAB</span>
            <div style={styles.bridgeLine} />
            <span style={{
              ...styles.swapBadge,
              background: sample.consistent ? "#F59E0B18" : "#F8717118",
              borderColor: sample.consistent ? "#F59E0B" : "#F87171",
              color: sample.consistent ? "#F59E0B" : "#F87171",
            }}>
              buf[{sample.coldBuffer}]
            </span>
            <div style={styles.bridgeLine} />
            <span style={{ fontSize: 9, color: "#475569" }}>Rel/Acq</span>
          </div>
          <ThreadLane
            label="RUST WORKER"
            state={deriveWorkerState(sample)}
            color={deriveWorkerColor(sample)}
            detail={deriveWorkerDetail(sample)}
          />
        </div>
      )}

      {/* Consistency note */}
      <div style={styles.note}>
        Live reads via seqlock protocol — CTRL_WRITE_IDX pre/post validated.
        {!sample?.consistent && (
          <span style={{ color: "#FBBF24" }}> Last sample torn — retry budget exhausted.</span>
        )}
      </div>

      <style>{`
        @keyframes pulse { from { opacity: 0.5 } to { opacity: 1 } }
      `}</style>
    </div>
  );
}

// ── Sub-components ───────────────────────────────────────────────────────────

function ThreadLane({ label, state, color, detail }: {
  label: string; state: string; color: string; detail: string;
}) {
  return (
    <div style={styles.lane}>
      <div style={{ fontSize: 9, color: "#64748B", marginBottom: 8, letterSpacing: "0.1em" }}>
        {label}
      </div>
      <div style={{ ...styles.stateBadge, background: color + "18", borderColor: color, color }}>
        {state}
      </div>
      <div style={{ fontSize: 10, color: "#475569", marginTop: 8, lineHeight: 1.5 }}>
        {detail}
      </div>
    </div>
  );
}

// ── State derivation from MemorySample ───────────────────────────────────────
// These functions map control block values to human-readable thread state labels.
// They encode the exact semantics of the Mesa-condition-variable protocol:
// the main thread is suspended when it last consumed the same buffer that is
// currently marked ready (i.e., it has nothing new to consume).

function deriveMainState(s: MemorySample): string {
  if (s.state.inputRingDepth > 16) return "BLOCKED_GC";
  if (s.state.lastConsumedBuffer === s.state.readyBuffer) return "SUSPENDED_WAIT_ASYNC";
  return "RAF_EXECUTING";
}

function deriveMainColor(s: MemorySample): string {
  const state = deriveMainState(s);
  return state === "SUSPENDED_WAIT_ASYNC" ? "#818CF8"
       : state === "RAF_EXECUTING"        ? "#4ADE80"
       : "#F87171";
}

function deriveMainDetail(s: MemorySample): string {
  const state = deriveMainState(s);
  if (state === "SUSPENDED_WAIT_ASYNC") {
    return `waitAsync(ctrl, READY_IDX, ${s.state.lastConsumedBuffer})\nMicrotask queue suspended — zero CPU cost`;
  }
  if (state === "RAF_EXECUTING") {
    return `rAF: putImageData(buf[${s.state.readyBuffer}]) → OffscreenCanvas`;
  }
  return `GC pause — input ring depth: ${s.state.inputRingDepth}`;
}

function deriveWorkerState(s: MemorySample): string {
  // Worker writes to the buffer that is NOT currently marked ready.
  // If write === ready, it just finished a frame (notifying or spin-waiting).
  if (s.state.workerWriteBuffer !== s.state.readyBuffer) return "WRITING_FRAME";
  if (s.state.lastConsumedBuffer !== s.state.readyBuffer) return "SPIN_LOOP";
  return "NOTIFYING";
}

function deriveWorkerColor(s: MemorySample): string {
  const state = deriveWorkerState(s);
  return state === "WRITING_FRAME" ? "#4ADE80"
       : state === "SPIN_LOOP"     ? "#FBBF24"
       : "#F59E0B";
}

function deriveWorkerDetail(s: MemorySample): string {
  const state = deriveWorkerState(s);
  if (state === "WRITING_FRAME") {
    return `DOD rasterize_scene() → buf[${s.state.workerWriteBuffer}]\nSoA f32 arrays, AVX2 path`;
  }
  if (state === "NOTIFYING") {
    return `ctrl[READY_IDX].store(${s.state.readyBuffer}, Release)\natomic_notify → wakes main thread`;
  }
  return `ctrl[CONSUME_IDX].load(Acquire) waiting for ${s.state.readyBuffer}\ncore::hint::spin_loop()`;
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = {
  root: {
    background: "#060810",
    border: "1px solid #1E293B",
    borderTop: "2px solid #F59E0B",
    borderRadius: 6,
    padding: 20,
    fontFamily: "'IBM Plex Mono', 'Courier New', monospace",
    color: "#E2E8F0",
  } as React.CSSProperties,

  panel: {
    background: "#060810",
    border: "1px solid #1E293B",
    borderRadius: 6,
    padding: 16,
  } as React.CSSProperties,

  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  } as React.CSSProperties,

  statusLine: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  } as React.CSSProperties,

  dot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
    display: "inline-block",
  } as React.CSSProperties,

  title: {
    fontSize: 11,
    color: "#F59E0B",
    fontWeight: 700,
    letterSpacing: "0.1em",
  } as React.CSSProperties,

  metaRow: {
    display: "flex",
    gap: 16,
    alignItems: "center",
  } as React.CSSProperties,

  meta: {
    fontSize: 10,
    color: "#475569",
    fontFamily: "monospace",
  } as React.CSSProperties,

  memBar: {
    display: "flex",
    gap: 2,
    height: 28,
    background: "#0D1117",
    borderRadius: 3,
    overflow: "hidden",
  } as React.CSSProperties,

  memRegion: {
    height: "100%",
    cursor: "pointer",
    transition: "opacity 0.1s, background 0.2s",
    minWidth: 3,
  } as React.CSSProperties,

  offsetRow: {
    display: "flex",
    gap: 2,
    marginTop: 3,
  } as React.CSSProperties,

  tooltip: {
    marginTop: 10,
    padding: "8px 12px",
    background: "#0D1117",
    border: "1px solid",
    borderRadius: 4,
    fontSize: 11,
  } as React.CSSProperties,

  stateRow: {
    display: "flex",
    gap: 12,
    marginTop: 20,
  } as React.CSSProperties,

  lane: {
    flex: 1,
    border: "1px solid #1E293B",
    borderRadius: 5,
    padding: 12,
  } as React.CSSProperties,

  stateBadge: {
    padding: "8px 12px",
    borderRadius: 4,
    border: "1px solid",
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: "0.05em",
    minHeight: 36,
    display: "flex",
    alignItems: "center",
  } as React.CSSProperties,

  bridge: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    minWidth: 64,
  } as React.CSSProperties,

  bridgeLine: {
    width: 2,
    height: 24,
    background: "linear-gradient(to bottom, #1E293B, #334155)",
  } as React.CSSProperties,

  swapBadge: {
    padding: "3px 8px",
    borderRadius: 3,
    border: "1px solid",
    fontSize: 10,
    fontWeight: 700,
    textAlign: "center" as const,
    fontFamily: "monospace",
  } as React.CSSProperties,

  note: {
    marginTop: 14,
    fontSize: 10,
    color: "#334155",
    fontFamily: "monospace",
  } as React.CSSProperties,
} as const;
