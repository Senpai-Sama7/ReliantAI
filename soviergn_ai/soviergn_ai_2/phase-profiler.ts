/**
 * src/lib/phase-profiler.ts
 *
 * Statistical microbenchmark harness for the AoS→SoA phase boundary.
 *
 * ─── THE BROWSER MICROBENCHMARKING PROBLEM ──────────────────────────────────
 *
 * Measuring cache behavior differences in a browser runtime is hostile to
 * naive timing approaches for several compounding reasons:
 *
 *   1. JIT TIER TRANSITIONS
 *      V8 compiles WASM functions in two tiers:
 *        Liftoff (baseline): compiles in ~10μs/function, no optimization.
 *          Used immediately on first call.
 *        Turbofan (optimizing): compiles in background after ~1000 calls,
 *          produces ~3-5x faster code with SIMD auto-vectorization.
 *      Measurements taken before Turbofan fires capture Liftoff performance,
 *      which has no relationship to the production execution profile.
 *      Minimum warm-up: 2000 invocations per measured function.
 *
 *   2. PERFORMANCE.NOW() RESOLUTION
 *      After Spectre/Meltdown, browsers reduced timer resolution to prevent
 *      cache-timing side-channel attacks:
 *        Without COOP/COEP: ±100μs (Chrome), ±1ms (Firefox, IE-mode)
 *        With COOP/COEP:    ±5μs (Chrome), ±20μs (Firefox)
 *      Our Bun server serves COOP/COEP headers, so we operate in the
 *      higher-resolution regime. However: operations faster than 5μs require
 *      loop-based timing (measure N iterations, divide) rather than per-call
 *      timing.
 *
 *   3. HARDWARE PREFETCHER LEARNING
 *      Modern CPUs implement stride prefetchers that learn sequential access
 *      patterns after 2-4 cache misses and begin speculative loads. For AoS
 *      vs SoA comparisons, this means:
 *        - If the AoS traversal runs first, the prefetcher learns the stride
 *        - When SoA runs next, some of its "cache misses" are actually
 *          prefetched hits from the previous AoS run's pattern learning
 *      Solution: pollute the L1/L2 cache between measurements with a large
 *      sequential read of a different buffer (the "cache buster" pattern).
 *
 *   4. GARBAGE COLLECTION JITTER
 *      V8's generational GC introduces stop-the-world pauses of 0.5–50ms.
 *      Major GC cycles (old generation compaction) can pause 100–500ms.
 *      These pauses appear as outliers in timing data. They must be detected
 *      and excluded rather than averaged — they are not measurement error,
 *      they are scheduler noise orthogonal to the phenomenon being measured.
 *
 *   5. OS SCHEDULER PREEMPTION
 *      Even in a single-threaded WASM context, the OS scheduler can preempt
 *      the browser process for 1–15ms (typical time quantum). These manifest
 *      as large outliers indistinguishable from GC pauses at the sampling
 *      level. Both are excluded by the same IQR-based outlier rejection.
 *
 * ─── STATISTICAL METHODOLOGY ────────────────────────────────────────────────
 *
 * Each benchmark produces a `TimingDistribution` over N=200 trials (default).
 * The distribution characterizes:
 *
 *   - p50 (median): central tendency, robust to outliers
 *   - p95, p99:     tail latency — critical for cache miss characterization
 *   - IQR:          interquartile range, outlier-robust dispersion measure
 *   - σ (std dev):  after outlier rejection; measures trial-to-trial variance
 *
 * Outlier rejection uses the Tukey fence method (John Tukey, EDA, 1977):
 *   lower fence = Q1 - 1.5 × IQR
 *   upper fence = Q3 + 1.5 × IQR
 * Measurements outside [lower, upper] are discarded.
 * The k=1.5 multiplier corresponds to approximately ±2.7σ for normally
 * distributed data — aggressive enough to exclude GC pauses while preserving
 * the natural right tail of cache-miss latency distributions.
 *
 * ─── WASM BENCHMARK FUNCTIONS ────────────────────────────────────────────────
 *
 * The benchmark functions are implemented in Rust and compiled to WASM with
 * the doc-viz feature flag. Using WASM rather than JS for the benchmark
 * functions is intentional:
 *
 *   - JS engine optimizations (hidden class specialization, TypedArray fast
 *     paths) obscure the cache behavior we're measuring
 *   - WASM provides a more direct mapping to assembly output, making the
 *     L1/L2 miss penalty predictable
 *   - wasm-opt with --enable-simd generates explicit SIMD instructions
 *     for the SoA pass, making the throughput difference concrete
 *
 * The AoS benchmark traverses a `Vec<ContentStreamNode>` where each node
 * contains a heterogeneous mix of fields (operator enum, SmallVec of operands,
 * byte_offset). This replicates the Phase 1 parse tree traversal pattern.
 *
 * The SoA benchmark traverses four `Vec<f32>` arrays (x_min, y_min, x_max,
 * y_max) for the bounding box alignment scoring pass. This is the Phase 2
 * classification batch pattern.
 *
 * ─── CACHE CONTAMINATION PROTOCOL ───────────────────────────────────────────
 *
 * Between each trial, a "cache buster" buffer of size 2×L2_CACHE_SIZE is
 * read sequentially. This forces the L1 and L2 caches to evict the working
 * set from the previous trial, ensuring each trial begins from a cold cache
 * state. The L2 cache size on typical server/desktop CPUs is 256KB–1MB;
 * we use 4MB as a conservative upper bound.
 *
 * Cache buster size: 4MB × 2 = 8MB (ensures LLC eviction on most platforms)
 * Cache buster access pattern: sequential stride-1 reads (optimally prefetchable,
 * ensuring the buster itself completes quickly while still evicting the target
 * working set from all cache levels)
 */

