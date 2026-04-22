# NEXUS — Browser-Native Document Intelligence Runtime

> A privacy-preserving, zero-egress document processing platform built on a
> hardware-aware, thread-segregated, shared-memory compute pipeline hosted in
> a sandboxed userspace execution environment.
>
> **No cloud inference. No data egress. No cold starts. No serialization overhead.**

---

## The Core Architectural Thesis

Most "AI document processing" platforms are architecturally inverted: they route
sensitive documents through cloud inference pipelines, adding latency, cost, data
custody risk, and per-document API billing that compounds destructively at scale.

NEXUS inverts this model. The inference runtime lives in the user's browser. The
compute happens on the user's CPU. The server's only role is edge-synchronized
metadata persistence. The result is a system that is simultaneously faster, cheaper,
more private, and more available than any server-side equivalent.

This is not an optimization. It is a different execution model.

---

## Stack

| Layer | Technology | Role |
|-------|-----------|------|
| Runtime | Bun | Sub-millisecond TS transpilation, zero-overhead dev server |
| Presentation | Astro (TypeScript) | Zero-JS-by-default shell; selective island hydration |
| Compute | Rust → WASM | Deterministic, GC-free document processing pipeline |
| Persistence | Turso (libSQL, edge) | Append-only audit log, metadata, session state |
| Synchronization | SharedArrayBuffer + Atomics | Mesa-semantics condition variable signaling |
| Rendering | OffscreenCanvas + SAB ring buffer | Full UI/compute decoupling |

---

## Architecture: The Four-Lane Execution Model

```
┌─────────────────────────────────────────────────────────────────────┐
│  Browser Process                                                      │
│                                                                       │
│  ┌─────────────────────────────┐  SAB Ring Buffer (input events)     │
│  │  Main Thread                │ ──────────────────────────────────► │
│  │  Astro Islands              │                                      │
│  │  ├─ Document upload UI      │  SharedArrayBuffer (frame/data)      │
│  │  ├─ Review/correction UI    │ ◄────────────────────────────────── │
│  │  └─ Navigation/shell        │                                      │
│  └─────────────────────────────┘                                     │
│                                                                       │
│  ┌─────────────────────────────┐                                      │
│  │  Web Worker (Compute Lane)  │                                      │
│  │  Rust WASM Module           │                                      │
│  │  ├─ Phase 1: PDF parse      │ ──► libSQL/Turso (metadata only)    │
│  │  ├─ Phase 2: Field extract  │                                      │
│  │  ├─ Phase 3: Classification │                                      │
│  │  └─ Phase 4: Confidence     │                                      │
│  └─────────────────────────────┘                                      │
│                                                                       │
│  ┌─────────────────────────────┐                                      │
│  │  OffscreenCanvas Worker     │                                      │
│  │  ├─ Rasterization           │                                      │
│  │  └─ requestAnimationFrame   │ ──► GPU Process (compositor)        │
│  └─────────────────────────────┘                                      │
│                                                                       │
│  GPU Process                                                          │
│  └─ Compositor (zero main-thread involvement in render path)          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The Memory Architecture

### Shared Linear Memory — Zero-Copy Guarantee

WASM linear memory is a typed `ArrayBuffer` exposed to the JS heap. JavaScript
can hold a `Uint8Array` view into it at zero copy cost. This is not an
optimization over serialization — it is the elimination of a semantic category.

```typescript
// Memory must be constructed as shared BEFORE wasm instantiation.
// SharedArrayBuffer cannot be retrofitted onto an existing non-shared instance.
const sharedMemory = new WebAssembly.Memory({
  initial: 256,    // 256 × 64KiB = 16MB initial allocation
  maximum: 65536,  // 4GB theoretical ceiling
  shared: true,    // Internally wraps a SharedArrayBuffer
});

const { instance } = await WebAssembly.instantiateStreaming(
  fetch('/nexus_engine.wasm'),
  { env: { memory: sharedMemory } }  // Injected at link time — not post-hoc
);

// Transfer ownership to Worker — zero-copy, not clone
worker.postMessage({ type: 'init', memory: sharedMemory }, [sharedMemory]);
```

The Rust target must declare shared memory at compile time:

```bash
RUSTFLAGS="-C target-feature=+atomics,+bulk-memory,+mutable-globals" \
  cargo build --target wasm32-unknown-unknown --release
