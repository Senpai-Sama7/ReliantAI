// astro.config.mts
//
// Astro configuration for the Nexus Executable Topology Specification.
//
// ─── INTEGRATION RATIONALE ──────────────────────────────────────────────────
//
// @astrojs/react — Required for the visualization islands. Astro's island
// architecture delivers React components as isolated, independently-hydrated
// chunks. The `client:visible` directive used in the MDX routes defers
// component hydration until the island enters the viewport, matching the
// lazy-loading architecture described in the specification.
//
// @astrojs/mdx — Enables .mdx files in src/content/docs/. MDX compiles
// to an Astro component, meaning JSX expressions in documentation files
// are executed at build time (for static content) or at runtime (for
// islands). The visualization components are runtime islands — they are
// not executed during the Astro build, only when the user's browser loads
// and the IntersectionObserver fires.
//
// ─── VITE WASM CONFIGURATION ────────────────────────────────────────────────
//
// WASM files require special handling in the Vite bundler:
//
//   1. ?url import suffix: Vite's default behavior inlines small binary
//      assets as base64 data URIs. WASM binaries are too large for this
//      and require the streaming instantiation path (WebAssembly.instantiateStreaming),
//      which only accepts a Response object from fetch() — not a data URI.
//      The `?url` suffix tells Vite to emit the file to the output directory
//      and return its public URL, which we pass to fetch().
//
//   2. assetsInclude: Ensures Vite treats .wasm as a static asset even
//      when imported without the `?url` suffix (belt-and-suspenders).
//
//   3. optimizeDeps.exclude: Prevents Vite's dependency pre-bundling from
//      attempting to parse WASM modules as CommonJS/ESM. WASM is not a
//      JavaScript module — pre-bundling would corrupt the binary.
//
//   4. worker.format: "es" — Web Workers in the visualization islands
//      use ES module syntax. The Worker constructor's `{ type: "module" }`
//      option requires this. Bundling Workers as "iife" would require
//      importScripts() instead of import(), breaking the ES module WASM
//      instantiation pattern.
//
// ─── CONTENT COLLECTIONS ────────────────────────────────────────────────────
//
// The docs/ route is served from src/content/docs/ as an Astro content
// collection. This enables:
//   - Type-safe frontmatter validation via a Zod schema
//   - Automatic slug generation from file paths
//   - Integration with Astro's getCollection() API for generating navigation
//
// The `synchronization.mdx` file in that directory mounts the visualization
// island via a standard MDX component import — no special Astro configuration
// is required beyond enabling the MDX integration.

import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import mdx from "@astrojs/mdx";

export default defineConfig({
  integrations: [
    react(),
    mdx(),
  ],

  // Astro's output mode.
  // "static" produces pre-rendered HTML for all non-island content.
  // The islands (client:*) produce a minimal JS bundle per component,
  // loaded only when hydration conditions are met.
  output: "static",

  // The docs site is served at /docs/ — adjust to "/" for root deployment.
  base: "/",

  vite: {
    // ── WASM asset handling ─────────────────────────────────────────────
    assetsInclude: ["**/*.wasm"],

    optimizeDeps: {
      // Prevent Vite from attempting to CommonJS-wrap the WASM module.
      // wasm-pack generates an ES module glue file that handles instantiation;
      // pre-bundling it strips the top-level await that wasm-pack relies on.
      exclude: ["nexus-engine"],
    },

    build: {
      // Prevent Vite from inlining the WASM binary as a base64 data URI.
      // WebAssembly.instantiateStreaming() requires a fetch() Response —
      // it cannot accept a data: URI. Inlining would force fallback to
      // the slower WebAssembly.instantiate(arrayBuffer) path.
      assetsInlineLimit: 0,

      rollupOptions: {
        output: {
          // Ensure the WASM file retains a deterministic output name.
          // Content hashing is still applied — this just preserves the
          // human-readable prefix for debugging.
          assetFileNames: (assetInfo) => {
            if (assetInfo.name?.endsWith(".wasm")) {
              return "wasm/[name].[hash][extname]";
            }
            return "assets/[name].[hash][extname]";
          },
        },
      },
    },

    worker: {
      // ES module Workers are required for top-level await and dynamic
      // import() within the Worker scope. The WASM loading pattern:
      //   const { instance } = await WebAssembly.instantiateStreaming(fetch(...))
      // uses top-level await, which is only valid in module-type Workers.
      format: "es",
    },

    server: {
      // Vite dev server header injection.
      // These headers replicate the production Bun server's COOP/COEP
      // configuration, ensuring SharedArrayBuffer works during development
      // without running the production server.
      //
      // Note: Vite's devtools (HMR WebSocket, module overlay) are same-origin,
      // so they are not affected by COEP: require-corp.
      headers: {
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Embedder-Policy": "require-corp",
        "Cross-Origin-Resource-Policy": "same-site",
      },
    },
  },
});