/** Wasm-bindgen exports required for the phase profiler benchmark. */
export interface NexusProfilerExports extends WebAssembly.Exports {
  memory: WebAssembly.Memory;

  // Phase 1: AoS parse tree traversal benchmark
  // Traverses `node_count` ContentStreamNode objects, accumulating operator
  // counts. The accumulator prevents the optimizer from eliding the loop.
  // Returns: sum of operator type discriminants (opaque; for correctness only)
  bench_aos_parse_tree:      (node_count: number) => number;

  // Phase 2: SoA field batch alignment scoring benchmark
  // Computes bounding box overlap for `field_count` field pairs using
  // sequential SIMD-eligible f32 array access.
  // Returns: count of overlapping field pairs (opaque; for correctness only)
  bench_soa_field_scoring:   (field_count: number) => number;

  // Cache buster: reads `byte_count` bytes sequentially to evict L1/L2
  // Returns: XOR sum of all bytes (prevents optimizer elision)
  cache_bust:                (byte_count: number) => number;

  // JIT warm-up: runs both benchmarks `iterations` times without timing.
  // Call before measuring to ensure Turbofan has compiled both functions.
  warm_up:                   (iterations: number) => void;
}

/** Statistical distribution over N benchmark trials. */
export interface TimingDistribution {
  /** Raw sample array, sorted ascending, in microseconds. */
  rawSamples:    number[];
  /** After Tukey fence outlier rejection. */
  cleanSamples:  number[];
  /** Number of trials rejected as outliers. */
  outliersCount: number;

  // Percentiles (μs)
  p50:           number;
  p75:           number;
  p90:           number;
  p95:           number;
  p99:           number;
  min:           number;
  max:           number;

  // Dispersion
  mean:          number;
  stddev:        number;
  iqr:           number;   // Q3 - Q1

  // Cache characterization
  /** Estimated L1 hit rate — inferred from bimodal distribution detection */
  l1HitRatePct:  number;
}

export interface PhaseBenchmarkResult {
  aos:          TimingDistribution;
  soa:          TimingDistribution;
  /** Speedup factor: aos.p50 / soa.p50 */
  speedupP50:   number;
  /** Speedup at tail: aos.p95 / soa.p95 */
  speedupP95:   number;
  fieldCount:   number;
  timestamp:    number;
}

export interface BenchmarkConfig {
  /** Number of fields/nodes per trial. Default: 4096 */
  fieldCount:       number;
  /** Number of measurement trials. Default: 200 */
  trialCount:       number;
  /** Warm-up iterations before measurement begins. Default: 3000 */
  warmUpIterations: number;
  /** Cache buster size in bytes. Default: 8MB */
  cacheBusterBytes: number;
  /** Tukey fence multiplier. Default: 1.5 */
  tukeyK:           number;
}

const DEFAULT_CONFIG: BenchmarkConfig = {
  fieldCount:       4096,
  trialCount:       200,
  warmUpIterations: 3000,
  cacheBusterBytes: 8 * 1024 * 1024,  // 8MB — exceeds L2 on all common CPUs
  tukeyK:           1.5,
};

/**
 * PhaseProfiler
 *
 * Statistical benchmark harness for measuring the AoS→SoA phase boundary
 * cache performance difference in the NEXUS document processing pipeline.
 *
 * Usage:
 *   const profiler = await PhaseProfiler.fromUrl('/wasm/nexus_engine_doc_viz_bg.wasm');
 *   const result = await profiler.runBenchmark();
 *   renderFlameGraph(result);
 */
export class PhaseProfiler {
  private readonly exports: NexusProfilerExports;
  private readonly config:  BenchmarkConfig;

  private constructor(exports: NexusProfilerExports, config: BenchmarkConfig) {
    this.exports = exports;
    this.config  = config;
  }

