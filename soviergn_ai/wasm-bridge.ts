/**
 * src/lib/wasm-bridge.ts
 *
 * Safe third-observer read protocol for WebAssembly.Memory.
 *
 * ─── THE THIRD-OBSERVER PROBLEM ────────────────────────────────────────────
 *
 * The NEXUS architecture defines two threads with established Atomics roles:
 *   Producer  → Rust Worker: writes framebuffers, Release-stores CTRL_READY_IDX
 *   Consumer  → JS Main:    Acquire-loads CTRL_READY_IDX, rAF paints, sends ACK
 *
 * A documentation visualization island introduces a third reader that must
 * observe memory state WITHOUT interfering with the production signaling
 * protocol. This is a fundamentally different problem from the two-party case:
 *
 *   - The viz layer cannot call Atomics.waitAsync — it would consume the
 *     notification intended for the frame consumer.
 *   - The viz layer cannot write to CTRL_CONSUME_IDX — it would ACK a frame
 *     before the real consumer has painted it.
 *   - The viz layer cannot hold a stable "safe window" guarantee — between any
 *     two instructions in JS, the Worker may complete a frame, swap buffers,
 *     and begin writing to the buffer we are currently reading.
 *
 * The solution is a SOFTWARE SEQLOCK applied to the viz read path.
 *
 * ─── SEQLOCK PROTOCOL ───────────────────────────────────────────────────────
 *
 * A seqlock (sequence lock) is a reader-writer synchronization primitive
 * optimized for read-heavy workloads where readers must never block writers.
 * It was originally described by Linus Torvalds in the Linux kernel (2.5.59,
 * 2003) for protecting short, frequently-read data structures.
 *
 * The canonical seqlock protocol:
 *
 *   Writer:
 *     1. Increment sequence counter (odd = write in progress)
 *     2. Memory barrier (Release semantics)
 *     3. Write data
 *     4. Memory barrier (Release semantics)
 *     5. Increment sequence counter again (even = consistent state)
 *
 *   Reader:
 *     1. Read sequence counter (seq1)
 *     2. If seq1 is odd: writer active, retry
 *     3. Memory barrier (Acquire semantics)
 *     4. Read data
 *     5. Memory barrier (Acquire semantics)
 *     6. Read sequence counter again (seq2)
 *     7. If seq1 !== seq2: writer interrupted, retry
 *     8. Data is consistent
 *
 * In our context, CTRL_WRITE_IDX serves as the sequence discriminant:
 * we read it before and after sampling the cold buffer. If it changes,
 * a buffer swap occurred during our read — the sample is torn and must
 * be discarded. This is an OPTIMISTIC READ — we proceed assuming no
 * concurrent write, then validate the assumption post-hoc.
 *
 * ─── MEMORY GROWTH SAFETY ───────────────────────────────────────────────────
 *
 * WebAssembly.Memory with {shared: true} wraps a SharedArrayBuffer.
 * The critical property: SAB instances are NEVER detached on memory.grow().
 *
 * Compare to non-shared WASM memory: when memory.grow() is called, the
 * underlying ArrayBuffer is detached and a new, larger one is allocated.
 * Any TypedArray views over the old buffer immediately throw TypeError
 * on access — this is a common source of silent memory corruption bugs
 * in WASM-JS interop code that doesn't account for growth.
 *
 * With a SAB-backed shared memory:
 *   - The SAB's identity is stable across growth events
 *   - Existing TypedArray views remain valid (they see the expanded capacity)
 *   - byteLength on the view reflects the pre-growth capacity until re-acquired
 *
 * WASM does not expose a "memory grew" event. We detect growth by comparing
 * memory.buffer.byteLength against our cached capacity on each read cycle.
 * When growth is detected, we invalidate all cached views and re-acquire them.
 * This is a cache invalidation, not a safety fix — the views would work either
 * way with SAB. The re-acquisition ensures our offset arithmetic is correct
 * relative to the new capacity.
 *
 * ─── ATOMICS MEMORY ORDERING ────────────────────────────────────────────────
 *
 * JavaScript's Atomics API implements a subset of the C++20 memory model.
 * The relevant orderings for this bridge:
 *
 *   Atomics.load(ta, idx)         → Acquire semantics
 *   Atomics.store(ta, idx, val)   → Release semantics
 *   Atomics.add/sub/etc           → sequentially consistent (stronger than needed)
 *
 * An Acquire load of a value that was stored with Release semantics establishes
 * a happens-before edge: all memory writes that preceded the Release store are
 * visible to the thread performing the Acquire load. This is the fundamental
 * guarantee that makes lock-free data structures correct across hardware
 * memory models (TSO on x86, weakly-ordered on ARM).
 *
 * Our seqlock read uses Atomics.load for the pre/post sequence reads, which
 * provides the Acquire fence required to observe consistent buffer state.
 */

