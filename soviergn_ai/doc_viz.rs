// crates/nexus-engine/src/doc_viz.rs
//
// Documentation visualization export surface.
//
// This module is compiled ONLY when the `doc-viz` feature flag is enabled.
// It exposes internal arena pointers and memory layout constants to the JS
// documentation layer, enabling the Executable Topology Specification to
// visualize live engine state rather than rendering static diagrams.
//
// ─── WHY A FEATURE FLAG? ────────────────────────────────────────────────────
//
// The exported functions in this module violate a fundamental WASM security
// property: they expose raw linear memory pointers to the host. In the default
// production build, WASM's capability model ensures that the host JavaScript
// environment cannot observe the module's internal memory layout beyond what
// is explicitly exported. The `doc-viz` exports deliberately break this
// encapsulation for instrumentation purposes.
//
// Keeping this behind a feature flag ensures:
//   1. Production binaries expose zero internal layout information.
//   2. The documentation build is explicitly opt-in:
//      `cargo build --features doc-viz --target wasm32-unknown-unknown`
//   3. CI can verify invariants against the doc-viz binary without shipping
//      the instrumented binary to users.
//
// ─── WASM-BINDGEN EXPORT CONTRACT ───────────────────────────────────────────
//
// Each function returns a `u32` representing a byte offset into the WASM
// module's linear memory. The JS layer constructs typed array views over
// the exported `WebAssembly.Memory` object using these offsets:
//
//   const ptr = instance.exports.ctrl_block_ptr();         // → u32 offset
//   const ctrl = new Int32Array(memory.buffer, ptr, len);  // → view
//
// The `#[wasm_bindgen]` attribute on a `pub fn() -> u32` generates:
//   - A WASM export with the function's name
//   - A TypeScript declaration file entry (when --typescript is passed to wasm-pack)
//   - A JS wrapper that handles number coercion
//
// wasm-bindgen does not automatically handle raw pointer returns as safe —
// it is the caller's responsibility to stay within bounds. The JS bridge
// (wasm-bridge.ts) validates all offsets against memory.buffer.byteLength
// before constructing views.
//
// ─── REPR AND ALIGNMENT REQUIREMENTS ────────────────────────────────────────
//
// The control block uses `#[repr(C)]` to guarantee a stable, predictable
// field layout. Without this annotation, Rust's optimizer is permitted to
// reorder struct fields for padding reduction, which would invalidate the
// JS side's index constants (CTRL.WRITE_IDX = 0, etc.).
//
// The framebuffers and SoA field arrays are plain `Vec<u8>` and `Vec<f32>`
// respectively — their heap allocation addresses are not stable across
// program invocations, which is why we export pointer-returning functions
// rather than compile-time constants. The functions are called once at
// bridge initialization and the results are cached.
//
// ─── MEMORY INVARIANT BITFIELD ──────────────────────────────────────────────
//
// check_memory_invariants() returns a u32 bitfield encoding region overlap
// violations. Each bit represents a specific pair of regions:
//
//   Bit 0: ctrl_block ∩ framebuffer_a ≠ ∅
//   Bit 1: framebuffer_a ∩ framebuffer_b ≠ ∅
//   Bit 2: framebuffer_b ∩ input_ring ≠ ∅
//   Bit 3: input_ring ∩ soa_field_batch ≠ ∅
//
// A return value of 0 asserts that all memory regions are non-overlapping.
// This function is designed to be called in CI via a headless browser test:
//
//   const violations = instance.exports.check_memory_invariants();
//   assert.strictEqual(violations, 0, `Memory invariant violation: 0b${violations.toString(2)}`);
//
// This transforms a documentation page into an integration test: a PR that
// introduces memory region overlap produces a visible, immediately failing
// CI check rather than silent data corruption at runtime.

use wasm_bindgen::prelude::*;

// ── Static arena allocations ──────────────────────────────────────────────
// In a production implementation, these would be thread-local or protected
// by the atomic synchronization protocol. For the doc-viz build, they are
// static mutable to simplify initialization — this is sound in the WASM
// single-threaded execution model (wasm32-unknown-unknown with atomics
// uses cooperative threading, not true parallelism at the JS level).
//
// The actual production implementation uses a global allocator slab that
// is initialized once in `nexus_init()` and thereafter immutable in terms
// of base addresses (though content is continuously overwritten by the
// rasterization loop).

