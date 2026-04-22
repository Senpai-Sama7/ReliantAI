# CyberArchitect - Agent Guide

**Last updated:** 2026-03-05

## Project Overview

CyberArchitect is a robust, high-performance Node.js toolkit for comprehensive website replication, archiving, and analysis. It emphasizes resilience, efficiency, and respectful crawling of modern web applications.

**Key Capabilities:**
- True streaming pipeline (assets stream directly to disk)
- Optional Brotli compression
- Optimized image/SVG handling (AVIF/WebP conversion)
- Per-domain concurrency limits and circuit breakers
- Intelligent SPA crawling with cycle detection
- sitemap.xml discovery
- Incremental replication with ETag/Last-Modified

**Architecture Pattern:**
```
┌─────────────────────────────────────────────────────────┐
│  Replication Engine                                     │
│  ├── Streaming pipeline (network → disk)               │
│  ├── Per-domain circuit breakers                       │
│  └── Exponential backoff with jitter                   │
├─────────────────────────────────────────────────────────┤
│  Asset Processing                                       │
│  ├── Image optimization (AVIF/WebP)                    │
│  ├── SVG minification                                  │
│  ├── CSS/HTML minification                             │
│  └── Brotli compression (optional)                     │
├─────────────────────────────────────────────────────────┤
│  Crawling Intelligence                                  │
│  ├── sitemap.xml discovery                             │
│  ├── SPA simulation (user interactions)                │
│  ├── robots.txt compliance                             │
│  └── Lazy 404 caching                                  │
└─────────────────────────────────────────────────────────┘
```

---

## Build / Run / Test Commands

### Installation
```bash
# Install dependencies (Chromium downloaded automatically)
npm install

# Verify installation
node replicator.js --help
```

### Replication Commands
```bash
# Basic replication
node replicator.js replicate https://example.com ./my-replica

# Deep crawl + responsive screenshots
node replicator.js replicate https://myspa.com ./spa-archive --depth 3 --responsive

# Incremental update with Brotli
node replicator.js replicate https://myblog.com ./blog-update --incremental --brotli

# Fine-tuned concurrency
node replicator.js replicate https://complex-site.com ./complex \
  --pageConcurrency 2 \
  --baseAssetConcurrency 15 \
  --domainAssetConcurrency 5
```

### Verification
```bash
# Verify replica integrity
node replicator.js verify ./my-replica

# Shows SHA-256 hash validation for all assets
```

### CLI Help
```bash
# Full help
node replicator.js --help

# Command-specific help
node replicator.js replicate --help
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Runtime** | Node.js 18+ | JavaScript execution |
| **Browser** | Puppeteer | Headless Chrome for rendering |
| **CLI** | yargs | Professional command-line interface |
| **Logging** | pino | Structured JSON logging |
| **Compression** | zlib (Brotli) | Asset compression |
| **Image Processing** | sharp | AVIF/WebP conversion |
| **HTML Parsing** | cheerio | Server-side DOM manipulation |
| **Concurrency** | p-limit | Rate limiting per domain |

---

## Project Structure

```
CyberArchitect/
├── ultimate-website-replicator.js    # Main replicator (30KB+)
├── README.md                         # User documentation
└── package.json                      # Dependencies

# Runtime outputs (created on run)
./my-replica/
├── index.html                        # Entry point
├── assets/                           # Downloaded assets
├── css/                              # Stylesheets
├── js/                               # JavaScript files
├── images/                           # Optimized images
└── .replication-manifest.json        # Integrity manifest
```

---

## Critical Code Patterns

### Circuit Breaker Per Domain
```javascript
// Circuit breakers isolate failures per domain
const circuitBreakers = new Map();

function getCircuitBreaker(domain) {
  if (!circuitBreakers.has(domain)) {
    circuitBreakers.set(domain, new CircuitBreaker({
      failureThreshold: 5,
      resetTimeout: 60000
    }));
  }
  return circuitBreakers.get(domain);
}
```

### Streaming Asset Pipeline
```javascript
// Assets stream directly to disk (no memory buffering)
const response = await fetch(assetUrl);
const fileStream = fs.createWriteStream(localPath);

await pipeline(
  response.body,
  brotliCompress(),  // Optional compression
  fileStream
);
```

### Exponential Backoff with Jitter
```javascript
// Prevents thundering herd on recovery
function calculateDelay(attempt) {
  const base = Math.pow(2, attempt) * 1000;  // Exponential
  const jitter = Math.random() * 1000;        // Randomness
  return Math.min(base + jitter, 60000);      // Cap at 60s
}
```

### Lazy 404 Caching
```javascript
// Don't retry URLs that consistently 404
const notFoundCache = new Set();