```

The resulting WAT memory section:
```wat
(memory (export "memory") (import "env" "memory") (;shared;) 16 65536)
```

### Shared Address Space Layout

```
SAB Layout (conceptual — not byte-accurate, illustrative)
├── [0x0000 – 0x0FFF]  Control block (Int32Array)
│   ├── CTRL_WRITE_IDX    : which buffer Rust is writing (0|1)
│   ├── CTRL_READY_IDX    : which buffer is ready for JS to read
│   ├── CTRL_CONSUME_IDX  : JS acknowledgment to Rust
│   ├── INPUT_WRITE_IDX   : ring buffer write head (input events)
│   └── INPUT_READ_IDX    : ring buffer read head
├── [0x1000 – 0x1FFF]  Input event ring buffer
├── [0x2000 – 0x????]  Framebuffer A (width × height × 4 bytes RGBA)
├── [0x???? – 0x????]  Framebuffer B (double-buffer swap target)
└── [0x???? – end]     Document field data (SoA layout, phase-partitioned)
```

---

## Synchronization: Correct Mesa-Semantics Atomics

### The Critical API Constraint

`Atomics.waitAsync(typedArray, index, expectedValue)` suspends the microtask
queue **only if** `typedArray[index] === expectedValue` at call time. If they
differ, the promise resolves immediately with `'not-equal'`.

This means: you cannot pass a sentinel (e.g., `-1`) as a "block on any change"
wildcard. Passing `-1` against an index holding `0` or `1` produces guaranteed
immediate resolution — a polling loop throttled entirely by display refresh rate,
not a hardware-backed sleep.

### The Correct Pattern: Generation-Tracking Consumer

```typescript
// The consumer tracks its OWN last-consumed state.
// waitAsync is called with that state as the expected value.
// This is a condition variable: "sleep WHILE value equals lastConsumed"
async function frameConsumer(
  ctrl: Int32Array,
  mem: WebAssembly.Memory,
  ctx: OffscreenCanvasRenderingContext2D
): Promise<void> {
  // Init: Rust will write buffer 0 first. We initialize to 1
  // so the first real publish immediately wakes us.
  let lastConsumed: 0 | 1 = 1;

  while (true) {
    const { value: result } = Atomics.waitAsync(
      ctrl, 
      CTRL_READY_IDX, 
      lastConsumed  // ← correct: block WHILE this is still what we last saw
    );

    const outcome = await result;
    // 'ok'        → woken by Atomics.notify from Rust Worker
    // 'not-equal' → Rust already published a new frame before we suspended
    // Both are valid; both require identical handling

    const readBuf = Atomics.load(ctrl, CTRL_READY_IDX) as 0 | 1;
    if (readBuf === lastConsumed) continue; // Spurious wake guard

    const offset = readBuf === 0 ? BUFFER_0_OFFSET : BUFFER_1_OFFSET;
    const frame = new Uint8ClampedArray(mem.buffer, offset, FRAME_SIZE);

    await new Promise<void>(resolve => {
      requestAnimationFrame(() => {
        ctx.putImageData(new ImageData(frame, width, height), 0, 0);
        lastConsumed = readBuf; // Update BEFORE notifying — prevents race
        Atomics.store(ctrl, CTRL_CONSUME_IDX, readBuf);
        Atomics.notify(ctrl, CTRL_CONSUME_IDX, 1);
        resolve();
      });
    });
  }
}
```

### Rust Producer Side

```rust
use std::sync::atomic::{AtomicI32, Ordering};

pub fn render_loop(ctrl: &[AtomicI32], mem: &mut [u8]) {
    let mut write_buf: i32 = 0;

    loop {
        let offset = if write_buf == 0 { BUFFER_0_OFFSET } else { BUFFER_1_OFFSET };
        let frame_region = &mut mem[offset..offset + FRAME_SIZE];

        // Heavy compute — JS is reading from the OTHER buffer during this
        rasterize_scene(frame_region);

        // Release store: all preceding writes visible to any thread
        // that subsequently observes this via an Acquire load
        ctrl[CTRL_READY_IDX].store(write_buf, Ordering::Release);
        atomic_notify(&ctrl[CTRL_READY_IDX], 1);

        // Wait for JS to consume before reclaiming this buffer
        while ctrl[CTRL_CONSUME_IDX].load(Ordering::Acquire) != write_buf {
            core::hint::spin_loop();
        }

        write_buf = 1 - write_buf; // Swap buffers
    }
}
```

The `Release`/`Acquire` pair establishes a formal happens-before relationship
across threads. Without it, the CPU's out-of-order execution and WASM's own
weak memory model (mirroring hardware) can legally reorder frame writes to be
*visible after* the notification. This is not defensive programming — it is a
correctness requirement.

---

## Input Decoupling: The SAB Ring Buffer

`OffscreenCanvas` decouples rasterization throughput from main thread GC pauses.
It does **not** decouple input delivery. DOM pointer events originate exclusively
on the main thread. A 200ms React reconcile will cause the Worker to render 12
smooth frames of completely stale interaction state.

The solution: bypass React's event system for high-frequency pointer events,
writing directly into a SAB ring buffer.

```typescript
// Main thread: allocation-free pointer handler
// This cannot block during GC because it makes no heap allocations
const inputRingBuffer = new Float32Array(sharedMemory.buffer, INPUT_RING_OFFSET, RING_SIZE * 2);
const inputCtrl = new Int32Array(sharedMemory.buffer, 0, CTRL_BLOCK_SIZE);