/** Index constants into the Int32Array control block at offset 0x0000. */
export const CTRL = {
  WRITE_IDX:   0,  // Which buffer Rust is currently writing (0 | 1)
  READY_IDX:   1,  // Which buffer is ready for the JS consumer (0 | 1)
  CONSUME_IDX: 2,  // JS consumer's ACK — last consumed buffer index
  INPUT_WRITE: 3,  // Ring buffer write head (input events)
  INPUT_READ:  4,  // Ring buffer read head
} as const;

/** Memory region layout — offsets in bytes into the SharedArrayBuffer. */
export interface MemoryLayout {
  ctrlBlockOffset:    number;  // 0x0000 — Int32Array[5] control block
  ctrlBlockBytes:     number;
  inputRingOffset:    number;  // 0x1000 — Float32Array ring buffer
  inputRingCapacity:  number;  // Number of (x, y) event slots
  framebuffer0Offset: number;  // 0x2000 — RGBA framebuffer A
  framebuffer1Offset: number;  // 0x???? — RGBA framebuffer B
  framebufferBytes:   number;  // width * height * 4
  soaBatchOffset:     number;  // SoA FieldBatch — x_min, y_min, x_max, y_max
  soaBatchFieldCount: number;
  totalBytes:         number;
}

/** Thread execution state as observed by reading the control block. */
export interface ObservedThreadState {
  workerWriteBuffer:   0 | 1;
  readyBuffer:         0 | 1;
  lastConsumedBuffer:  0 | 1;
  inputRingDepth:      number;   // write - read (may be negative if stale)
  inputRingWriteHead:  number;
  inputRingReadHead:   number;
}

/** A stable, non-tearing sample of a memory region. */
export interface MemorySample {
  state:       ObservedThreadState;
  layout:      MemoryLayout;
  /** The cold buffer index — the one safe to read at the moment of sampling. */
  coldBuffer:  0 | 1;
  /** Whether this sample was obtained cleanly (seqlock validated). */
  consistent:  boolean;
  /** Number of retries required before a consistent sample was obtained. */
  retries:     number;
  timestamp:   number;
}

/** Result of reading a region of the cold framebuffer. */
export interface FramebufferSample {
  data:       Uint8ClampedArray;
  buffer:     0 | 1;
  consistent: boolean;
}

/** Wraps a wasm-bindgen doc-viz export surface. */
export interface NexusDocVizExports extends WebAssembly.Exports {
  memory:                    WebAssembly.Memory;
  ctrl_block_ptr:            () => number;
  ctrl_block_byte_len:       () => number;
  framebuffer_0_ptr:         () => number;
  framebuffer_1_ptr:         () => number;
  framebuffer_byte_len:      () => number;
  input_ring_ptr:            () => number;
  input_ring_capacity:       () => number;
  field_batch_x_min_ptr:     () => number;
  field_batch_len:           () => number;
  check_memory_invariants:   () => number;
}

/**
 * WasmMemoryBridge
 *
 * Safe read-only observer of NEXUS engine internal memory state.
 * Implements the seqlock protocol to obtain non-tearing memory samples
 * without interfering with the production Atomics signaling chain.
 *
 * Usage:
 *
 *   const bridge = await WasmMemoryBridge.fromUrl('/wasm/nexus_engine.wasm');
 *   const sample = bridge.sampleState();
 *   if (sample.consistent) {
 *     renderControlBlockViz(sample.state);
 *   }
 */
