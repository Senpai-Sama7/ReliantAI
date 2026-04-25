# reGenesis — User Manual

## 0) Purpose

Generate brand-driven static sites with AI. Replicate live sites to a local copy with integrity tracking. Verify assets. Ship accessible UI primitives.

---

## 1) System requirements

* OS: macOS, Linux, or WSL2 on Windows.
* Node.js 20 or newer.
* Disk: 5–10 GB free for replicas and screenshots.
* For image conversion: CPU with AVX2 (your CPU has it).
* Low-power setup (your laptop): use `--pageConcurrency 2`, `--domainAssetConcurrency 2`, `--baseAssetConcurrency 5`.

---

## 2) Install

```bash
# clone your repo
git clone https://github.com/Senpai-Sama7/reGenesis.git
cd reGenesis

# install root deps
npm i
```

Optional per-package installs (build token packages if you will import them elsewhere):

```bash
npm run build:tokens
```

---

## 3) Folder tour

```
tools/
  generate.mjs       # AI generator (brand brief → index.html + motion.css)
  replicator.js      # website replicate/verify CLI
packages/
  design-tokens/     # DTCG tokens → CSS vars + TS export
  motion-tokens/     # motion tokens → CSS vars
  ui/                # SkipLink and minimal UI primitives
  scroll/            # smooth scroll helper
apps/
  site-example/      # Next app that can serve generated output
tests/               # unit + CLI tests
e2e/                 # Playwright e2e
```

---

## 4) Quick starts

### A) Generate a website from a brand brief

1. Set your API key:

```bash
export GEMINI_API_KEY=YOUR_GEMINI_KEY
```

2. Prepare a brief (see §6).
3. Run:

```bash
node tools/generate.mjs \
  --brief ./brand-brief.example.json \
  --outputDir ./apps/site-example/public/generated \
  --force
```

4. Result files:

```
apps/site-example/public/generated/index.html
apps/site-example/public/generated/motion.css
```

5. Preview in the example app (optional):

```bash
cd apps/site-example
npm i
npm run dev
# open http://localhost:3000 and route to your generated HTML if wired
```

### B) Replicate a live website

1. Pick a target domain that you own or are authorized to archive.
2. Run replicate:

```bash
node tools/replicator.js replicate https://example.com ./replicas/example \
  --depth 2 \
  --pageConcurrency 2 \
  --baseAssetConcurrency 6 \
  --domainAssetConcurrency 2 \
  --responsive true \
  --brotli true
```

3. Artifacts:

```
./replicas/example/manifest.json
./replicas/example/** (HTML, CSS, JS, images, optional .br files)
```

### C) Verify integrity later

```bash
node tools/replicator.js verify ./replicas/example
# prints counts: total, ok, bad
```

---

## 5) Command reference

### Generator: `tools/generate.mjs`

Required:

* `--brief <path>`: JSON brief file.
* `--outputDir <dir>`: output folder.

Optional:

* `--model <name>`: default `gemini-2.0-flash`.
* `--timeout <ms>`: default `30000`.
* `--dry-run`: prints plan but writes nothing.
* `--force`: overwrite existing files.

Examples:

```bash
# fast dry-run check
node tools/generate.mjs --brief ./brief.json --outputDir ./out --dry-run

# change model and timeout
node tools/generate.mjs --brief ./brief.json --outputDir ./out --model gemini-1.5-flash --timeout 45000 --force
```

### Replicator: `tools/replicator.js`

Subcommands:

* `replicate <url> [outputDir]`
* `verify <outputDir>`

Flags for `replicate`:

* `--depth <n>`: crawl depth from entry. Default `2`.
* `--incremental`: respect previous `manifest.json` via ETag/Last-Modified. Default `false`.
* `--responsive`: take screenshots at defined breakpoints. Default `false`.
* `--brotli`: store text assets as `.br`. Default `false`.
* `--pageConcurrency <n>`: concurrent pages. Default `4`.
* `--baseAssetConcurrency <n>`: same-origin assets concurrency. Default `10`.
* `--domainAssetConcurrency <n>`: third-party domain concurrency. Default `3`.

Examples:

```bash
# minimal crawl
node tools/replicator.js replicate https://docs.example.org ./replicas/docs --depth 1

# low-resource friendly
node tools/replicator.js replicate https://example.com ./replicas/example \
  --depth 2 --pageConcurrency 2 --baseAssetConcurrency 5 --domainAssetConcurrency 2

# incremental daily job
node tools/replicator.js replicate https://example.com ./replicas/daily --incremental true
```

---

## 6) Brand brief format (generator input)

### Schema constraints

