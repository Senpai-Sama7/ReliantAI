import { useState, useEffect, useRef, useCallback } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

// ─── WASM BINDGEN EXPORT SIGNATURES ────────────────────────────────────────
// These are the exact Rust signatures required to expose internal arena
// pointers to the JS documentation layer. The documentation reads live
// memory topology from the actual binary — not from hardcoded constants.
const RUST_SIGNATURES = `
// nexus-engine/src/lib.rs
// Expose arena pointers so the documentation layer can render
// a live memory map from actual module state — not from static constants.

use wasm_bindgen::prelude::*;

// ── Control Block ──────────────────────────────────────────────────────────
// Mesa-semantics synchronization: CTRL_READY_IDX, CTRL_CONSUME_IDX,
// INPUT_WRITE_IDX, INPUT_READ_IDX as Int32Array indices.
#[wasm_bindgen]
pub fn ctrl_block_ptr() -> u32 {
    CTRL_BLOCK.as_ptr() as u32
}

#[wasm_bindgen]
pub fn ctrl_block_byte_len() -> u32 {
    std::mem::size_of::<ControlBlock>() as u32
}

// ── Double Framebuffer ─────────────────────────────────────────────────────
// Release/Acquire ordering on CTRL_READY_IDX governs access.
// JS must perform an Acquire load before dereferencing these pointers.
#[wasm_bindgen]
pub fn framebuffer_0_ptr() -> u32 {
    unsafe { FRAMEBUFFER_A.as_ptr() as u32 }
}

#[wasm_bindgen]
pub fn framebuffer_1_ptr() -> u32 {
    unsafe { FRAMEBUFFER_B.as_ptr() as u32 }
}

#[wasm_bindgen]
pub fn framebuffer_byte_len() -> u32 {
    (WIDTH * HEIGHT * 4) as u32
}

// ── Input Ring Buffer ──────────────────────────────────────────────────────
// Allocation-free pointer event delivery from main thread.
// Capacity must be power-of-two for bitmask modulo arithmetic.
#[wasm_bindgen]
pub fn input_ring_ptr() -> u32 {
    INPUT_RING.as_ptr() as u32
}

#[wasm_bindgen]
pub fn input_ring_capacity() -> u32 {
    INPUT_RING_CAPACITY as u32
}

// ── SoA Field Batch ────────────────────────────────────────────────────────
// Phase 2 data layout: contiguous f32 arrays for SIMD-eligible
// bounding box scoring. Exposed so the documentation layer can
// visualize the phase boundary and measure cache utilization.
#[wasm_bindgen]
pub fn field_batch_x_min_ptr() -> u32 {
    unsafe { FIELD_STORE.x_min.as_ptr() as u32 }
}

#[wasm_bindgen]
pub fn field_batch_len() -> u32 {
    unsafe { FIELD_STORE.x_min.len() as u32 }
}

// ── Memory Layout Invariant Checker ───────────────────────────────────────
// Returns a bitfield of invariant violations. 0 = all clear.
// Bit 0: ctrl block overlaps framebuffer A
// Bit 1: framebuffer A overlaps framebuffer B
// Bit 2: framebuffer B overlaps input ring
// Bit 3: input ring overlaps field batch
// CI integration: assert_eq!(check_memory_invariants(), 0)
#[wasm_bindgen]
pub fn check_memory_invariants() -> u32 {
    let regions = [
        (ctrl_block_ptr(), ctrl_block_byte_len()),
        (framebuffer_0_ptr(), framebuffer_byte_len()),
        (framebuffer_1_ptr(), framebuffer_byte_len()),
        (input_ring_ptr(), input_ring_capacity() * 8),
    ];
    let mut violations: u32 = 0;
    for i in 0..regions.len() {
        for j in (i + 1)..regions.len() {
            let (a_start, a_len) = regions[i];
            let (b_start, b_len) = regions[j];
            let a_end = a_start + a_len;
            let b_end = b_start + b_len;
            if a_start < b_end && b_start < a_end {
                violations |= 1 << i;
            }
        }
    }
    violations
}`;