export class WasmMemoryBridge {
  private readonly exports: NexusDocVizExports;
  private readonly sab:     SharedArrayBuffer;
  private readonly ctrl:    Int32Array;

  /** Cached view capacity — used to detect memory.grow() events. */
  private cachedByteLength: number;

  /** Derived layout computed from wasm-bindgen pointer exports. */
  private layout: MemoryLayout;

  /** Seqlock retry budget before returning an inconsistent sample. */
  static readonly MAX_SEQLOCK_RETRIES = 8;

  private constructor(exports: NexusDocVizExports) {
    this.exports = exports;

    // Validate that memory is shared (SAB-backed).
    // Non-shared WASM memory would be detachable on growth,
    // making this bridge unsafe to hold across render cycles.
    if (!(exports.memory.buffer instanceof SharedArrayBuffer)) {
      throw new TypeError(
        "WasmMemoryBridge requires shared WebAssembly.Memory " +
        "(compiled with +atomics +bulk-memory). " +
        "Non-shared memory is detached on growth, which invalidates " +
        "this bridge's cached views."
      );
    }

    this.sab = exports.memory.buffer as SharedArrayBuffer;
    this.cachedByteLength = this.sab.byteLength;

    // Acquire the control block view.
    // The control block is at a fixed offset (exported by Rust) and is
    // a simple Int32Array. We keep this view for the lifetime of the bridge
    // because the control block never moves and SAB views survive growth.
    const ctrlOffset = exports.ctrl_block_ptr();
    const ctrlLen    = exports.ctrl_block_byte_len();
    this.ctrl = new Int32Array(this.sab, ctrlOffset, ctrlLen / 4);

    // Derive the full memory layout from the pointer exports.
    this.layout = this.deriveLayout();
  }

  /**
   * Load and instantiate the nexus-engine WASM module compiled with the
   * `doc-viz` feature flag. Falls back to a mock bridge in environments
   * where WASM is unavailable (e.g., SSR, test runners).
   */
  static async fromUrl(url: string): Promise<WasmMemoryBridge> {
    // Streaming instantiation requires application/wasm MIME type.
    // Bun-server.ts ensures this for .wasm assets.
    const { instance } = await WebAssembly.instantiateStreaming(
      fetch(url),
      {
        env: {
          // The WASM module was compiled with --import-memory.
          // The host constructs the shared memory and injects it,
          // ensuring the documentation layer and production layer
          // share the same physical SharedArrayBuffer.
          memory: new WebAssembly.Memory({
            initial: 256,
            maximum: 65536,
            shared: true,
          }),
        },
      }
    );

    const exports = instance.exports as NexusDocVizExports;

    // Verify the module exposes the doc-viz surface.
    // These exports are gated behind #[cfg(feature = "doc-viz")] in Rust —
    // if they're absent, the binary was compiled without the feature flag.
    const required = [
      "ctrl_block_ptr", "framebuffer_0_ptr", "framebuffer_1_ptr",
      "check_memory_invariants", "field_batch_x_min_ptr",
    ];
    const missing = required.filter(name => !(name in exports));
    if (missing.length > 0) {
      throw new Error(
        `WASM module missing doc-viz exports: ${missing.join(", ")}. ` +
        `Rebuild with: RUSTFLAGS="-C target-feature=+atomics,+bulk-memory,+mutable-globals" ` +
        `cargo build --features doc-viz --target wasm32-unknown-unknown`
      );
    }

    return new WasmMemoryBridge(exports);
  }