* `brand.name` (string)
* `brand.voice` ∈ `calm | energetic | premium | playful | tech`
* `identity.colors`: `bg`, `fg`, `accent`, `muted` (hex or CSS color)
* `identity.typography.display.family`, `identity.typography.text.family`
* `identity.density` ∈ `compact | comfortable | spacious`
* `motion.personality` ∈ `subtle | standard | expressive`
* `contentModel`: array of sections. Each item:

  * `intent`: e.g., `hero`, `feature-grid`, `testimonial`, `cta`, etc.
  * `payload`: intent-specific fields.

### Minimal working example

```json
{
  "brand": { "name": "Acme Quantum", "voice": "tech" },
  "identity": {
    "colors": { "bg": "#0b1220", "fg": "#e6edf7", "accent": "#4da3ff", "muted": "#122034" },
    "typography": { "display": { "family": "Inter" }, "text": { "family": "Inter" } },
    "density": "comfortable"
  },
  "motion": { "personality": "standard" },
  "contentModel": [
    { "intent": "hero", "payload": { "heading": "Faster inference. Lower cost.", "kicker": "Acme Quantum", "cta": {"href": "#cta", "label": "Get started"} } },
    { "intent": "feature-grid", "payload": { "items": [
      {"title":"Latency","body":"p95 under 150ms"},
      {"title":"Cost","body":"Run 40% cheaper"},
      {"title":"Security","body":"SOC2 ready"}
    ] } },
    { "intent": "testimonial", "payload": { "quote": "Cut infra spend in half.", "author": "Dana Li, CTO" } },
    { "intent": "cta", "payload": { "heading": "Ship today", "button": {"href":"#","label":"Start free"} } }
  ]
}
```

### Tips

* Keep headings short. Use sentence case.
* Use real copy. No lorem ipsum.
* If you want zero motion for regulated contexts, set `motion.personality` to `subtle` and later remove any fade-ins in your CSS, or honor system `prefers-reduced-motion`.

---

## 7) When to use Generator vs Replicator

* Use **Generator** for net-new brand pages or controlled refreshes.
* Use **Replicator** to archive your own site, migrate static content, or capture a microsite for analysis.
* Do not replicate third-party sites without permission. See §12.

---

## 8) Performance tuning

### Generator

* Model choice: `gemini-2.0-flash` is fast. Heavier models may improve layout semantics but cost more.
* Use `--timeout 45000` on slow networks.

### Replicator on low CPU/RAM

* Start: `--pageConcurrency 2 --baseAssetConcurrency 5 --domainAssetConcurrency 2`.
* Turn off screenshots: `--responsive false`.
* Turn off AVIF: set env `CA_ENABLE_AVIF=0` if you modify code to read it; current default converts images when fetched but is efficient. If CPU spikes, reduce crawl depth.
* Prefer `--incremental` for repeat runs.

### Asset choices

* `--brotli true` saves disk on text. Requires serving with correct headers later.
* AVIF yields smallest images; WebP is faster to encode. The replicator auto-converts images it downloads; for lossless archival, fork and disable conversion in `getOptimizationStream`.

---

## 9) Testing

### Unit + CLI

```bash
npm test
```

Covers path mapping, HTML/CSS URL rewriting, and CLI verify behavior.

### End-to-end

```bash
npx playwright install --with-deps
npm run test:e2e
```

E2E runs a dry-run of the generator and asserts sane errors without API keys.

Add more:

* Lighthouse CI for perf budgets.
* `axe-core` for automated accessibility checks.

---

## 10) CI/CD example (GitHub Actions)

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci || npm i
      - run: npm run build:tokens
      - run: npm run test
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
```

---

## 11) Troubleshooting

### Generator fails with “GEMINI\_API\_KEY is required”

Set the environment variable first:

```bash
export GEMINI_API_KEY=... # your key
```

### Generator returns HTTP error

* Wrong model name or expired key.
* Network blocked by corporate proxy. Try on another network or configure proxy.

### Replicator exits on missing system libraries (Linux)

Install Chromium deps:

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y \
  libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 \
  libxcomposite1 libxrandr2 libxdamage1 libpango-1.0-0 libcairo2 \
  libasound2 libxshmfence1
```

### Sharp install problems on Windows

Use WSL2 Ubuntu. Or install prebuilt sharp by ensuring Node 20 and recent npm, then reinstall:

```bash
npm rebuild sharp
```

### Crawl too slow or throttled

Lower `--pageConcurrency` to 1–2. Increase only if the target allows.

### Assets missing after verify

Look for `missing` lines in `verify`. Recrawl without `--incremental`. Increase `--depth` if links were deeper.

### HTML looks broken after rewrite

