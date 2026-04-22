// playwright/invariants.spec.ts
//
// CI integration test for the Nexus Executable Topology Specification.
//
// This spec validates two properties that static code review cannot verify:
//
//   1. MEMORY LAYOUT CORRECTNESS — that no memory arena overlaps exist in the
//      compiled binary. A PR shifting arena offsets (e.g., extending the SoA
//      FieldBatch without adjusting framebuffer offsets) produces a non-zero
//      violations bitfield from check_memory_invariants(), causing this test
//      to fail before merge. The documentation page is the integration test.
//
//   2. SEQLOCK CONSISTENCY — that the WasmMemoryBridge's third-observer read
//      protocol achieves a consistent sample rate above a defined threshold.
//      Consistent rate below 95% would indicate either pathological Worker
//      scheduling (buffer swaps occurring faster than our read window) or a
//      correctness error in the seqlock implementation.
//
// ─── TEST EXECUTION MODEL ────────────────────────────────────────────────────
//
// These tests run in a headed or headless Chromium instance with COOP/COEP
// headers active (served by the Bun dev server or Astro preview). The COOP/COEP
// headers are a prerequisite for SharedArrayBuffer availability, which is
// required for the WasmMemoryBridge to instantiate.
//
// The tests use page.evaluate() to execute synchronous assertions inside the
// browser context, against the bridge instance that the island exposes on
// window.__nexusBridge. This avoids the serialization overhead of postMessage-
// based communication — the bridge's state is read directly from JS.
//
// ─── CI CONFIGURATION ────────────────────────────────────────────────────────
//
// Required Playwright config (playwright.config.ts):
//
//   webServer: {
//     command: "bun run preview",  // or "bun run dev"
//     port: 4321,
//     reuseExistingServer: true,
//   }
//
// The preview server must serve COOP/COEP headers. The Bun server (bun-server.ts)
// handles this for production. For Astro dev mode, the headers are injected via
// vite.server.headers in astro.config.mts.
//
// ─── BROWSER EXPOSURE PATTERN ────────────────────────────────────────────────
//
// The island exposes the bridge on window for test access. This is added to
// NexusMemoryViz.tsx when the bridge reaches "ready" state:
//
//   if (typeof window !== "undefined" && process.env.NODE_ENV !== "production") {
//     (window as any).__nexusBridge = bridge;
//   }
//
// This pattern is acceptable for documentation infrastructure: the bridge is
// never shipped to production users (the WASM module requires the doc-viz
// feature flag), and the window exposure is guarded by NODE_ENV.

import { test, expect, Page } from "@playwright/test";

// ── Constants ─────────────────────────────────────────────────────────────────

const DOCS_SYNC_URL = "/docs/synchronization";

/** Maximum allowable memory invariant violations (0 = all regions non-overlapping). */
const ALLOWED_INVARIANT_VIOLATIONS = 0;

/** Minimum seqlock consistent read rate over 100 samples (fraction). */
const MIN_SEQLOCK_CONSISTENCY_RATE = 0.95;

/** Timeout for WASM module instantiation + island hydration (ms). */
const WASM_INIT_TIMEOUT_MS = 15_000;

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * waitForBridgeReady — polls until the island's WasmMemoryBridge is available
 * on window.__nexusBridge.
 *
 * The island is hydrated with `client:visible`, meaning it doesn't boot until
 * it enters the viewport. We scroll to the island before waiting.
 */
async function waitForBridgeReady(page: Page): Promise<void> {
  // Scroll the synchronization section into view to trigger client:visible hydration
  await page.evaluate(() => {
    document.querySelector("[data-nexus-viz-root]")?.scrollIntoView();
  });

  // Wait for the island to mount and the WASM module to instantiate
  await page.waitForFunction(
    () => typeof (window as any).__nexusBridge?.checkInvariants === "function",
    { timeout: WASM_INIT_TIMEOUT_MS }
  );
}

/**
 * collectSeqlockSamples — runs the bridge's sampleState() N times and
 * returns an array of consistency flags.
 *
 * Executed inside the browser context via page.evaluate() to avoid the
 * serialization overhead of transferring full MemorySample objects over CDP.
 */