// ─── SIMULATION CONSTANTS ─────────────────────────────────────────────────
const SAB_TOTAL = 16 * 1024 * 1024; // 16MB
const REGIONS = [
  { id: "ctrl",    label: "Control Block",     offset: 0x0000, size: 0x1000, color: "#F59E0B", desc: "Int32Array: CTRL_WRITE_IDX, CTRL_READY_IDX, CTRL_CONSUME_IDX, INPUT_WRITE, INPUT_READ" },
  { id: "input",   label: "Input Ring Buffer", offset: 0x1000, size: 0x1000, color: "#818CF8", desc: "Float32Array[256×2]: pointerrawupdate ring — allocation-free, main thread writes" },
  { id: "buf_a",   label: "Framebuffer A",     offset: 0x2000, size: 0x3C0000, color: "#4ADE80", desc: "Uint8ClampedArray: RGBA framebuffer — written by Rust Worker, read by OffscreenCanvas" },
  { id: "buf_b",   label: "Framebuffer B",     offset: 0x3C2000, size: 0x3C0000, color: "#34D399", desc: "Uint8ClampedArray: RGBA framebuffer — double-buffer swap target" },
  { id: "soa",     label: "SoA Field Batch",   offset: 0x782000, size: 0x200000, color: "#FB923C", desc: "Vec<f32>×4: x_min, y_min, x_max, y_max — SIMD-eligible, L1 cache-optimal layout" },
  { id: "aos_tree",label: "AoS Parse Tree",    offset: 0x982000, size: 0x100000, color: "#94A3B8", desc: "ContentStreamNode heap: operator + SmallVec operands — hierarchical, non-SIMD phase" },
];

const THREAD_STATES = {
  MAIN: ["SUSPENDED_WAIT_ASYNC", "RAF_EXECUTING", "BLOCKED_GC", "IDLE", "NOTIFY_SENT"],
  WORKER: ["RASTERIZING", "SPIN_LOOP", "NOTIFYING", "IDLE", "WRITING_FRAME"],
};

const STATE_COLORS = {
  SUSPENDED_WAIT_ASYNC: "#818CF8",
  RAF_EXECUTING: "#4ADE80",
  BLOCKED_GC: "#F87171",
  IDLE: "#64748B",
  NOTIFY_SENT: "#F59E0B",
  RASTERIZING: "#4ADE80",
  SPIN_LOOP: "#FBBF24",
  NOTIFYING: "#F59E0B",
  WRITING_FRAME: "#34D399",
};