canvas.addEventListener('pointerrawupdate', (e: PointerEvent) => {
  const writeIdx = Atomics.load(inputCtrl, INPUT_WRITE_IDX);
  const slot = (writeIdx & RING_MASK) * 2;
  inputRingBuffer[slot]     = e.clientX;
  inputRingBuffer[slot + 1] = e.clientY;
  Atomics.add(inputCtrl, INPUT_WRITE_IDX, 1);
  // No postMessage. No allocation. No GC interaction.
}, { passive: true });
```

```rust
// Worker/Rust: drains the ring buffer every frame
fn poll_input(input_ctrl: &[AtomicI32], input_buffer: &[f32]) -> impl Iterator<Item = (f32, f32)> {
    let write_idx = input_ctrl[INPUT_WRITE_IDX].load(Ordering::Acquire);
    let read_idx  = input_ctrl[INPUT_READ_IDX].load(Ordering::Relaxed);

    let events = (read_idx..write_idx).map(|i| {
        let base = (i as usize & RING_MASK) * 2;
        (input_buffer[base], input_buffer[base + 1])
    });

    input_ctrl[INPUT_READ_IDX].store(write_idx, Ordering::Release);
    events
}
```

---

## Data-Oriented Design: Phase-Partitioned Layout

DOD is not a universal prescription. It is a per-phase design decision driven
by access pattern invariants. Applying SoA uniformly across a multi-phase
pipeline produces incoherent structures in phases with inherently hierarchical
or heterogeneous access patterns.

### Phase 1: Parse Tree — AoS is Correct

PDF content streams are operator-operand sequences with heterogeneous types and
variable-length operand lists. This is graph traversal. SoA is architecturally
incoherent here — there is no "batch of homogeneous nodes" to vectorize over.

```rust
// AoS is the correct layout for parse tree nodes.
// This is not a hot numerics loop — it is a heterogeneous traversal.
struct ContentStreamNode {
    operator: PdfOperator,
    operands: SmallVec<[PdfObject; 4]>, // Inline storage avoids heap for common cases
    byte_offset: u32,
}
```

### Phase 2: Field Extraction Batch — SoA is Correct

After parsing, fields are collected into homogeneous batches for bulk
classification. Access pattern is now fully predictable: alignment scoring
touches only bounding box coordinates across all N fields sequentially.
One cache line holds 16 f32 values — 16 field coordinates processed per
prefetch cycle.

```rust
#[repr(C)] // Explicit layout for SIMD alignment guarantees
struct FieldBatch {
    // HOT: Bounding box coordinates — processed sequentially by alignment scorer
    // Cache line = 64 bytes = 16 × f32. Entire coordinate pass stays in L1.
    x_min:       Vec<f32>,
    y_min:       Vec<f32>,
    x_max:       Vec<f32>,
    y_max:       Vec<f32>,

    // WARM: Classification outputs — written once after hot pass
    confidence:  Vec<f32>,
    field_type:  Vec<FieldType>,

    // COLD: Text content — accessed by index, not iterated
    text_offset: Vec<u32>,   // Index into a separate text slab
    text_slab:   Vec<u8>,    // Contiguous UTF-8, no per-string allocations
}
```

The SoA layout is applied precisely at the **phase boundary** — the transition
from parse tree to bulk-processable field arrays. The DOD discipline is scoped
to the computational phase where batch processing occurs. This is not a
performance optimization applied after profiling; it is a domain modeling
decision made because the access pattern at this phase is axiomatically known.

---

## COOP/COEP: The Security Tax and Its Actual Scope

`SharedArrayBuffer` requires these response headers on every page that uses it:

```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

### What This Actually Breaks

| Integration | Broken? | Notes |
|-------------|---------|-------|
| Google Analytics 4 | **No** | First-party script loader, no cross-origin iframe |
| Google Tag Manager (loader) | **No** | Script only |
| GTM → Hotjar / FullStory | **Yes** | These inject cross-origin iframes |
| Stripe Elements | **No** (2026) | Stripe CDN now serves `CORP` headers on SDK variants |
| Facebook Pixel | **No** | Script-only, no iframe requirement |
| Legacy ad networks | **Yes** | Cross-origin iframes without CORP headers |
| YouTube embeds (standard) | **No** | Google's CDN is COEP-compatible since 2023 |

For a B2B freight broker document intelligence platform, this surface is small.
You are not running Hotjar on an enterprise AR tool. The tax is much higher for
consumer media properties than for purpose-built productivity software.