/// Width and height used for the doc-viz build's framebuffer allocation.
/// Match these to the OffscreenCanvas dimensions in the documentation island.
pub const DOC_VIZ_WIDTH:  u32 = 1920;
pub const DOC_VIZ_HEIGHT: u32 = 1080;
pub const DOC_VIZ_FRAME_BYTES: usize = (DOC_VIZ_WIDTH * DOC_VIZ_HEIGHT * 4) as usize;

/// Maximum number of fields in the SoA classification batch.
/// This is the Phase 2 data structure — proportional to documents in flight.
pub const MAX_FIELD_COUNT: usize = 8192;

/// Input event ring buffer capacity. Must be a power of two for bitmask modulo.
pub const INPUT_RING_CAPACITY: usize = 256;

#[repr(C)]  // Stable field order — required for Int32Array index constants
pub struct ControlBlock {
    /// Index of the buffer Rust is currently writing (0 or 1).
    /// Atomically stored with Release ordering before Atomics.notify.
    pub write_idx:   i32,
    /// Index of the most recently completed buffer, ready for JS to read.
    /// JS performs an Acquire load on this before accessing framebuffer data.
    pub ready_idx:   i32,
    /// JS consumer's acknowledgment — the last buffer index it consumed.
    /// Rust spins on this with Acquire loads to reclaim the buffer.
    pub consume_idx: i32,
    /// Ring buffer write head — monotonically increasing, not masked.
    pub input_write: i32,
    /// Ring buffer read head — monotonically increasing, not masked.
    pub input_read:  i32,
}

// Static allocation of all major arenas.
// The doc-viz build uses zero-initialized statics to establish base addresses.
// The production build initializes these via `nexus_init()` which performs
// the shared memory injection and sets the initial atomic state.

#[cfg(feature = "doc-viz")]
static mut CTRL_BLOCK: ControlBlock = ControlBlock {
    write_idx:   0,
    ready_idx:   0,
    consume_idx: 1,  // Init to 1 so first publish of buffer 0 wakes consumer
    input_write: 0,
    input_read:  0,
};

#[cfg(feature = "doc-viz")]
static mut FRAMEBUFFER_A: [u8; DOC_VIZ_FRAME_BYTES] = [0u8; DOC_VIZ_FRAME_BYTES];

#[cfg(feature = "doc-viz")]
static mut FRAMEBUFFER_B: [u8; DOC_VIZ_FRAME_BYTES] = [0u8; DOC_VIZ_FRAME_BYTES];

#[cfg(feature = "doc-viz")]
static mut INPUT_RING: [f32; INPUT_RING_CAPACITY * 2] = [0.0f32; INPUT_RING_CAPACITY * 2];

// SoA FieldBatch — Phase 2 classification data.
// Declared as separate arrays rather than a struct to guarantee that each
// coordinate dimension is contiguous in memory, enabling SIMD auto-vectorization
// of the bounding box alignment scoring pass.
#[cfg(feature = "doc-viz")]
static mut FIELD_X_MIN: [f32; MAX_FIELD_COUNT] = [0.0f32; MAX_FIELD_COUNT];

#[cfg(feature = "doc-viz")]
static mut FIELD_X_MAX: [f32; MAX_FIELD_COUNT] = [0.0f32; MAX_FIELD_COUNT];

#[cfg(feature = "doc-viz")]
static mut FIELD_Y_MIN: [f32; MAX_FIELD_COUNT] = [0.0f32; MAX_FIELD_COUNT];

#[cfg(feature = "doc-viz")]
static mut FIELD_Y_MAX: [f32; MAX_FIELD_COUNT] = [0.0f32; MAX_FIELD_COUNT];

// ── wasm-bindgen exports ───────────────────────────────────────────────────
// Each function returns the byte offset of its arena within WASM linear memory.
// The `as *const _ as u32` pattern converts a raw pointer to a u32 offset.
// This is safe in wasm32-unknown-unknown because:
//   - Pointer size is 32 bits (the address space IS 32-bit linear memory)
//   - Static addresses are immutable after initialization (no address-space layout
//     randomization in WASM — the memory model has no such concept)
//   - The JS caller validates bounds before constructing views