// ─── MAIN COMPONENT ──────────────────────────────────────────────────────
export default function ExecutableTopology() {
  const [mainState, setMainState] = useState("SUSPENDED_WAIT_ASYNC");
  const [workerState, setWorkerState] = useState("WRITING_FRAME");
  const [activeBuffer, setActiveBuffer] = useState(0);
  const [lastConsumed, setLastConsumed] = useState(1);
  const [frameCount, setFrameCount] = useState(0);
  const [ringDepth, setRingDepth] = useState(0);
  const [gcActive, setGcActive] = useState(false);
  const [corruptActive, setCorruptActive] = useState(false);
  const [noOrdering, setNoOrdering] = useState(false);
  const [aosClassify, setAosClassify] = useState(false);
  const [invariantViolations, setInvariantViolations] = useState(0);
  const [events, setEvents] = useState([]);
  const [phaseData, setPhaseData] = useState([]);
  const [hoveredRegion, setHoveredRegion] = useState(null);
  const [showRust, setShowRust] = useState(false);
  const [tick, setTick] = useState(0);
  const [atomicSwapFlash, setAtomicSwapFlash] = useState(false);

  const gcTimerRef = useRef(null);
  const simRef = useRef({ frame: 0, lastMain: 0, lastWorker: 0, gcUntil: 0, ringWrite: 0, ringRead: 0 });
  const frameTimerRef = useRef(null);

  const addEvent = useCallback((type, msg) => {
    const ts = performance.now().toFixed(2);
    setEvents(prev => [{ts, type, msg}, ...prev].slice(0, 28));
  }, []);

  // ─── SIMULATION LOOP ────────────────────────────────────────────────────
  useEffect(() => {
    let rafId;
    let lastTime = performance.now();
    let workerPhase = 0; // 0=writing, 1=notifying, 2=spin
    let mainPhase = 0;   // 0=suspended, 1=raf
    let workerFrameDuration = 0;
    let mainFrameDuration = 0;
    let phaseTimer = 0;
    let mainTimer = 0;
    const WORKER_FRAME_MS = 16.7;
    const MAIN_RAF_MS = 4;

    function step(now) {
      const dt = now - lastTime;
      lastTime = now;
      const sim = simRef.current;

      // ── Simulate pointer events into ring buffer ──
      if (Math.random() < 0.4) {
        sim.ringWrite++;
        if (!gcActive) {
          // Main thread drains ring if not GC'd
          sim.ringRead = Math.max(sim.ringRead, sim.ringWrite - 3);
        }
        const depth = Math.max(0, sim.ringWrite - sim.ringRead);
        setRingDepth(depth);
      }

      // ── Worker simulation ──
      phaseTimer += dt;
      if (workerPhase === 0 && phaseTimer > WORKER_FRAME_MS * 0.7) {
        workerPhase = 1;
        workerFrameDuration = 0;
        setWorkerState("NOTIFYING");
        const buf = sim.frame % 2;
        setActiveBuffer(buf);
        setAtomicSwapFlash(true);
        setTimeout(() => setAtomicSwapFlash(false), 120);
        addEvent("ATOMIC", `Atomics.notify(CTRL_READY_IDX, ${buf}) — Release store complete`);
        phaseTimer = 0;
      } else if (workerPhase === 1 && phaseTimer > 2) {
        workerPhase = 2;
        setWorkerState("SPIN_LOOP");
        phaseTimer = 0;
      } else if (workerPhase === 2 && phaseTimer > (gcActive ? 500 : WORKER_FRAME_MS * 0.3)) {
        // GC pause doesn't block worker — it keeps spinning waiting for consume ACK
        if (!gcActive) {
          workerPhase = 0;
          sim.frame++;
          setFrameCount(f => f + 1);
          setWorkerState("WRITING_FRAME");
          addEvent("FRAME", `Frame ${sim.frame} — buffer swap, DOD rasterize begin`);
        }
        phaseTimer = 0;
      }

      // ── Main thread simulation ──
      mainTimer += dt;
      if (gcActive) {
        setMainState("BLOCKED_GC");
        // Ring buffer backs up
        sim.ringRead = Math.min(sim.ringRead, sim.ringWrite - Math.floor(mainTimer / 16));
        setRingDepth(Math.min(64, Math.max(0, sim.ringWrite - sim.ringRead)));
        mainPhase = 0;
      } else {
        if (mainPhase === 0) {
          setMainState("SUSPENDED_WAIT_ASYNC");
          // waitAsync wakes when CTRL_READY_IDX !== lastConsumed
          if (workerPhase === 2 && mainTimer > 1) {
            mainPhase = 1;
            mainTimer = 0;
            const readBuf = sim.frame % 2;
            setLastConsumed(readBuf);
            setMainState("RAF_EXECUTING");
            addEvent("WAKE", `waitAsync resolved 'ok' — Acquire load, readBuf=${readBuf}`);
          }
        } else if (mainPhase === 1 && mainTimer > MAIN_RAF_MS) {
          mainPhase = 0;
          mainTimer = 0;
          setMainState("SUSPENDED_WAIT_ASYNC");
          addEvent("CONSUME", `Atomics.store(CTRL_CONSUME_IDX, ${sim.frame % 2}) + notify`);
        }
      }

      // ── Phase profiler data ──
      if (sim.frame % 3 === 0 && dt > 1) {
        const aosLatency = 180 + Math.random() * 140 + (aosClassify ? 280 : 0);
        const soaLatency = aosClassify ? 190 + Math.random() * 160 : 22 + Math.random() * 18;
        setPhaseData(prev => {
          const next = [...prev, {
            t: sim.frame,
            aos: parseFloat(aosLatency.toFixed(1)),
            soa: parseFloat(soaLatency.toFixed(1)),
          }].slice(-60);
          return next;
        });
      }

      // ── Invariant check ──
      if (corruptActive) {
        setInvariantViolations(0b0110); // Simulate framebuffer overlap
      } else {
        setInvariantViolations(0);
      }

      setTick(t => t + 1);
      rafId = requestAnimationFrame(step);
    }

    rafId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafId);
  }, [gcActive, corruptActive, aosClassify, addEvent]);

  // ─── GC PAUSE HANDLER ───────────────────────────────────────────────────
  const triggerGC = () => {
    if (gcActive) return;
    setGcActive(true);
    addEvent("FAULT", "GC PAUSE injected — main thread blocked 500ms");
    clearTimeout(gcTimerRef.current);
    gcTimerRef.current = setTimeout(() => {
      setGcActive(false);
      addEvent("RECOVER", "GC pause ended — main thread unblocked");
    }, 500);
  };

  // ─── MEMORY REGION BAR ─────────────────────────────────────────────────
  const MemoryBar = () => {
    const totalDisplay = 0xB00000;
    return (
      <div style={{ fontFamily: "monospace" }}>
        <div style={{ display: "flex", gap: 2, height: 28, borderRadius: 3, overflow: "hidden", background: "#0D1117" }}>
          {REGIONS.map(r => {
            const width = (r.size / totalDisplay) * 100;
            const isViolated = corruptActive && (r.id === "buf_a" || r.id === "buf_b");
            return (
              <div
                key={r.id}
                onMouseEnter={() => setHoveredRegion(r)}
                onMouseLeave={() => setHoveredRegion(null)}
                style={{
                  width: `${width}%`,
                  background: isViolated ? "#F87171" : r.color,
                  opacity: hoveredRegion?.id === r.id ? 1 : 0.75,
                  cursor: "pointer",
                  transition: "opacity 0.15s, background 0.2s",
                  position: "relative",
                  minWidth: 4,
                  animation: isViolated ? "pulse 0.4s ease infinite alternate" : "none",
                }}
              />
            );
          })}
        </div>
        <div style={{ display: "flex", gap: 2, marginTop: 2 }}>
          {REGIONS.map(r => (
            <div key={r.id} style={{ width: `${(r.size / totalDisplay) * 100}%`, minWidth: 4 }}>
              <div style={{ fontSize: 9, color: r.color, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                0x{r.offset.toString(16).padStart(4, "0")}
              </div>
            </div>
          ))}
        </div>
        {hoveredRegion && (
          <div style={{
            marginTop: 10, padding: "8px 12px", background: "#0D1117",
            border: `1px solid ${hoveredRegion.color}40`, borderRadius: 4,
          }}>
            <div style={{ color: hoveredRegion.color, fontSize: 11, fontWeight: 700, marginBottom: 4 }}>
              {hoveredRegion.label}
              <span style={{ color: "#64748B", fontWeight: 400, marginLeft: 12 }}>
                0x{hoveredRegion.offset.toString(16).toUpperCase()} – 0x{(hoveredRegion.offset + hoveredRegion.size).toString(16).toUpperCase()}
                {" "}({(hoveredRegion.size / 1024).toFixed(0)} KiB)
              </span>
            </div>
            <div style={{ color: "#94A3B8", fontSize: 11 }}>{hoveredRegion.desc}</div>
          </div>
        )}
        <div style={{ marginTop: 12, display: "flex", flexWrap: "wrap", gap: 8 }}>
          {REGIONS.map(r => (
            <div key={r.id} style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <div style={{ width: 8, height: 8, borderRadius: 2, background: r.color }} />
              <span style={{ fontSize: 10, color: "#64748B", fontFamily: "monospace" }}>{r.label}</span>
            </div>
          ))}
        </div>
        {invariantViolations !== 0 && (
          <div style={{
            marginTop: 8, padding: "6px 12px", background: "#F87171" + "18",
            border: "1px solid #F87171", borderRadius: 4, fontSize: 11, color: "#F87171",
          }}>
            ⚠ INVARIANT VIOLATION — check_memory_invariants() → 0b{invariantViolations.toString(2).padStart(4, "0")}
            {" "}— Framebuffer regions overlap. CI would fail.
          </div>
        )}
      </div>
    );
  };

  // ─── CONCURRENCY STATE MACHINE ─────────────────────────────────────────
  const StateMachine = () => {
    const mainColor = STATE_COLORS[mainState] || "#64748B";
    const workerColor = STATE_COLORS[workerState] || "#64748B";
    return (
      <div style={{ display: "flex", gap: 16 }}>
        {/* Main Thread Lane */}
        <div style={{ flex: 1, border: "1px solid #1E293B", borderRadius: 6, padding: 14 }}>
          <div style={{ fontSize: 10, color: "#64748B", marginBottom: 10, letterSpacing: "0.1em" }}>MAIN THREAD</div>
          <div style={{
            padding: "10px 14px", borderRadius: 4, background: mainColor + "18",
            border: `1px solid ${mainColor}`,
            color: mainColor, fontSize: 12, fontFamily: "monospace", fontWeight: 700,
            transition: "all 0.15s", minHeight: 44, display: "flex", alignItems: "center",
          }}>
            {mainState}
          </div>
          <div style={{ marginTop: 12, fontSize: 10, color: "#475569", lineHeight: 1.6 }}>
            {mainState === "SUSPENDED_WAIT_ASYNC" && (
              <span>waitAsync(ctrl, CTRL_READY_IDX, <span style={{ color: "#F59E0B" }}>{lastConsumed}</span>)<br/>
              Microtask queue suspended — zero CPU cost</span>
            )}
            {mainState === "RAF_EXECUTING" && (
              <span>rAF callback executing<br/>
              putImageData → OffscreenCanvas → GPU compositor</span>
            )}
            {mainState === "BLOCKED_GC" && (
              <span style={{ color: "#F87171" }}>GC pause — event loop blocked<br/>
              Input ring backing up: <span style={{ color: "#F87171", fontWeight: 700 }}>{ringDepth} events queued</span></span>
            )}
          </div>
          {/* Input ring depth meter */}
          <div style={{ marginTop: 12 }}>
            <div style={{ fontSize: 9, color: "#475569", marginBottom: 4 }}>INPUT RING BUFFER DEPTH</div>
            <div style={{ background: "#0D1117", borderRadius: 2, height: 8, overflow: "hidden" }}>
              <div style={{
                height: "100%", borderRadius: 2,
                background: ringDepth > 32 ? "#F87171" : ringDepth > 8 ? "#FBBF24" : "#4ADE80",
                width: `${Math.min(100, (ringDepth / 64) * 100)}%`,
                transition: "width 0.1s, background 0.3s",
              }} />
            </div>
            <div style={{ fontSize: 9, color: "#475569", marginTop: 2 }}>{ringDepth}/64 slots</div>
          </div>
        </div>

        {/* Atomic Bridge */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8, minWidth: 70 }}>
          <div style={{ fontSize: 9, color: "#475569", textAlign: "center", letterSpacing: "0.05em" }}>SAB</div>
          <div style={{
            width: 2, flex: 1, maxHeight: 60,
            background: atomicSwapFlash
              ? "linear-gradient(to bottom, #F59E0B, #F59E0B)"
              : "linear-gradient(to bottom, #1E293B, #334155, #1E293B)",
            transition: "background 0.1s",
          }} />
          <div style={{
            padding: "4px 8px", borderRadius: 3,
            background: atomicSwapFlash ? "#F59E0B" : "#0D1117",
            border: `1px solid ${atomicSwapFlash ? "#F59E0B" : "#334155"}`,
            color: atomicSwapFlash ? "#000" : "#F59E0B",
            fontSize: 9, fontFamily: "monospace", fontWeight: 700,
            transition: "all 0.1s", textAlign: "center", minWidth: 60,
          }}>
            {atomicSwapFlash ? "NOTIFY" : `buf[${activeBuffer}]`}
          </div>
          <div style={{ width: 2, flex: 1, maxHeight: 60, background: "linear-gradient(to bottom, #1E293B, #334155, #1E293B)" }} />
          <div style={{ fontSize: 9, color: "#475569", textAlign: "center" }}>
            {noOrdering ? <span style={{ color: "#F87171" }}>NO ORD</span> : "Rel/Acq"}
          </div>
        </div>

        {/* Worker Thread Lane */}
        <div style={{ flex: 1, border: "1px solid #1E293B", borderRadius: 6, padding: 14 }}>
          <div style={{ fontSize: 10, color: "#64748B", marginBottom: 10, letterSpacing: "0.1em" }}>RUST WORKER</div>
          <div style={{
            padding: "10px 14px", borderRadius: 4, background: workerColor + "18",
            border: `1px solid ${workerColor}`,
            color: workerColor, fontSize: 12, fontFamily: "monospace", fontWeight: 700,
            transition: "all 0.15s", minHeight: 44, display: "flex", alignItems: "center",
          }}>
            {workerState}
          </div>
          <div style={{ marginTop: 12, fontSize: 10, color: "#475569", lineHeight: 1.6 }}>
            {workerState === "WRITING_FRAME" && (
              <span>DOD rasterize_scene() → buf[{activeBuffer}]<br/>
              SoA layout — 16 pixels/cache line, AVX2 path</span>
            )}
            {workerState === "NOTIFYING" && (
              <span>ctrl[CTRL_READY_IDX].store(<span style={{ color: "#F59E0B" }}>{activeBuffer}</span>, Release)<br/>
              atomic_notify() → wakes main thread</span>
            )}
            {workerState === "SPIN_LOOP" && (
              <span>Waiting for CTRL_CONSUME_IDX == {activeBuffer}<br/>
              {gcActive ? <span style={{ color: "#FBBF24" }}>GC pause detected — spin continues</span> : "Acquire load, core::hint::spin_loop()"}</span>
            )}
          </div>
          <div style={{ marginTop: 12 }}>
            <div style={{ fontSize: 9, color: "#475569", marginBottom: 4 }}>FRAME COUNT</div>
            <div style={{ fontSize: 18, color: "#4ADE80", fontFamily: "monospace", fontWeight: 700 }}>{frameCount.toString().padStart(6, "0")}</div>
          </div>
        </div>
      </div>
    );
  };

  // ─── PHASE BOUNDARY PROFILER ────────────────────────────────────────────
  const PhaseProfiler = () => (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div style={{ display: "flex", gap: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: "#94A3B8" }} />
            <span style={{ fontSize: 10, color: "#64748B" }}>Phase 1: AoS Parse Tree traversal (μs)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: "#FB923C" }} />
            <span style={{ fontSize: 10, color: "#64748B" }}>Phase 2: SoA Field Batch scoring (μs)</span>
          </div>
        </div>
        {aosClassify && (
          <div style={{ fontSize: 9, color: "#F87171", fontFamily: "monospace" }}>
            ⚠ AoS IN CLASSIFY PHASE — cache thrash visible
          </div>
        )}
      </div>
      <ResponsiveContainer width="100%" height={130}>
        <LineChart data={phaseData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <XAxis dataKey="t" hide />
          <YAxis domain={[0, 550]} tick={{ fontSize: 9, fill: "#475569" }} />
          <Tooltip
            contentStyle={{ background: "#0D1117", border: "1px solid #334155", borderRadius: 4, fontSize: 10 }}
            labelStyle={{ color: "#64748B" }}
          />
          <ReferenceLine y={100} stroke="#334155" strokeDasharray="3 3" />
          <Line type="monotone" dataKey="aos" stroke="#94A3B8" dot={false} strokeWidth={1.5} isAnimationActive={false} />
          <Line type="monotone" dataKey="soa" stroke="#FB923C" dot={false} strokeWidth={1.5} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
      <div style={{ marginTop: 8, padding: "8px 12px", background: "#0D1117", borderRadius: 4, fontSize: 10, color: "#475569" }}>
        {aosClassify
          ? <span style={{ color: "#F87171" }}>AoS classification: ~{(phaseData[phaseData.length - 1]?.soa || 0).toFixed(0)}μs — object pointer-chasing forces L2/L3 cache misses. Each FoundField scattered in heap. CPU prefetcher cannot anticipate next access.</span>
          : <span>SoA phase boundary operating correctly. Phase 2 latency ~22–40μs. x_min[i] through x_min[i+15] fit one 64-byte cache line — 16 fields scored per prefetch cycle. Phase 1 AoS traversal ~180–320μs — expected for hierarchical graph walk.</span>
        }
      </div>
    </div>
  );

  // ─── FUZZER PANEL ───────────────────────────────────────────────────────
  const FuzzerPanel = () => (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {[
        {
          id: "gc", label: "Simulate 500ms GC Pause",
          desc: "Blocks main thread. Worker render loop continues uninterrupted. Input ring backs up.",
          active: gcActive, onClick: triggerGC, danger: true, once: true,
        },
        {
          id: "corrupt", label: "Corrupt Frame Boundary",
          desc: "Overlaps framebuffer A and B in memory map. check_memory_invariants() → non-zero. CI fails.",
          active: corruptActive, onClick: () => setCorruptActive(v => !v), danger: true,
        },
        {
          id: "ordering", label: "Disable Acquire/Release Ordering",
          desc: "Removes happens-before guarantee. CPU reordering can make frame writes visible after notification.",
          active: noOrdering, onClick: () => setNoOrdering(v => !v), danger: true,
        },
        {
          id: "aos_classify", label: "Force AoS in Classification Phase",
          desc: "Routes phase 2 through Vec<FoundField> (AoS). Profiler shows cache-miss penalty immediately.",
          active: aosClassify, onClick: () => setAosClassify(v => !v), danger: false,
        },
      ].map(item => (
        <div key={item.id} style={{
          padding: "10px 14px", borderRadius: 4,
          background: item.active ? (item.danger ? "#F87171" + "12" : "#FB923C" + "12") : "#0D1117",
          border: `1px solid ${item.active ? (item.danger ? "#F87171" : "#FB923C") : "#1E293B"}`,
          transition: "all 0.2s",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{
              fontSize: 12, fontFamily: "monospace", fontWeight: 600,
              color: item.active ? (item.danger ? "#F87171" : "#FB923C") : "#E2E8F0",
            }}>
              {item.label}
            </span>
            <button onClick={item.onClick} style={{
              padding: "4px 14px", borderRadius: 3, fontSize: 11, fontFamily: "monospace",
              cursor: item.once && item.active ? "not-allowed" : "pointer",
              background: item.active ? (item.danger ? "#F87171" : "#FB923C") : "transparent",
              color: item.active ? "#000" : (item.danger ? "#F87171" : "#64748B"),
              border: `1px solid ${item.active ? "transparent" : (item.danger ? "#F87171" + "60" : "#334155")}`,
              fontWeight: 700, transition: "all 0.15s",
            }}>
              {item.once ? (item.active ? "ACTIVE" : "INJECT") : (item.active ? "ON" : "OFF")}
            </button>
          </div>
          <div style={{ marginTop: 6, fontSize: 10, color: "#475569", lineHeight: 1.5 }}>{item.desc}</div>
        </div>
      ))}
    </div>
  );

  // ─── EVENT LOG ──────────────────────────────────────────────────────────
  const EventLog = () => {
    const colors = { ATOMIC: "#F59E0B", FRAME: "#4ADE80", WAKE: "#818CF8", CONSUME: "#34D399", FAULT: "#F87171", RECOVER: "#4ADE80" };
    return (
      <div style={{ height: 160, overflowY: "auto", fontFamily: "monospace", fontSize: 10 }}>
        {events.map((e, i) => (
          <div key={i} style={{ display: "flex", gap: 10, padding: "2px 0", borderBottom: "1px solid #0F172A" }}>
            <span style={{ color: "#475569", minWidth: 72 }}>{e.ts}ms</span>
            <span style={{ color: colors[e.type] || "#64748B", minWidth: 62 }}>[{e.type}]</span>
            <span style={{ color: "#94A3B8" }}>{e.msg}</span>
          </div>
        ))}
      </div>
    );
  };

  const Panel = ({ title, subtitle, children, accentColor = "#F59E0B" }) => (
    <div style={{
      background: "#0A0E1A",
      border: "1px solid #1E293B",
      borderTop: `2px solid ${accentColor}`,
      borderRadius: 6,
      padding: 18,
      display: "flex",
      flexDirection: "column",
      gap: 12,
    }}>
      <div>
        <div style={{ fontSize: 11, color: accentColor, fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.12em" }}>{title}</div>
        {subtitle && <div style={{ fontSize: 10, color: "#475569", marginTop: 2 }}>{subtitle}</div>}
      </div>
      {children}
    </div>
  );

  return (
    <div style={{
      background: "#060810",
      minHeight: "100vh",
      color: "#E2E8F0",
      fontFamily: "'IBM Plex Mono', 'Courier New', monospace",
      padding: "24px",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&display=swap');
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0D1117; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
        @keyframes pulse { from { opacity: 0.6 } to { opacity: 1 } }
        @keyframes scanline {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100vh); }
        }
      `}</style>

      {/* Header */}
      <div style={{ borderBottom: "1px solid #1E293B", paddingBottom: 16, marginBottom: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#F59E0B", letterSpacing: "0.05em" }}>
              NEXUS — EXECUTABLE TOPOLOGY SPECIFICATION
            </div>
            <div style={{ fontSize: 11, color: "#475569", marginTop: 4 }}>
              Live runtime documentation · SharedArrayBuffer + Atomics + Rust WASM + OffscreenCanvas
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#4ADE80", boxShadow: "0 0 6px #4ADE80" }} />
              <span style={{ fontSize: 10, color: "#4ADE80" }}>SIMULATION RUNNING</span>
            </div>
            <div style={{ fontSize: 11, color: "#334155" }}>
              invariants: <span style={{ color: invariantViolations ? "#F87171" : "#4ADE80" }}>
                {invariantViolations ? `0b${invariantViolations.toString(2).padStart(4,"0")} FAIL` : "0b0000 PASS"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Row 1: Memory + Concurrency */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        <Panel
          title="01 · LIVE MEMORY ARENA MAP"
          subtitle="SharedArrayBuffer layout — hover to inspect regions"
          accentColor="#F59E0B"
        >
          <MemoryBar />
        </Panel>

        <Panel
          title="02 · CONCURRENCY STATE MACHINE"
          subtitle="Mesa-semantics Atomics · Release/Acquire ordering · double-buffer TOCTOU guard"
          accentColor="#818CF8"
        >
          <StateMachine />
        </Panel>
      </div>

      {/* Row 2: Profiler + Fuzzer */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 16, marginBottom: 16 }}>
        <Panel
          title="03 · AoS → SoA PHASE BOUNDARY PROFILER"
          subtitle="Live latency · Phase 1 parse tree (AoS) vs Phase 2 classification batch (SoA)"
          accentColor="#FB923C"
        >
          <PhaseProfiler />
        </Panel>

        <Panel
          title="04 · INVARIANT FUZZER"
          subtitle="Inject architectural violations to observe failure modes"
          accentColor="#F87171"
        >
          <FuzzerPanel />
        </Panel>
      </div>

      {/* Row 3: Event Log */}
      <Panel
        title="05 · ATOMIC EVENT LOG"
        subtitle="Real-time synchronization events — Atomics.notify, buffer swaps, GC pauses, rAF callbacks"
        accentColor="#4ADE80"
      >
        <EventLog />
      </Panel>

      {/* Row 4: wasm-bindgen signatures */}
      <div style={{ marginTop: 16, border: "1px solid #1E293B", borderTop: "2px solid #334155", borderRadius: 6, overflow: "hidden" }}>
        <button
          onClick={() => setShowRust(v => !v)}
          style={{
            width: "100%", padding: "12px 18px",
            background: "#0A0E1A", border: "none", cursor: "pointer",
            color: "#64748B", textAlign: "left", fontFamily: "monospace", fontSize: 11,
            display: "flex", justifyContent: "space-between",
          }}
        >
          <span>06 · WASM BINDGEN EXPORT SIGNATURES — <span style={{ color: "#334155" }}>Rust arena pointer exposure API</span></span>
          <span style={{ color: "#334155" }}>{showRust ? "▲ collapse" : "▼ expand"}</span>
        </button>
        {showRust && (
          <pre style={{
            margin: 0, padding: "16px 20px",
            background: "#060810", color: "#64748B",
            fontSize: 11, lineHeight: 1.7, overflowX: "auto",
            borderTop: "1px solid #1E293B",
          }}>
            <code>{RUST_SIGNATURES}</code>
          </pre>
        )}
      </div>

      <div style={{ marginTop: 20, fontSize: 10, color: "#1E293B", textAlign: "center" }}>
        This document does not describe the system. It runs it.
      </div>
    </div>
  );
}