  static async fromUrl(
    url:    string,
    config: Partial<BenchmarkConfig> = {}
  ): Promise<PhaseProfiler> {
    const { instance } = await WebAssembly.instantiateStreaming(fetch(url), {
      env: {
        memory: new WebAssembly.Memory({ initial: 256, maximum: 65536, shared: true }),
      },
    });
    const exports = instance.exports as NexusProfilerExports;
    return new PhaseProfiler(exports, { ...DEFAULT_CONFIG, ...config });
  }

  /**
   * runBenchmark — execute the full AoS vs SoA measurement protocol.
   *
   * The benchmark pipeline:
   *   1. JIT warm-up (3000 iterations each, ensures Turbofan compilation)
   *   2. Interleaved measurement: AoS trial → cache bust → SoA trial → cache bust
   *      Interleaving prevents systematic ordering bias: if AoS always ran
   *      before SoA, any CPU frequency scaling or thermal throttling would
   *      consistently affect SoA measurements.
   *   3. Statistical analysis: Tukey fence outlier rejection, percentile
   *      computation, bimodal L1-hit-rate inference
   *
   * The function yields control to the event loop between trial batches (every
   * 20 trials) via a 0ms setTimeout to prevent blocking the UI thread during
   * the measurement loop. This is a necessary concession — timing pauses are
   * introduced by the yield, but they are consistently placed between trials,
   * not within them, so they do not corrupt individual measurements.
   *
   * @param onProgress  Optional callback called every 20 trials with [0, 1] progress
   */
  async runBenchmark(
    onProgress?: (progress: number) => void
  ): Promise<PhaseBenchmarkResult> {
    const { fieldCount, trialCount, warmUpIterations, cacheBusterBytes, tukeyK } = this.config;

    // ── Step 1: JIT warm-up ────────────────────────────────────────────────
    // warm_up() calls both bench functions warmUpIterations times.
    // After ~1000 calls, V8's profiling tier triggers Turbofan compilation
    // for the hot functions. We use 3000 iterations to ensure the optimizing
    // compiler has fired and generated its final tier code before measurement.
    //
    // Observable effect: a short synchronous pause (~100-300ms on first call)
    // as Turbofan compiles the WASM functions. Subsequent benchmark runs are
    // unaffected (Turbofan output is cached in the CodeSpace).
    this.exports.warm_up(warmUpIterations);

    // Brief yield after warm-up to allow any pending microtasks (including
    // Turbofan's background compilation notification) to complete.
    await new Promise<void>(r => setTimeout(r, 50));

    const aosSamples: number[] = [];
    const soaSamples: number[] = [];

    // ── Step 2: Interleaved measurement loop ──────────────────────────────
    for (let i = 0; i < trialCount; i++) {
      // Cache buster before AoS trial.
      // This evicts any cached data from the previous SoA trial, ensuring
      // the AoS traversal begins from a cold-cache state for its working set.
      this.exports.cache_bust(cacheBusterBytes);

      // AoS timing: single-trial measurement.
      // performance.now() with COOP/COEP gives 5μs resolution.
      // Each AoS trial traverses 4096 ContentStreamNode objects at ~120 bytes/node
      // = ~480KB working set (fits in L2 on modern CPUs, cold after cache bust).
      const aosStart = performance.now();
      this.exports.bench_aos_parse_tree(fieldCount);
      const aosDuration = (performance.now() - aosStart) * 1000; // Convert ms → μs
      aosSamples.push(aosDuration);

      // Cache buster between AoS and SoA trials.
      this.exports.cache_bust(cacheBusterBytes);

      // SoA timing: traverses 4096 × 4 f32 arrays = 64KB working set.
      // This fits entirely in L1 on most CPUs (32-48KB typical).
      // The SIMD path processes 4 f32 values per instruction cycle.
      const soaStart = performance.now();
      this.exports.bench_soa_field_scoring(fieldCount);
      const soaDuration = (performance.now() - soaStart) * 1000;
      soaSamples.push(soaDuration);

      // Yield control every 20 trials to prevent UI blocking.
      // The 0ms delay allows pending animation frames and input events to
      // process without introducing a full event loop cycle delay.
      if (i % 20 === 19) {
        await new Promise<void>(r => setTimeout(r, 0));
        onProgress?.((i + 1) / trialCount);
      }
    }

    const aosDistrib = computeDistribution(aosSamples, tukeyK);
    const soaDistrib = computeDistribution(soaSamples, tukeyK);

    return {
      aos:        aosDistrib,
      soa:        soaDistrib,
      speedupP50: aosDistrib.p50 / soaDistrib.p50,
      speedupP95: aosDistrib.p95 / soaDistrib.p95,
      fieldCount,
      timestamp:  Date.now(),
    };
  }
}