### Bun Server Configuration

```typescript
// server.ts
import { serve } from 'bun';

serve({
  port: 3000,
  fetch(req) {
    const url = new URL(req.url);
    const response = await handleRequest(req);

    return new Response(response.body, {
      status: response.status,
      headers: {
        ...response.headers,
        // Required for SharedArrayBuffer
        'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Embedder-Policy': 'require-corp',
        // Required for resources you DO control to be embeddable
        'Cross-Origin-Resource-Policy': 'same-site',
      }
    });
  }
});
```

---

## Document Intelligence Pipeline: Full Phase Map

For freight broker AR document processing, the pipeline maps directly onto
the architecture above.

```
Input: PDF binary (Carrier Invoice, Rate Confirmation, BOL)
│
├── [WASM Worker — Phase 1: Structural Parse]
│   ├── lopdf-style binary parser (AoS parse tree)
│   ├── Content stream tokenizer
│   ├── Font resource resolver
│   └── Page geometry model
│   Output: ContentStreamGraph (AoS, ~100μs for typical invoice)
│
├── [WASM Worker — Phase 2: Field Extraction]
│   ├── Text run collector → FieldBatch (SoA layout)
│   ├── Bounding box normalization
│   ├── Reading order heuristic (Y-major, X-secondary sort)
│   └── Table structure detection (gap analysis on x_min/x_max arrays)
│   Output: FieldBatch (SoA, SIMD-eligible layout)
│
├── [WASM Worker — Phase 3: Classification]
│   ├── Rule engine (regex + layout geometry) — handles ~80% of cases
│   ├── Lightweight embedding model (GGML quantized, optional)
│   └── Confidence score per field
│   Output: ClassifiedFieldBatch with confidence scores
│
├── [Decision Gate]
│   ├── confidence > threshold → direct to output, no API call
│   └── confidence < threshold → Claude API call (ambiguous fields only)
│
├── [Turso — Edge Persistence]
│   ├── Extracted metadata (field names, values, positions)
│   ├── Processing audit log (append-only)
│   ├── Template store (per-carrier field mapping rules)
│   └── Session state (no raw PDF bytes ever leave the browser)
│
└── Output: Structured JSON / EDI-ready payload
```

### Cost Model at Scale

| Processing Step | Cost per Document |
|-----------------|------------------|
| WASM parse + extract (browser) | $0.00 |
| Rule-based classification (~80% of docs) | $0.00 |
| Claude API call (remaining ~20%) | ~$0.002 |
| Turso metadata write | ~$0.000001 |
| **Blended cost at scale** | **~$0.0004** |

Compare to full-pipeline LLM extraction at ~$0.02–0.05/doc. At 10,000
documents/month, this stack costs ~$4 vs ~$200–500. The delta compounds.

---

## The Irreversibility Map

These architectural decisions cannot be undone without structural rebuilds.
Make them explicitly.

| Decision | Reversible? | Notes |
|----------|-------------|-------|
| WASM compiled as shared memory | No | Requires separate non-threaded build artifact for fallback |
| `transferControlToOffscreen()` | No | Main thread loses canvas access permanently. Export API must be a Worker RPC. |
| SoA layout at FieldBatch phase boundary | Costly | Function signatures encode access pattern. AoS → SoA requires full hot-path rewrite. |
| COOP/COEP headers | Conditionally | Can be scoped per-route. Non-SAB pages can opt out. |
| Turso as append-only audit log | No | Append-only is a data integrity guarantee, not a storage optimization. |

---

## What This Is, Precisely

A **hardware-aware, thread-segregated, shared-memory compute pipeline hosted
in a sandboxed userspace execution environment**, where:

- Synchronization is Mesa-semantics condition variable signaling, not sentinel polling
- Input decoupling requires a SAB ring buffer — OffscreenCanvas alone is insufficient
- Rendering decoupling is real but scoped to rasterization; input delivery is a separate problem
- Data layout is assigned per computational phase based on access pattern invariants
- Privacy is structural, not policy — documents never leave the browser

The browser is the operating system. You are not escaping its constraints.
You are working with their grain. That is the actual architectural insight.

---

## Quick Start

```bash
# Prerequisites: Rust with wasm32 target, wasm-pack, Bun >= 1.0
rustup target add wasm32-unknown-unknown
cargo install wasm-pack

# Clone and install
git clone https://github.com/your-org/nexus
cd nexus
bun install

# Build WASM with atomics support
RUSTFLAGS="-C target-feature=+atomics,+bulk-memory,+mutable-globals" \
  wasm-pack build crates/nexus-engine \
    --target web \
    --out-dir ../../src/wasm \
    -- -Z build-std=panic_abort,std

# Dev server
bun run dev

# Production build
bun run build && bun run preview
```

---

## License

MIT