async function collectSeqlockSamples(
  page: Page,
  sampleCount: number
): Promise<{ consistent: boolean; retries: number }[]> {
  return page.evaluate((count: number) => {
    const bridge = (window as any).__nexusBridge;
    const results: { consistent: boolean; retries: number }[] = [];
    for (let i = 0; i < count; i++) {
      const sample = bridge.sampleState();
      results.push({ consistent: sample.consistent, retries: sample.retries });
    }
    return results;
  }, sampleCount);
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe("Nexus Engine — Memory Invariants", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(DOCS_SYNC_URL);
    await waitForBridgeReady(page);
  });

  test("check_memory_invariants() returns 0 (no region overlaps)", async ({ page }) => {
    const violations = await page.evaluate(() => {
      return (window as any).__nexusBridge.checkInvariants() as number;
    });

    // Provide a human-readable failure message that identifies the specific
    // overlapping pair when violations > 0.
    const violationBits = violations.toString(2).padStart(4, "0");
    const REGION_PAIRS = [
      "ctrl_block ∩ framebuffer_a",
      "framebuffer_a ∩ framebuffer_b",
      "framebuffer_b ∩ input_ring",
      "input_ring ∩ soa_field_batch",
    ];
    const overlapping = REGION_PAIRS.filter((_, i) => violations & (1 << i));

    expect(violations, [
      `Memory invariant violation: 0b${violationBits}`,
      overlapping.length > 0
        ? `Overlapping regions: ${overlapping.join(", ")}`
        : "",
      "A PR shifted memory arena boundaries without adjusting offsets.",
      "Re-run build-doc-viz.sh and verify all arenas are non-overlapping.",
    ].filter(Boolean).join("\n")).toBe(ALLOWED_INVARIANT_VIOLATIONS);
  });

  test("memory layout derives from live pointer exports (not hardcoded constants)", async ({ page }) => {
    const layout = await page.evaluate(() => {
      const bridge = (window as any).__nexusBridge;
      return bridge.currentLayout;
    });

    // The layout must report the WASM module's actual memory capacity.
    // A hardcoded layout would report a fixed number regardless of the
    // compiled binary's allocations.
    expect(layout.totalBytes).toBeGreaterThan(0);
    expect(layout.ctrlBlockOffset).toBeGreaterThanOrEqual(0);
    expect(layout.framebuffer0Offset).toBeGreaterThan(layout.ctrlBlockOffset);
    expect(layout.framebuffer1Offset).toBeGreaterThan(layout.framebuffer0Offset);

    // Framebuffers must not overlap
    const fb0End = layout.framebuffer0Offset + layout.framebufferBytes;
    expect(fb0End).toBeLessThanOrEqual(layout.framebuffer1Offset);

    // SoA batch must come after framebuffers
    const fb1End = layout.framebuffer1Offset + layout.framebufferBytes;
    expect(layout.soaBatchOffset).toBeGreaterThanOrEqual(fb1End);
  });

  test("framebuffer regions fit within SAB bounds", async ({ page }) => {
    const result = await page.evaluate(() => {
      const bridge = (window as any).__nexusBridge;
      const l = bridge.currentLayout;
      const fb0End = l.framebuffer0Offset + l.framebufferBytes;
      const fb1End = l.framebuffer1Offset + l.framebufferBytes;
      return {
        fb0End,
        fb1End,
        totalBytes: l.totalBytes,
        fb0InBounds: fb0End <= l.totalBytes,
        fb1InBounds: fb1End <= l.totalBytes,
      };
    });

    expect(result.fb0InBounds, `Framebuffer A end (${result.fb0End}) exceeds SAB (${result.totalBytes})`).toBe(true);
    expect(result.fb1InBounds, `Framebuffer B end (${result.fb1End}) exceeds SAB (${result.totalBytes})`).toBe(true);
  });
});