#[cfg(feature = "doc-viz")]
#[wasm_bindgen]
pub fn ctrl_block_ptr() -> u32 {
    unsafe { &CTRL_BLOCK as *const ControlBlock as u32 }
}

#[cfg(feature = "doc-viz")]
#[wasm_bindgen]
pub fn ctrl_block_byte_len() -> u32 {
    std::mem::size_of::<ControlBlock>() as u32
}

#[cfg(feature = "doc-viz")]
#[wasm_bindgen]
pub fn framebuffer_0_ptr() -> u32 {
    unsafe { FRAMEBUFFER_A.as_ptr() as u32 }
}

#[cfg(feature = "doc-viz")]
#[wasm_bindgen]
pub fn framebuffer_1_ptr() -> u32 {
    unsafe { FRAMEBUFFER_B.as_ptr() as u32 }
}

#[cfg(feature = "doc-viz")]
#[wasm_bindgen]
pub fn framebuffer_byte_len() -> u32 {
    DOC_VIZ_FRAME_BYTES as u32
}

#[cfg(feature = "doc-viz")]
#[wasm_bindgen]
pub fn input_ring_ptr() -> u32 {
    unsafe { INPUT_RING.as_ptr() as u32 }
}

#[cfg(feature = "doc-viz")]
#[wasm_bindgen]
pub fn input_ring_capacity() -> u32 {
    INPUT_RING_CAPACITY as u32
}

#[cfg(feature = "doc-viz")]
#[wasm_bindgen]
pub fn field_batch_x_min_ptr() -> u32 {
    unsafe { FIELD_X_MIN.as_ptr() as u32 }
}

#[cfg(feature = "doc-viz")]
#[wasm_bindgen]
pub fn field_batch_len() -> u32 {
    MAX_FIELD_COUNT as u32
}

/// Invariant checker — returns 0 if all memory regions are non-overlapping.
/// Non-zero: bitmask of violated region pairs (see module-level comments).
///
/// This function is the CI integration point. Call it from a Playwright test
/// after instantiating the doc-viz WASM module to assert that no memory
/// region overlaps exist in the compiled binary:
///
///   const violations = instance.exports.check_memory_invariants();
///   assert.strictEqual(violations, 0);
///
#[cfg(feature = "doc-viz")]
#[wasm_bindgen]
pub fn check_memory_invariants() -> u32 {
    let regions: [(u32, u32); 5] = [
        (ctrl_block_ptr(),    ctrl_block_byte_len()),
        (framebuffer_0_ptr(), framebuffer_byte_len()),
        (framebuffer_1_ptr(), framebuffer_byte_len()),
        (input_ring_ptr(),    input_ring_capacity() * 8),
        (field_batch_x_min_ptr(), (MAX_FIELD_COUNT * 4) as u32),
    ];

    let mut violations: u32 = 0;

    // Check all pairs for overlap. Two intervals [a, a+la) and [b, b+lb)
    // overlap iff a < b+lb AND b < a+la.
    for i in 0..regions.len() {
        for j in (i + 1)..regions.len() {
            let (a_start, a_len) = regions[i];
            let (b_start, b_len) = regions[j];
            let a_end = a_start.saturating_add(a_len);
            let b_end = b_start.saturating_add(b_len);

            if a_start < b_end && b_start < a_end {
                // Encode the pair index into the violation bitfield.
                // Pair (i, j) maps to bit i for simplicity; a full implementation
                // would use a Cantor pairing function for unique pair encoding.
                violations |= 1u32 << i;
            }
        }
    }

    violations
}

/// Returns the frame dimensions for the current doc-viz build.
/// The JS layer uses these to construct correctly-sized ImageData objects.
#[cfg(feature = "doc-viz")]
#[wasm_bindgen]
pub fn framebuffer_width() -> u32 { DOC_VIZ_WIDTH }

#[cfg(feature = "doc-viz")]
#[wasm_bindgen]
pub fn framebuffer_height() -> u32 { DOC_VIZ_HEIGHT }