Some apps require their own domain for JS boot. Use replicator for static assets only or disable SPA crawl. Consider an export flow on the source app instead of raw replication.

---

## 12) Legal, safety, and ethics

* Respect `robots.txt` and rate limits.
* Only replicate content you own or have permission to archive.
* Do not store or publish private data captured by mistake.
* Honor `prefers-reduced-motion` to avoid motion-triggered discomfort.
* For customer data, run the generator on sanitized briefs only. No PII.

---

## 13) Deployment notes

* Serve `.html`, `.css`, `.js` with correct `Content-Type`.
* If you enabled Brotli, configure the server to map `*.br` with `Content-Encoding: br` and `Vary: Accept-Encoding`.
* Cache policy:

  * HTML: `Cache-Control: max-age=60, must-revalidate`.
  * Static assets: `Cache-Control: public, max-age=31536000, immutable`.

---

## 14) FAQs

**Q: Do I need the example Next app to use generated files?**
A: No. Any static host works. The app is a convenient viewer.

**Q: Can I use my own fonts?**
A: Yes. Set families in the brief. The generator will reference them. Self-host if needed.

**Q: Does the replicator copy forms or server code?**
A: No. It captures client-side assets only.

**Q: Can I keep originals without image conversion?**
A: Fork and remove the conversion branch in `getOptimizationStream`. Then recrawl.

**Q: Will replication keep my SEO meta?**
A: Yes. The HTML is saved after rewrite. Verify with your own checks.

---

## 15) Glossary (plain language)

* **Monorepo**: one Git repository with many packages and apps inside. Easier sharing.
* **Package**: a folder that can be published or imported. Has its own `package.json`.
* **CLI**: command-line tool. You run it in a terminal.
* **Environment variable**: a named value visible to programs. Example: `GEMINI_API_KEY`.
* **Generator**: the tool that asks an AI to output HTML and CSS from a brand brief.
* **Brand brief**: a JSON file that describes colors, fonts, tone, and page sections.
* **Schema**: a set of rules a JSON file must follow. The generator checks it first.
* **DTCG tokens**: a standard way to store design values like colors and spacing.
* **Motion tokens**: design values for animation timing and easing.
* **Replicator**: the tool that downloads pages and assets from a site you control.
* **Crawl depth**: how many link levels from the starting page to follow.
* **robots.txt**: a file on a website that tells crawlers what they may fetch.
* **sitemap.xml**: a file listing pages on the site to help crawlers find them.
* **Brotli**: a compression method that makes text files smaller.
* **AVIF/WebP**: modern image formats that are smaller than JPEG/PNG.
* **Integrity hash**: a fingerprint (SHA-256) of a file to check if it changed.
* **Manifest**: a JSON list of saved files and their metadata.
* **Incremental**: only fetch what changed since the last run.
* **Concurrency**: how many things happen at once. Too high can get you blocked.
* **Headless browser**: Chrome that runs without a window. Used for crawling.
* **Viewport**: the browser window size used while crawling or screenshotting.
* **ETag / Last-Modified**: server hints that tell if a file changed.
* **304 Not Modified**: response meaning your local copy is still current.
* **IntersectionObserver**: browser feature to detect when elements enter the screen.
* **WCAG**: accessibility rules to help all users, including keyboard and screen readers.

---

## 16) Word key (synonyms)

* **Replicate** = crawl, archive, mirror.
* **Generate** = synthesize, create, render.
* **Brief** = spec, configuration, plan.
* **Tokens** = variables, design values.
* **Integrity** = checksum, hash match.
* **Concurrency** = parallelism, simultaneous tasks.
* **Headless** = no GUI, background browser.
* **Compression** = shrinking files, smaller size.

---

## 17) Checklists

### Pre-run checklist

* Node 20+ installed.
* Disk space available.
* API key set (for generator).
* Permission to crawl the target domain (for replicator).

### Post-run checklist

* `verify` returns `bad: 0`.
* Visual spot check a few pages.
* Publish with correct `Content-Type` and `Content-Encoding` headers.

---

## 18) Non-technical paths

### I only want a branded landing page

1. Copy the minimal brief from §6.
2. Edit brand name, colors, texts.
3. Run the generator command in §4A.
4. Upload the `generated` folder to your web host.

### I only want a copy of my current site

1. Use the replicate command in §4B with your domain.
2. Wait until complete.
3. Run `verify`.
4. Open the saved `index.html` files locally to review.

---

## 19) Next steps

* Hand me your real brand brief and target allowlist. I will provide locked defaults and tuned flags.
* If you want me to output this guide as `docs/USER_MANUAL.md`, say so.