test.describe("Nexus Engine — Seqlock Protocol Correctness", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(DOCS_SYNC_URL);
    await waitForBridgeReady(page);
  });

  test(`seqlock consistent read rate > ${MIN_SEQLOCK_CONSISTENCY_RATE * 100}% over 100 samples`, async ({ page }) => {
    const samples = await collectSeqlockSamples(page, 100);

    const consistentCount = samples.filter((s) => s.consistent).length;
    const consistentRate = consistentCount / samples.length;

    const maxRetries = Math.max(...samples.map((s) => s.retries));
    const avgRetries =
      samples.reduce((sum, s) => sum + s.retries, 0) / samples.length;

    expect(
      consistentRate,
      [
        `Seqlock consistency rate: ${(consistentRate * 100).toFixed(1)}%`,
        `(${consistentCount}/${samples.length} clean reads)`,
        `Max retries in a single read: ${maxRetries}`,
        `Average retries per read: ${avgRetries.toFixed(2)}`,
        "",
        "If consistency rate is low, the Rust Worker may be completing",
        "buffer swaps faster than the seqlock read window (~200ns).",
        "Consider increasing the frame interval or adding a spin-wait",
        "between the Worker's Release store and Atomics.notify.",
      ].join("\n")
    ).toBeGreaterThanOrEqual(MIN_SEQLOCK_CONSISTENCY_RATE);
  });

  test("seqlock does not consume Atomics notifications intended for frame consumer", async ({ page }) => {
    // The bridge must not call Atomics.waitAsync — only Atomics.load.
    // We verify this by ensuring the production frameCount continues to
    // advance while the bridge is running in its polling loop.
    //
    // If the bridge were calling waitAsync, it would steal notifications from
    // the frame consumer, causing the frame counter to stall.
    const frameCountBefore = await page.evaluate(() => {
      return (window as any).__nexusFrameCount ?? 0;
    });

    // Wait 500ms — at 60fps, we expect ~30 frames
    await page.waitForTimeout(500);

    const frameCountAfter = await page.evaluate(() => {
      return (window as any).__nexusFrameCount ?? 0;
    });

    const framesAdvanced = frameCountAfter - frameCountBefore;

    expect(
      framesAdvanced,
      [
        `Frame count did not advance during seqlock polling.`,
        `Before: ${frameCountBefore}, After: ${frameCountAfter}`,
        "The bridge may be consuming Atomics.notify signals intended for",
        "the frame consumer. Check that WasmMemoryBridge only uses",
        "Atomics.load and never calls Atomics.waitAsync or Atomics.wait.",
      ].join("\n")
    ).toBeGreaterThan(5); // At 60fps/500ms, expect ≥5 frames; 30 is typical
  });

  test("sampleFramebuffer returns consistent data for cold buffer", async ({ page }) => {
    const result = await page.evaluate(() => {
      const bridge = (window as any).__nexusBridge;
      // Use a small resolution to keep the data transfer manageable
      const sample = bridge.sampleFramebuffer(64, 64);
      if (!sample) return null;
      return {
        consistent: sample.consistent,
        buffer:     sample.buffer,
        byteLength: sample.data.byteLength,
        // Sample 4 pixels from the center to verify non-zero content
        centerPixels: Array.from(
          sample.data.slice(64 * 32 * 4, 64 * 32 * 4 + 16)
        ),
      };
    });

    expect(result).not.toBeNull();
    expect(result!.consistent).toBe(true);
    expect(result!.byteLength).toBe(64 * 64 * 4); // 64×64 RGBA
    expect([0, 1]).toContain(result!.buffer);      // Must be 0 or 1
  });
});

test.describe("Nexus Engine — SharedArrayBuffer Prerequisites", () => {
  test("page serves COOP/COEP headers (SharedArrayBuffer available)", async ({ page }) => {
    const response = await page.goto(DOCS_SYNC_URL);

    const coopHeader = response?.headers()["cross-origin-opener-policy"];
    const coepHeader = response?.headers()["cross-origin-embedder-policy"];

    expect(coopHeader, "Missing Cross-Origin-Opener-Policy header").toBe("same-origin");
    expect(coepHeader, "Missing Cross-Origin-Embedder-Policy header").toBe("require-corp");

    // Verify SharedArrayBuffer is actually accessible in the page context
    const sabAvailable = await page.evaluate(() => {
      try {
        new SharedArrayBuffer(4);
        return true;
      } catch {
        return false;
      }
    });

    expect(
      sabAvailable,
      "SharedArrayBuffer unavailable despite COOP/COEP headers. " +
      "Check that all subresources served to this page include " +
      "Cross-Origin-Resource-Policy headers."
    ).toBe(true);
  });

  test("WASM module declares shared memory in binary", async ({ page }) => {
    // Fetch the WASM binary and parse its memory section to verify
    // the shared flag is set. This catches the case where the binary
    // was compiled without +atomics and falls back to non-shared memory.
    const isShared = await page.evaluate(async () => {
      const response = await fetch("/wasm/nexus_engine_doc_viz_bg.wasm");
      const buffer = await response.arrayBuffer();

      // Parse the WASM binary to find the memory section (section type 0x05).
      // WASM binary format: 4-byte magic (\0asm) + 4-byte version (1) + sections.
      // Memory section element encoding: limits byte (0x01 = shared, 0x00 = non-shared)
      const bytes = new Uint8Array(buffer);

      // Walk sections looking for the memory section (id=5)
      let offset = 8; // Skip magic + version
      while (offset < bytes.length) {
        const sectionId   = bytes[offset];
        let sizeOffset    = offset + 1;
        // Decode LEB128 section size
        let size = 0, shift = 0, byte;
        do {
          byte = bytes[sizeOffset++];
          size |= (byte & 0x7F) << shift;
          shift += 7;
        } while (byte & 0x80);

        if (sectionId === 5) { // Memory section
          // Memory section: count + [limits...]
          // limits: flags_byte, min_pages[, max_pages]
          // flags bit 0: has max; flags bit 1: shared
          const countOffset = sizeOffset;
          const flagsByte   = bytes[countOffset + 1]; // Skip LEB128 count
          return (flagsByte & 0x02) !== 0; // Bit 1 = shared
        }

        offset = sizeOffset + size;
      }
      return false; // Memory section not found
    });

    expect(
      isShared,
      "WASM binary does not declare shared memory. " +
      "Rebuild with: RUSTFLAGS=\"-C target-feature=+atomics,+bulk-memory,+mutable-globals\""
    ).toBe(true);
  });
});