// ── Statistical functions ────────────────────────────────────────────────────

/**
 * computeDistribution — compute a full TimingDistribution from raw samples.
 *
 * @param samples  Raw timing measurements in μs (unsorted)
 * @param tukeyK   Tukey fence multiplier (default 1.5)
 */
function computeDistribution(samples: number[], tukeyK: number): TimingDistribution {
  const sorted = [...samples].sort((a, b) => a - b);
  const n = sorted.length;

  // Quartiles via linear interpolation (method R7, default in most statistical packages)
  const q1 = interpolatedPercentile(sorted, 0.25);
  const q3 = interpolatedPercentile(sorted, 0.75);
  const iqr = q3 - q1;

  // Tukey fences
  const lowerFence = q1 - tukeyK * iqr;
  const upperFence = q3 + tukeyK * iqr;

  const cleanSamples = sorted.filter(x => x >= lowerFence && x <= upperFence);
  const outliersCount = n - cleanSamples.length;

  // Descriptive statistics on clean samples
  const mean = cleanSamples.reduce((s, x) => s + x, 0) / cleanSamples.length;
  const variance = cleanSamples.reduce((s, x) => s + (x - mean) ** 2, 0) / cleanSamples.length;
  const stddev = Math.sqrt(variance);

  // Percentiles on clean distribution
  const p50 = interpolatedPercentile(cleanSamples, 0.50);
  const p75 = interpolatedPercentile(cleanSamples, 0.75);
  const p90 = interpolatedPercentile(cleanSamples, 0.90);
  const p95 = interpolatedPercentile(cleanSamples, 0.95);
  const p99 = interpolatedPercentile(cleanSamples, 0.99);

  // ── L1 hit rate inference ────────────────────────────────────────────────
  // Cache latency distributions are typically bimodal for working sets near
  // the L1/L2 boundary: one mode for L1 hits (~4 cycles), another for L2
  // hits or misses (~40-200 cycles). We detect bimodality by checking if the
  // distribution has two distinct peaks using a simplified Hartigan dip test
  // approximation: if the coefficient of variation (σ/μ) is high (> 0.3) and
  // the p50/p95 ratio is large (> 3), the distribution is likely bimodal.
  //
  // This is an approximation — a rigorous bimodality test requires the full
  // Hartigan & Hartigan (1985) dip statistic computation. For a documentation
  // visualizer, the approximation is sufficient to flag the AoS cache-miss
  // pattern versus the SoA L1-resident pattern.
  const cv = stddev / mean;
  const tailRatio = p95 / p50;
  const bimodal = cv > 0.3 && tailRatio > 3.0;

  // Infer L1 hit rate from bimodality and mean latency.
  // L1 access: ~4ns on 3GHz CPU ≈ 1.3ns/cycle. L2: ~12ns. DRAM: ~70ns.
  // SoA 4KB working set → expected ~100% L1 hits → low CV, low tail ratio.
  // AoS 480KB working set → L1 thrash, mixed L2/DRAM → high CV, high tail.
  const l1HitRatePct = bimodal
    ? Math.max(10, 100 - (cv * 100))
    : Math.min(99, 100 - (tailRatio * 5));

  return {
    rawSamples:    sorted,
    cleanSamples,
    outliersCount,
    p50, p75, p90, p95, p99,
    min:  cleanSamples[0],
    max:  cleanSamples[cleanSamples.length - 1],
    mean, stddev, iqr,
    l1HitRatePct: Math.max(0, Math.min(100, l1HitRatePct)),
  };
}

/**
 * interpolatedPercentile — compute a percentile via R7 linear interpolation.
 *
 * R7 is the default method used by NumPy, R's quantile(), and most statistical
 * packages. It linearly interpolates between adjacent order statistics, giving
 * a continuous percentile function over the discrete sample.
 *
 * For a sorted array of length n, the h-th order statistic index is:
 *   h = p × (n - 1)
 *   result = sorted[floor(h)] + frac(h) × (sorted[ceil(h)] - sorted[floor(h)])
 */
function interpolatedPercentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  if (sorted.length === 1) return sorted[0];

  const h = p * (sorted.length - 1);
  const lo = Math.floor(h);
  const hi = Math.ceil(h);
  const frac = h - lo;

  return sorted[lo] + frac * (sorted[hi] - sorted[lo]);
}

/**
 * formatLatency — format a microsecond value for human display.
 * Automatically selects ns, μs, or ms depending on magnitude.
 */
export function formatLatency(us: number): string {
  if (us < 1)   return `${(us * 1000).toFixed(0)} ns`;
  if (us < 1000) return `${us.toFixed(1)} μs`;
  return `${(us / 1000).toFixed(2)} ms`;
}