async function fetchAsset(url) {
  if (notFoundCache.has(url)) {
    return { status: 'skipped', reason: 'cached-404' };
  }
  
  try {
    const response = await fetch(url);
    if (response.status === 404) {
      notFoundCache.add(url);
    }
    return response;
  } catch (err) {
    // Retry logic...
  }
}
```

---

## Non-Obvious Gotchas

### 1. Single-File Architecture
The entire replicator is in `ultimate-website-replicator.js` (30KB+). This is intentional:
- Self-contained, no complex module structure
- Easy to understand and modify
- All logic in one place

### 2. Chromium Download on Install
Puppeteer downloads Chromium on `npm install`:
- ~100MB download
- Required for JavaScript execution
- Can be skipped with `PUPPETEER_SKIP_DOWNLOAD=true` (limited functionality)

### 3. Per-Domain Concurrency Limits
Different limits for different resource types:
```javascript
--pageConcurrency 2        // Simultaneous page crawls
--baseAssetConcurrency 15  // CSS/JS from main domain
--domainAssetConcurrency 5 // Assets from CDNs
```

This prevents hammering any single host while maximizing throughput.

### 4. Integrity Manifest Format
```json
{
  "generated": "2024-03-05T12:00:00Z",
  "source": "https://example.com",
  "assets": {
    "index.html": {
      "hash": "sha256:a1b2c3...",
      "size": 15320,
      "contentType": "text/html"
    }
  }
}
```

Use `verify` command to check against this manifest.

### 5. SPA Crawling Simulation
For SPAs, the tool simulates user interactions:
- Clicks navigation links
- Waits for dynamic content
- Detects infinite scroll patterns
- Handles client-side routing

This requires Puppeteer's full browser, not just HTTP requests.

### 6. robots.txt Compliance
The tool respects robots.txt:
- Parses crawl-delay directives
- Respects Disallow patterns
- Identifies itself with User-Agent

But: You can override with `--ignore-robots` (use responsibly).

### 7. Memory Monitoring
Built-in memory monitoring with optional GC:
```bash
node --expose-gc replicator.js replicate ...
```

Triggers garbage collection when memory pressure detected.

### 8. Incremental Replication
Uses HTTP caching headers:
- Sends `If-None-Match` (ETag)
- Sends `If-Modified-Since`
- Skips unchanged assets
- Updates manifest accordingly

---

## CLI Reference

### Global Options
```bash
--help, -h          Show help
--version, -v       Show version
--verbose           Enable debug logging
--quiet             Suppress non-error output
```

### Replicate Command
```bash
node replicator.js replicate <url> [outputDir] [options]

Options:
  --depth <n>                    Crawl depth (default: 2)
  --responsive                   Capture responsive screenshots
  --incremental                  Update only changed assets
  --brotli                       Enable Brotli compression
  --pageConcurrency <n>          Page crawl concurrency (default: 3)
  --baseAssetConcurrency <n>     Asset concurrency for base domain (default: 10)
  --domainAssetConcurrency <n>   Asset concurrency for other domains (default: 5)
  --ignore-robots                Ignore robots.txt (not recommended)
```

### Verify Command
```bash
node replicator.js verify <outputDir>

Re-hashes all local files and validates against manifest.
Reports mismatches, missing files, and extra files.
```

---

## Usage Examples

### Backup a Static Site
```bash
node replicator.js replicate https://docs.example.com ./docs-backup --depth 1
```

### Archive a Complex SPA
```bash
node replicator.js replicate https://app.example.com ./app-archive \
  --depth 3 \
  --responsive \
  --pageConcurrency 1 \
  --brotli
```

### Incremental Update
```bash
# First run - full replication
node replicator.js replicate https://blog.example.com ./blog --depth 2

# Later - only update changed content
node replicator.js replicate https://blog.example.com ./blog --incremental
```

### Verify Archive Integrity
```bash
node replicator.js verify ./my-archive
# Output: ✓ 150/150 assets validated
#         ✗ 3 files modified (show details)
```

---

## Performance Tuning

### For Large Sites (>10k pages)
```bash
node replicator.js replicate https://huge-site.com ./archive \
  --pageConcurrency 1 \        # Be polite
  --domainAssetConcurrency 3 \
  --brotli                     # Save disk space
```

### For Fast Archival
```bash
node replicator.js replicate https://fast-site.com ./archive \
  --pageConcurrency 5 \
  --baseAssetConcurrency 20 \
  --depth 1                    # Shallow crawl
```

---

## Troubleshooting

### Chromium Download Issues
```bash
# If Chromium fails to download
export PUPPETEER_DOWNLOAD_HOST=https://npm.taobao.org/mirrors
npm install
```

### Memory Issues
```bash
# Enable garbage collection
node --max-old-space-size=4096 --expose-gc replicator.js replicate ...
```

### Network Timeouts
```bash
# Increase timeouts
node replicator.js replicate ... --timeout 60000 --retry 5
```

---

## Reference

See root `AGENTS.md` for:
- Core commandments (integration build rules)
- Mode-specific guidelines
- Universal patterns across all ReliantAI projects
