/**
 * bun-server.ts
 *
 * Entry point for the sovereign_ai documentation and visualization service.
 *
 * The Cross-Origin-Opener-Policy and Cross-Origin-Embedder-Policy headers
 * are not optional configuration — they are the security prerequisite that
 * causes the browser's process model to grant access to SharedArrayBuffer.
 *
 * Without these headers, `new SharedArrayBuffer(...)` throws a TypeError in
 * all modern browsers regardless of context. This is a deliberate post-Spectre
 * mitigation introduced in browsers circa 2021: SAB enables high-resolution
 * timing via Atomics.wait, which is a Spectre gadget surface if cross-origin
 * content can share memory with a page.
 *
 * COOP: same-origin  → Places the document in its own browsing context group.
 *                       Cross-origin popups and openers cannot share the same
 *                       OS process, eliminating the Spectre cross-process read
 *                       attack surface.
 *
 * COEP: require-corp → Every subresource (scripts, images, iframes) must
 *                       explicitly opt in to cross-origin embedding via either:
 *                       - Cross-Origin-Resource-Policy: cross-origin
 *                       - CORS headers
 *                       Without this, a compromised subresource could read
 *                       the SAB's contents via a Spectre timing channel.
 *
 * The documentation build pipeline requires both. The Astro static output
 * is served through this Bun handler, which attaches the headers to every
 * response. In production (e.g., Vercel/Cloudflare), these headers must be
 * set at the edge configuration layer — the Bun handler documents the contract.
 */

import { serve, file } from "bun";
import { join } from "path";

const DIST_DIR = join(import.meta.dir, "dist");

/**
 * Security header contract for SharedArrayBuffer access.
 * These values are not configurable — any relaxation breaks SAB availability.
 */
const SECURITY_HEADERS = {
  "Cross-Origin-Opener-Policy": "same-origin",
  "Cross-Origin-Embedder-Policy": "require-corp",
  // Resources served from this origin are embeddable by same-site pages.
  // Required so Astro's sub-route navigation doesn't self-block.
  "Cross-Origin-Resource-Policy": "same-site",
  // Prevent MIME-type sniffing, which can reinterpret a WASM binary as
  // something executable in a different context.
  "X-Content-Type-Options": "nosniff",
} as const;

/**
 * WASM binaries require the application/wasm MIME type for the browser to
 * invoke the streaming instantiation fast path (WebAssembly.instantiateStreaming).
 * If served as application/octet-stream, the browser falls back to buffered
 * instantiation, which requires the entire binary to be downloaded before
 * compilation begins — adding 200–800ms to startup on large modules.
 */
const MIME_TYPES: Record<string, string> = {
  ".wasm": "application/wasm",
  ".js":   "text/javascript",
  ".mjs":  "text/javascript",
  ".html": "text/html; charset=utf-8",
  ".css":  "text/css",
  ".json": "application/json",
  ".svg":  "image/svg+xml",
  ".ico":  "image/x-icon",
};

function mimeFor(path: string): string {
  const ext = path.slice(path.lastIndexOf("."));
  return MIME_TYPES[ext] ?? "application/octet-stream";
}

const PORT = parseInt(process.env.PORT ?? "8106");
const HOST = process.env.HOST ?? "0.0.0.0";

serve({
  port: PORT,
  hostname: HOST,

  async fetch(req: Request): Promise<Response> {
    const url = new URL(req.url);
    let pathname = url.pathname;

    // Health check endpoint for Docker
    if (pathname === "/health") {
      return new Response(
        JSON.stringify({ status: "healthy", service: "sovereign-ai" }),
        {
          headers: {
            "Content-Type": "application/json",
            ...SECURITY_HEADERS,
          },
        }
      );
    }

    // Normalize trailing slash to index.html
    if (pathname.endsWith("/")) pathname += "index.html";

    // Attempt direct file serve
    const filePath = join(DIST_DIR, pathname);
    const candidate = file(filePath);

    if (await candidate.exists()) {
      return new Response(candidate, {
        headers: {
          ...SECURITY_HEADERS,
          "Content-Type": mimeFor(pathname),
          // WASM and hashed JS assets can be cached aggressively.
          // HTML documents must not be cached — they contain the Astro
          // island hydration script tags which reference versioned hashes.
          "Cache-Control": pathname.endsWith(".html")
            ? "no-cache"
            : "public, max-age=31536000, immutable",
        },
      });
    }

    // SPA fallback: serve index.html for client-side routes
    const index = file(join(DIST_DIR, "index.html"));
    if (await index.exists()) {
      return new Response(index, {
        status: 200,
        headers: {
          ...SECURITY_HEADERS,
          "Content-Type": "text/html; charset=utf-8",
          "Cache-Control": "no-cache",
        },
      });
    }

    return new Response("Not Found", {
      status: 404,
      headers: SECURITY_HEADERS,
    });
  },
});

console.log(`sovereign-ai running on http://localhost:${PORT}`);
console.log("COOP/COEP headers active — SharedArrayBuffer available");
