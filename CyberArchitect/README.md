# CyberArchitect

## The Ultimate Website Replication Suite — Professional‑Grade Edition

[![Node.js Version](https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen)](#)
[![License](https://img.shields.io/badge/License-MIT-yellow)](#)
[![Powered by Puppeteer](https://img.shields.io/badge/powered%20by-Puppeteer-blue)](#)

---
**CyberArchitect** is a robust, high‑performance Node.js toolkit for comprehensive website replication, archiving, and analysis. Built with professional workflows in mind, it emphasizes resilience, efficiency, and respectful crawling of modern web applications.
---

### ✨ Key Features

#### 🚀 Core Replication & Performance

* **True streaming pipeline** – assets stream directly from the network to disk, minimizing RAM.
* **Optional Brotli compression** – shrink HTML, CSS, and JS to save disk space and bandwidth.
* **Optimized image & SVG handling** – on‑the‑fly AVIF/WebP conversion and SVG minification.
* **CSS & HTML minification** – lean, production‑ready output.

#### 🛡️ Network Resilience & Control

* **Per‑domain concurrency limits** – avoid hammering any single host.
* **Per‑domain circuit breakers** – isolate failures; a downed CDN won’t block the main site.
* **Exponential back‑off with jitter** – intelligent retries for transient errors.
* **Lazy 404 caching** – skip repeatedly missing assets.

#### 🧠 Advanced Crawling & Discovery

* **`sitemap.xml` discovery** – automatically harvest hidden URLs.
* **Intelligent SPA crawling** – simulates user interactions and detects cycles.
* **Robots.txt compliance** – ethical, spec‑compliant crawling.

#### 🔄 Integrity & Auditing

* **Incremental replication (`--incremental`)** – update only what changed using ETag & Last‑Modified.
* **Integrity manifest** – SHA‑256 hashes for every asset.
* **`verify` command** – re‑hash local files and validate against the manifest.

#### 🛠️ Developer Experience

* **Professional CLI** powered by *yargs* (`replicate`, `verify`, `--help`).
* **Structured logging** with *pino*.
* **Memory monitoring** with optional GC triggers (`--expose-gc`).
* **Cross‑platform compatibility** – automatic `fetch` polyfill for Node 16.

---

### 📦 Installation

#### Prerequisites

* Node.js **≥ 18**
* npm

```bash
# Clone the repository
git clone https://github.com/Senpai-sama7/CyberArchitect.git
cd CyberArchitect

# Install dependencies (Chromium is downloaded automatically)
npm install
```

---

### 🚀 Usage

#### Replicate a website

```bash
node replicator.js replicate <url> [outputDir] [options]
```

Examples:

```bash
# Basic replication
node replicator.js replicate https://example.com ./my‑replica

# Deep crawl + responsive screenshots
node replicator.js replicate https://myspa.com ./spa‑archive --depth 3 --responsive

# Incremental update with Brotli
node replicator.js replicate https://myblog.com ./blog‑update --incremental --brotli

# Fine‑tuned concurrency
node replicator.js replicate https://complex‑site.com ./complex --pageConcurrency 2 --baseAssetConcurrency 15 --domainAssetConcurrency 5
```

#### Verify a replica

```bash
node replicator.js verify <outputDir>
# e.g.
node replicator.js verify ./my‑replica
```

#### Get help

```bash
node replicator.js --help
node replicator.js replicate --help
```

---

### ⚙️ Configuration Options (CLI flags)

| Option                     | Type    | Default             | Description                                           |
| -------------------------- | ------- | ------------------- | ----------------------------------------------------- |
| `<url>`                    | string  | **required**        | Target URL to replicate                               |
| `[outputDir]`              | string  | `./replicated‑site` | Output directory                                      |
| `--depth`                  | number  | `2`                 | Max crawl depth for SPA crawling (0 = main page only) |
| `--pageConcurrency`        | number  | `4`                 | Concurrent browser pages                              |
| `--baseAssetConcurrency`   | number  | `10`                | Concurrent asset downloads on main domain             |
| `--domainAssetConcurrency` | number  | `3`                 | Concurrent asset downloads per external domain        |
| `--incremental`            | boolean | `false`             | Incremental updates using ETag/Last‑Modified          |
| `--brotli`                 | boolean | `false`             | Enable Brotli compression                             |
| `--crawlSPA`               | boolean | `true`              | Enable SPA crawling                                   |
| `--respectRobotsTxt`       | boolean | `true`              | Obey robots.txt                                       |
| ...                        |         |                     | *(see `--help` for the full list)*                    |

---

### 💡 Advanced Topics

#### Incremental replication

When `--incremental` is enabled CyberArchitect loads the existing `manifest.json`, re‑validates assets with `If‑None‑Match`/`If‑Modified‑Since`, and downloads only what changed.

#### Domain‑based concurrency

`--baseAssetConcurrency` and `--domainAssetConcurrency` ensure fair use of network resources by throttling each host independently.

#### Brotli compression

With `--brotli`, HTML/CSS/JS are stored as `.br` files. Configure your web server to serve these when the client advertises `Accept‑Encoding: br`.

---

### 🤝 Contributing

Pull requests and feature ideas are welcome—check the issue tracker first to avoid duplication.

### 📄 License

CyberArchitect is released under the **MIT License**.