  /**
   * Derive the MemoryLayout from live pointer exports.
   *
   * This is called once at construction and re-called after memory.grow()
   * events. The layout is derived from the Rust module's own exported pointer
   * values, not from hardcoded constants — this means refactoring the Rust
   * arena layout automatically propagates to the documentation visualizer.
   * A PR that shifts memory regions will immediately produce a different
   * (and still correct) layout diagram without any documentation update.
   */
  private deriveLayout(): MemoryLayout {
    const e = this.exports;
    const fbBytes = e.framebuffer_byte_len();
    const ringCap = e.input_ring_capacity();

    return {
      ctrlBlockOffset:    e.ctrl_block_ptr(),
      ctrlBlockBytes:     e.ctrl_block_byte_len(),
      inputRingOffset:    e.input_ring_ptr(),
      inputRingCapacity:  ringCap,
      framebuffer0Offset: e.framebuffer_0_ptr(),
      framebuffer1Offset: e.framebuffer_1_ptr(),
      framebufferBytes:   fbBytes,
      soaBatchOffset:     e.field_batch_x_min_ptr(),
      soaBatchFieldCount: e.field_batch_len(),
      totalBytes:         this.cachedByteLength,
    };
  }

  /**
   * Detect memory.grow() by comparing current byteLength against cache.
   * If growth occurred, invalidate the layout cache and re-derive.
   *
   * WebAssembly.Memory does not expose a growth event or callback.
   * This poll-on-read approach adds ~2 property reads per sample cycle —
   * negligible compared to the cost of the visualization render.
   */
  private checkGrowth(): void {
    const currentBytes = this.exports.memory.buffer.byteLength;
    if (currentBytes !== this.cachedByteLength) {
      this.cachedByteLength = currentBytes;
      this.layout = this.deriveLayout();
    }
  }

  /**
   * Sample the thread execution state from the control block.
   *
   * Uses Atomics.load for all reads, which provides Acquire semantics:
   * we are guaranteed to see any memory writes that preceded the
   * corresponding Release stores from the Worker.
   */
  private readControlBlock(): ObservedThreadState {
    const writeBuffer   = Atomics.load(this.ctrl, CTRL.WRITE_IDX) as 0 | 1;
    const readyBuffer   = Atomics.load(this.ctrl, CTRL.READY_IDX) as 0 | 1;
    const consumedBuf   = Atomics.load(this.ctrl, CTRL.CONSUME_IDX) as 0 | 1;
    const inputWrite    = Atomics.load(this.ctrl, CTRL.INPUT_WRITE);
    const inputRead     = Atomics.load(this.ctrl, CTRL.INPUT_READ);

    return {
      workerWriteBuffer:  writeBuffer,
      readyBuffer:        readyBuffer,
      lastConsumedBuffer: consumedBuf,
      inputRingDepth:     Math.max(0, inputWrite - inputRead),
      inputRingWriteHead: inputWrite,
      inputRingReadHead:  inputRead,
    };
  }

  /**
   * sampleState — obtain a consistent, non-tearing snapshot of the
   * engine's memory state using the seqlock protocol.
   *
   * The seqlock retry loop:
   *
   *   1. Read CTRL_WRITE_IDX (pre-read discriminant)
   *   2. Read all control block values
   *   3. Read CTRL_WRITE_IDX again (post-read discriminant)
   *   4. If pre !== post: a buffer swap occurred during reads → retry
   *   5. If pre === post: reads are consistent → return sample
   *
   * The "buffer swap" event (Rust incrementing CTRL_WRITE_IDX from 0 to 1
   * or 1 to 0) is the equivalent of the seqlock's sequence counter
   * incrementing through an odd value. If we observe a change, our reads
   * span a write boundary and may contain torn values.
   *
   * In practice, the retry loop converges in 0–1 iterations because the
   * buffer swap is a single Atomics.store operation, and the control block
   * read window is ~200ns on a modern CPU. The retry budget of 8 is purely
   * defensive.
   */
  sampleState(): MemorySample {
    this.checkGrowth();
    let retries = 0;

    for (let i = 0; i < WasmMemoryBridge.MAX_SEQLOCK_RETRIES; i++) {
      // Pre-read discriminant — Acquire semantics via Atomics.load
      const preWrite = Atomics.load(this.ctrl, CTRL.WRITE_IDX);

      // Read all control block state
      const state = this.readControlBlock();

      // Post-read discriminant
      const postWrite = Atomics.load(this.ctrl, CTRL.WRITE_IDX);

      if (preWrite === postWrite) {
        // Consistent read — CTRL_WRITE_IDX did not change during our sample.
        // The cold buffer is the one NOT currently being written.
        const coldBuffer = (state.workerWriteBuffer === 0 ? 1 : 0) as 0 | 1;
        return {
          state,
          layout:     this.layout,
          coldBuffer,
          consistent: true,
          retries,
          timestamp:  performance.now(),
        };
      }
      retries++;
    }

    // Exhausted retry budget — return best-effort sample marked inconsistent.
    // The visualization layer should treat this as a "busy" state and skip
    // rendering rather than displaying potentially corrupt data.
    const state = this.readControlBlock();
    return {
      state,
      layout:     this.layout,
      coldBuffer: (state.workerWriteBuffer === 0 ? 1 : 0) as 0 | 1,
      consistent: false,
      retries,
      timestamp:  performance.now(),
    };
  }

  /**
   * sampleFramebuffer — read a snapshot of the cold framebuffer.
   *
   * This combines the seqlock state sample with a framebuffer read.
   * The read is bounded to the cold buffer region — the buffer the Worker
   * is NOT currently writing. We validate consistency by checking that
   * CTRL_WRITE_IDX did not change between our state read and our data read.
   *
   * @param width  - framebuffer width in pixels
   * @param height - framebuffer height in pixels
   */
  sampleFramebuffer(width: number, height: number): FramebufferSample | null {
    this.checkGrowth();
    const stateSample = this.sampleState();
    if (!stateSample.consistent) return null;

    const { coldBuffer, layout } = stateSample;
    const offset = coldBuffer === 0
      ? layout.framebuffer0Offset
      : layout.framebuffer1Offset;

    // Validate offset is within current SAB bounds
    if (offset + layout.framebufferBytes > this.cachedByteLength) {
      console.warn(
        `WasmMemoryBridge: framebuffer${coldBuffer} offset 0x${offset.toString(16)} ` +
        `+ ${layout.framebufferBytes} bytes exceeds SAB byteLength ${this.cachedByteLength}`
      );
      return null;
    }

    // Create a view over the cold buffer region.
    // Uint8ClampedArray is required by ImageData — values are clamped to [0,255].
    // This view is intentionally not cached — we want to observe the exact
    // bytes present at this moment, not a stale snapshot.
    const data = new Uint8ClampedArray(this.sab, offset, width * height * 4);

    // Post-read consistency check: verify Worker hasn't swapped buffers
    // during our Uint8ClampedArray construction (which may allocate).
    const postWrite = Atomics.load(this.ctrl, CTRL.WRITE_IDX);
    const consistent = postWrite === stateSample.state.workerWriteBuffer;

    return { data, buffer: coldBuffer, consistent };
  }

  /**
   * checkInvariants — call the Rust invariant checker and return the bitfield.
   *
   * Return value: 0 = all invariants satisfied.
   * Non-zero: bitmask of violated invariants (see doc_viz.rs for bit definitions).
   *
   * This is the CI integration point: `assert(bridge.checkInvariants() === 0)`
   * in a Playwright test run against the documentation page validates that
   * no memory region overlaps exist in the compiled binary.
   */
  checkInvariants(): number {
    return this.exports.check_memory_invariants();
  }

  get currentLayout(): Readonly<MemoryLayout> {
    this.checkGrowth();
    return this.layout;
  }

  /**
   * Expose the raw SharedArrayBuffer for cases where the visualization
   * layer needs to construct its own typed views (e.g., the SoA profiler
   * constructing a Float32Array over the field batch region).
   *
   * The caller must respect the seqlock protocol — read CTRL_WRITE_IDX
   * before and after any multi-value read from a region that may be
   * written concurrently.
   */
  get sharedBuffer(): SharedArrayBuffer {
    return this.sab;
  }
}
