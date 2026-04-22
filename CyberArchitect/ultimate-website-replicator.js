/**
 * Ultimate Website Replication Suite - The Professional Grade Edition
 */

// --- Core Dependencies ---
const { EventEmitter } = require('events');
const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const { URL } = require('url');
const crypto = require('crypto');
const { pipeline } = require('stream/promises');
const os = require('os');
const zlib = require('zlib');

// --- Third-Party Libraries ---
const puppeteer = require('puppeteer');
const puppeteerExtra = require('puppeteer-extra');
const puppeteerStealth = require('puppeteer-extra-plugin-stealth');
const cheerio = require('cheerio');
const sharp = require('sharp');
const PQueue = require('p-queue');
const { optimize: optimizeSvg } = require('svgo');
const pino = require('pino');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const robotsParser = require('robots-parser');

// --- Setup & Polyfills ---
// Polyfill fetch for Node.js < 18
if (!globalThis.fetch) {
    try {
        const { fetch, Request, Response, Headers } = require('undici');
        globalThis.fetch = fetch;
        globalThis.Request = Request;
        globalThis.Response = Response;
        globalThis.Headers = Headers;
    } catch (e) {
        console.error("'undici' package not found. Please install it (`npm i undici`) for Node.js versions older than 18.");
        process.exit(1);
    }
}

puppeteerExtra.use(puppeteerStealth());
const logger = pino({ transport: { target: 'pino-pretty' } });

// --- Processors & Utilities ---

class CSSProcessor {
    rewriteUrls(cssContent, urlRewriter) {
        const urlPattern = /url\s*\(\s*(['"]?)([^'")]+?)\1\s*\)/gi;
        return cssContent.replace(urlPattern, (match, quote, originalUrl) => {
            if (originalUrl.startsWith('data:')) return match;
            const rewrittenUrl = urlRewriter(originalUrl);
            return `url(${quote}${rewrittenUrl}${quote})`;
        });
    }

    minify(cssContent) {
        return cssContent
            .replace(/\/\*[\s\S]*?\*\//g, '')
            .replace(/\s+/g, ' ')
            .replace(/;\s*}/g, '}')
            .replace(/,\s+/g, ',')
            .replace(/:\s+/g, ':')
            .trim();
    }
}

class HTMLProcessor {
    constructor() {
        this.urlAttributes = new Map([
            ['img', ['src', 'srcset']], ['source', ['src', 'srcset']],
            ['link', ['href']], ['script', ['src']],
            ['video', ['src', 'poster']], ['audio', ['src']],
            ['iframe', ['src']], ['form', ['action']],
        ]);
    }

    processSrcset(srcsetValue, urlRewriter) {
        if (!srcsetValue) return '';
        return srcsetValue.split(',').map(part => {
            const [url, descriptor] = part.trim().split(/\s+/);
            return `${urlRewriter(url)} ${descriptor || ''}`.trim();
        }).join(', ');
    }

    rewriteUrls(htmlContent, urlRewriter, cssProcessor) {
        const $ = cheerio.load(htmlContent, { decodeEntities: false });

        this.urlAttributes.forEach((attrs, tagName) => {
            $(tagName).each((_, el) => {
                const $el = $(el);
                attrs.forEach(attr => {
                    const originalValue = $el.attr(attr);
                    if (!originalValue) return;

                    if (attr.includes('srcset')) {
                        $el.attr(attr, this.processSrcset(originalValue, urlRewriter));
                    } else {
                        $el.attr(attr, urlRewriter(originalValue));
                    }
                });
            });
        });

        $('[style]').each((_, el) => {
            const $el = $(el);
            const originalStyle = $el.attr('style');
            $el.attr('style', cssProcessor.rewriteUrls(originalStyle, urlRewriter));
        });

        $('style').each((_, el) => {
            const $el = $(el);
            const originalCSS = $el.html();
            $el.html(cssProcessor.rewriteUrls(originalCSS, urlRewriter));
        });

        return $.html();
    }
}

class AdvancedCircuitBreaker extends EventEmitter {
    constructor(options = {}) {
        super();
        this.failureThreshold = options.failureThreshold || 5;
        this.successThreshold = options.successThreshold || 3;
        this.timeout = options.timeout || 30000;
        this.retryTimeoutBase = options.retryTimeoutBase || 1000;
        this.state = 'CLOSED';
        this.failureCount = 0;
        this.successCount = 0;
        this.nextAttempt = Date.now();
    }

    async execute(operation) {
        if (this.state === 'OPEN') {
            if (Date.now() < this.nextAttempt) {
                throw new Error('Circuit breaker is OPEN.');
            }
            this.state = 'HALF_OPEN';
            this.successCount = 0;
        }

        try {
            const result = await Promise.race([
                operation(),
                new Promise((_, reject) => setTimeout(() => reject(new Error('Operation timed out.')), this.timeout))
            ]);
            this.onSuccess();
            return result;
        } catch (error) {
            this.onFailure();
            throw error;
        }
    }

    onSuccess() {
        this.failureCount = 0;
        if (this.state === 'HALF_OPEN') {
            this.successCount++;
            if (this.successCount >= this.successThreshold) {
                this.state = 'CLOSED';
                this.emit('close');
            }
        } else {
            this.state = 'CLOSED';
        }
        this.emit('success');
    }

    onFailure() {
        this.failureCount++;
        if (this.state === 'HALF_OPEN' || this.failureCount >= this.failureThreshold) {
            this.state = 'OPEN';
            const exponent = this.failureCount - this.failureThreshold;
            const waitTime = this.retryTimeoutBase * Math.pow(2, exponent);
            this.nextAttempt = Date.now() + waitTime;
            this.emit('open');
        }
        this.emit('failure');
    }
}


class UltimateWebsiteReplicator extends EventEmitter {
    constructor(options = {}) {
        super();
        this.options = {
            viewport: { width: 1920, height: 1080 },
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            timeout: 60000,
            pageConcurrency: 4,
            baseAssetConcurrency: 10,
            domainAssetConcurrency: 3,
            maxRetries: 3,
            retryDelayBase: 1000,
            incremental: false,
            crawlSPA: true,
            maxCrawlDepth: 2,
            respectRobotsTxt: true,
            optimizeImages: true,
            enableAVIF: true,
            minifyCSS: true,
            captureResponsive: false,
            responsiveBreakpoints: [
                { name: 'mobile', width: 375, height: 812 },
                { name: 'desktop', width: 1920, height: 1080 },
            ],
            enableBrotli: false,
            memoryThreshold: 0.85,
            ...options
        };

        this.pageQueue = new PQueue({ concurrency: this.options.pageConcurrency });
        this.cssProcessor = new CSSProcessor();
        this.htmlProcessor = new HTMLProcessor();

        this.state = {
            browser: null,
            manifest: { assets: {} },
            urlToLocalPath: new Map(),
            crawledUrls: new Set(),
            failedUrls: new Set(),
            robots: null,
            baseUrl: '',
            outputDir: '',
            memoryMonitor: null,
            domainQueues: new Map(),
            circuitBreakers: new Map(),
        };

        this.stats = { totalAssets: 0, totalSize: 0, crawledPages: 0, skippedAssets: 0, failedAssets: 0 };
        ['SIGINT', 'SIGTERM'].forEach(signal => process.on(signal, () => this.shutdown()));
    }

    async initialize() {
        logger.info('Initializing browser...');
        this.state.browser = await puppeteerExtra.launch({
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
        });
        logger.info('Browser initialized.');
    }

    startMemoryMonitor() {
        this.state.memoryMonitor = setInterval(() => {
            const memoryUsage = process.memoryUsage().heapUsed / os.totalmem();
            if (memoryUsage > this.options.memoryThreshold) {
                logger.warn({ memoryUsage, threshold: this.options.memoryThreshold }, 'Memory threshold exceeded.');
                if (global.gc) {
                    logger.info('Forcing garbage collection.');
                    global.gc();
                } else {
                    logger.warn('Cannot force GC. Run Node with the --expose-gc flag for better memory management.');
                }
            }
        }, 15000);
    }

    async shutdown() {
        logger.info('Shutting down...');
        if (this.state.memoryMonitor) clearInterval(this.state.memoryMonitor);
        this.pageQueue.clear();
        Array.from(this.state.domainQueues.values()).forEach(q => q.clear());
        if (this.state.browser) await this.state.browser.close();
        logger.info('Shutdown complete.');
    }

    async replicate(targetUrl, outputDir) {
        const startTime = Date.now();
        this.state.baseUrl = new URL(targetUrl).origin;
        this.state.outputDir = path.resolve(outputDir);
        await fs.mkdir(this.state.outputDir, { recursive: true });

        logger.info({ options: this.options }, 'Replication starting with options.');

        try {
            if (this.options.incremental) {
                await this.loadManifest();
            }

            await this.initialize();
            this.startMemoryMonitor();

            const initialUrls = await this.discoverInitialUrls(targetUrl);
            logger.info({ count: initialUrls.size }, 'Discovered initial URLs from sitemap and entrypoint.');

            for (const url of initialUrls) {
                if (!this.state.crawledUrls.has(url)) {
                    this.state.crawledUrls.add(url);
                    this.pageQueue.add(() => this.processPage(url, 0));
                }
            }

            await this.pageQueue.onIdle();
            await Promise.all(Array.from(this.state.domainQueues.values()).map(q => q.onIdle()));

            await this.generateManifest();
            const duration = (Date.now() - startTime) / 1000;
            logger.info({ duration: `${duration.toFixed(2)}s`, stats: this.stats }, 'Replication complete!');
            this.emit('complete', { duration, stats: this.stats });

        } catch (error) {
            logger.fatal(error, 'A fatal error occurred during replication.');
            throw error;
        } finally {
            await this.shutdown();
        }
    }

    async discoverInitialUrls(entryUrl) {
        const urls = new Set([entryUrl]);
        try {
            const robotsUrl = new URL('/robots.txt', this.state.baseUrl).href;
            const response = await fetch(robotsUrl);
            if (response.ok) {
                const text = await response.text();
                this.state.robots = robotsParser(robotsUrl, text);
                const sitemaps = this.state.robots.getSitemaps();
                for (const sitemapUrl of sitemaps) {
                    await this.parseSitemap(sitemapUrl, urls);
                }
            }
        } catch (e) {
            logger.warn({ err: e }, 'Could not process robots.txt, falling back to default sitemap location.');
        }

        try {
            await this.parseSitemap(new URL('/sitemap.xml', this.state.baseUrl).href, urls);
        } catch (e) {
            logger.warn('No sitemap.xml found at default location.');
        }

        return urls;
    }

    async parseSitemap(sitemapUrl, urlSet) {
        try {
            const response = await fetch(sitemapUrl);
            if (!response.ok) return;
            const xml = await response.text();
            const $ = cheerio.load(xml, { xmlMode: true });
            $('loc').each((_, el) => {
                const url = $(el).text();
                if (url.startsWith(this.state.baseUrl)) {
                    urlSet.add(url);
                }
            });
            logger.info({ url: sitemapUrl, count: urlSet.size }, 'Parsed sitemap.');
        } catch (error) {
            logger.error({ err: error, url: sitemapUrl }, 'Failed to parse sitemap.');
        }
    }

    async processPage(pageUrl, depth) {
        if (depth > this.options.maxCrawlDepth) return;
        if (this.state.robots && !this.state.robots.isAllowed(pageUrl, this.options.userAgent)) {
            logger.warn({ url: pageUrl }, 'Skipping page disallowed by robots.txt');
            return;
        }

        logger.info({ url: pageUrl, depth }, 'Processing page...');
        const page = await this.state.browser.newPage();
        await page.setViewport(this.options.viewport);
        await page.setUserAgent(this.options.userAgent);

        try {
            const pageAssetInfo = this.state.manifest.assets[this.getLocalPathForUrl(pageUrl)];
            const headers = {};
            if (this.options.incremental && pageAssetInfo?.etag) {
                headers['If-None-Match'] = pageAssetInfo.etag;
            }
            if (this.options.incremental && pageAssetInfo?.lastModified) {
                headers['If-Modified-Since'] = pageAssetInfo.lastModified;
            }

            await page.setExtraHTTPHeaders(headers);
            const response = await page.goto(pageUrl, { waitUntil: 'networkidle2', timeout: this.options.timeout });

            if (response.status() === 304) {
                logger.info({ url: pageUrl }, 'Page not modified (304). Skipping processing.');
                this.stats.skippedAssets++;
                await page.close();
                return;
            }

            const discoveredAssets = new Set();
            page.on('response', res => {
                const url = res.url();
                if (res.ok() && !url.startsWith('data:')) {
                    discoveredAssets.add(url);
                }
            });

            await page.waitForTimeout(1000); // Allow dynamic content to settle

            let html = await page.content();
            const etag = response.headers().etag;
            const lastModified = response.headers()['last-modified'];

            for (const assetUrl of discoveredAssets) {
                this.captureAsset(assetUrl);
            }

            const rewrittenHtml = this.htmlProcessor.rewriteUrls(html, (url) => this.rewriteUrl(url, pageUrl), this.cssProcessor);
            const localPath = this.getLocalPathForUrl(pageUrl);
            const fullPath = path.join(this.state.outputDir, localPath);

            await fs.writeFile(fullPath, rewrittenHtml);
            const hash = crypto.createHash('sha256').update(rewrittenHtml).digest('hex');

            this.state.urlToLocalPath.set(pageUrl, localPath);
            this.state.manifest.assets[localPath] = {
                originalUrl: pageUrl,
                contentType: 'text/html',
                size: rewrittenHtml.length,
                integrity: `sha256-${hash}`,
                etag,
                lastModified
            };
            this.stats.crawledPages++;

            if (this.options.captureResponsive) {
                for (const breakpoint of this.options.responsiveBreakpoints) {
                    this.captureAsset(page, pageUrl, breakpoint);
                }
            }

            if (this.options.crawlSPA && depth < this.options.maxCrawlDepth) {
                const newLinks = this.discoverLinks(html, pageUrl);
                for (const link of newLinks) {
                    if (!this.state.crawledUrls.has(link)) {
                        this.state.crawledUrls.add(link);
                        this.pageQueue.add(() => this.processPage(link, depth + 1));
                    }
                }
            }
        } catch (error) {
            logger.error({ url: pageUrl, err: error }, 'Failed to process page.');
        } finally {
            await page.close();
        }
    }

    getQueueForDomain(domain) {
        if (!this.state.domainQueues.has(domain)) {
            const isBaseDomain = domain === new URL(this.state.baseUrl).hostname;
            const concurrency = isBaseDomain ? this.options.baseAssetConcurrency : this.options.domainAssetConcurrency;
            logger.info({ domain, concurrency }, 'Creating new asset queue for domain.');
            this.state.domainQueues.set(domain, new PQueue({ concurrency }));
        }
        return this.state.domainQueues.get(domain);
    }

    getCircuitBreakerForDomain(domain) {
        if (!this.state.circuitBreakers.has(domain)) {
            this.state.circuitBreakers.set(domain, new AdvancedCircuitBreaker({ timeout: this.options.timeout }));
        }
        return this.state.circuitBreakers.get(domain);
    }

    captureAsset(assetUrl) {
        const domain = new URL(assetUrl).hostname;
        const queue = this.getQueueForDomain(domain);
        const circuitBreaker = this.getCircuitBreakerForDomain(domain);
        queue.add(() => this.fetchAndProcessAsset(assetUrl, circuitBreaker));
    }

    async fetchAndProcessAsset(assetUrl, circuitBreaker) {
        if (this.state.urlToLocalPath.has(assetUrl) || this.state.failedUrls.has(assetUrl)) {
            return;
        }

        for (let attempt = 0; attempt <= this.options.maxRetries; attempt++) {
            try {
                return await circuitBreaker.execute(async () => {
                    const headers = {};
                    const localPathForCheck = this.getLocalPathForUrl(assetUrl);
                    const existingAsset = this.state.manifest.assets[localPathForCheck];
                    if (this.options.incremental && existingAsset?.etag) {
                        headers['If-None-Match'] = existingAsset.etag;
                    }
                    if (this.options.incremental && existingAsset?.lastModified) {
                        headers['If-Modified-Since'] = existingAsset.lastModified;
                    }

                    const response = await fetch(assetUrl, { headers });

                    if (response.status === 304) {
                        logger.info({ url: assetUrl }, 'Asset not modified (304). Skipping download.');
                        this.stats.skippedAssets++;
                        return;
                    }
                    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

                    const contentType = response.headers.get('content-type') || '';
                    const isTextAsset = /^(text\/|application\/(javascript|json|xml))/.test(contentType);
                    const useBrotli = this.options.enableBrotli && isTextAsset;
                    const localPath = this.getLocalPathForUrl(assetUrl) + (useBrotli ? '.br' : '');
                    const fullPath = path.join(this.state.outputDir, localPath);

                    await fs.mkdir(path.dirname(fullPath), { recursive: true });

                    const optimizationStream = this.getOptimizationStream(contentType);
                    const compressionStream = useBrotli ? zlib.createBrotliCompress() : null;
                    const writeStream = fsSync.createWriteStream(fullPath);

                    const streams = [response.body, optimizationStream, compressionStream, writeStream].filter(Boolean);
                    await pipeline(streams);

                    const finalBuffer = await fs.readFile(fullPath);
                    const hash = crypto.createHash('sha256').update(finalBuffer).digest('hex');

                    this.state.urlToLocalPath.set(assetUrl, localPath);
                    this.state.manifest.assets[localPath] = {
                        originalUrl: assetUrl,
                        contentType,
                        size: finalBuffer.length,
                        integrity: `sha256-${hash}`,
                        etag: response.headers.get('etag'),
                        lastModified: response.headers.get('last-modified'),
                    };

                    this.stats.totalAssets++;
                    this.stats.totalSize += finalBuffer.length;
                    logger.info({ path: localPath, size: `${(finalBuffer.length / 1024).toFixed(2)} KB` }, 'Asset captured');
                });
            } catch (error) {
                logger.warn({ url: assetUrl, attempt: attempt + 1, err: error.message }, 'Asset download failed. Retrying...');
                if (attempt < this.options.maxRetries) {
                    const delay = (this.options.retryDelayBase * Math.pow(2, attempt)) + (Math.random() * 1000);
                    await new Promise(resolve => setTimeout(resolve, delay));
                } else {
                    logger.error({ url: assetUrl }, 'Asset download failed after all retries.');
                    this.state.failedUrls.add(assetUrl);
                    this.stats.failedAssets++;
                }
            }
        }
    }

    getOptimizationStream(contentType) {
        if (this.options.optimizeImages && contentType.startsWith('image/')) {
            if (contentType.includes('svg')) {
                return new Transform({
                    chunks: [],
                    transform(chunk, encoding, callback) { this.chunks.push(chunk); callback(); },
                    flush(callback) {
                        const svgBuffer = Buffer.concat(this.chunks);
                        try { this.push(Buffer.from(optimizeSvg(svgBuffer.toString()).data)); }
                        catch (e) { this.push(svgBuffer); }
                        callback();
                    }
                });
            }
            const sharpStream = sharp();
            if (this.options.enableAVIF) sharpStream.avif({ quality: 75 });
            else sharpStream.webp({ quality: 80 });
            return sharpStream;
        }
        return new Transform({ transform(chunk, enc, cb) { cb(null, chunk); } });
    }

    async captureScreenshot(page, pageUrl, breakpoint) {
        logger.info({ url: pageUrl, viewport: breakpoint.name }, 'Capturing responsive screenshot...');
        const originalViewport = page.viewport();
        await page.setViewport(breakpoint);
        await page.waitForTimeout(500);

        const screenshotPath = this.getLocalPathForUrl(pageUrl).replace(/\.html$/, `_${breakpoint.name}.png`);
        const fullPath = path.join(this.state.outputDir, screenshotPath);

        try {
            await page.screenshot({ path: fullPath, fullPage: true });
            logger.info({ path: screenshotPath }, 'Screenshot saved.');
        } catch (error) {
            logger.error({ err: error }, `Failed to capture screenshot for ${breakpoint.name}`);
        } finally {
            await page.setViewport(originalViewport);
        }
    }

    async loadManifest() {
        const manifestPath = path.join(this.state.outputDir, 'manifest.json');
        try {
            const data = await fs.readFile(manifestPath, 'utf-8');
            this.state.manifest = JSON.parse(data);
            for (const [localPath, assetInfo] of Object.entries(this.state.manifest.assets)) {
                this.state.urlToLocalPath.set(assetInfo.originalUrl, localPath);
            }
            logger.info(`Loaded existing manifest with ${Object.keys(this.state.manifest.assets).length} assets.`);
        } catch (e) {
            logger.warn('No existing manifest found or failed to load. Performing a full replication.');
            this.state.manifest = { assets: {} };
        }
    }

    async generateManifest() {
        const manifestPath = path.join(this.state.outputDir, 'manifest.json');
        const manifestData = {
            replicatedAt: new Date().toISOString(),
            sourceUrl: this.state.baseUrl,
            stats: this.stats,
            assets: this.state.manifest.assets,
        };
        await fs.writeFile(manifestPath, JSON.stringify(manifestData, null, 2));
        logger.info(`Integrity manifest saved to ${manifestPath}`);
    }

    async verify(outputDir) {
        logger.info({ directory: outputDir }, 'Starting integrity verification...');
        const manifestPath = path.join(outputDir, 'manifest.json');
        let manifest;
        try {
            manifest = JSON.parse(await fs.readFile(manifestPath, 'utf-8'));
        } catch (e) {
            logger.fatal('Could not read manifest.json. Cannot verify integrity.');
            return false;
        }

        let validCount = 0;
        let invalidCount = 0;
        const assetEntries = Object.entries(manifest.assets);

        for (const [localPath, assetInfo] of assetEntries) {
            const fullPath = path.join(outputDir, localPath);
            try {
                const buffer = await fs.readFile(fullPath);
                const actualHash = `sha256-${crypto.createHash('sha256').update(buffer).digest('hex')}`;
                if (actualHash === assetInfo.integrity) {
                    validCount++;
                } else {
                    invalidCount++;
                    logger.error({ path: localPath, expected: assetInfo.integrity, actual: actualHash }, 'Integrity mismatch!');
                }
            } catch (e) {
                invalidCount++;
                logger.error({ path: localPath }, 'File not found during verification.');
            }
        }

        logger.info('Verification complete.');
        logger.info(`Total assets: ${assetEntries.length}, Valid: ${validCount}, Invalid: ${invalidCount}`);
        return invalidCount === 0;
    }

    discoverLinks(html, baseUrl) {
        const $ = cheerio.load(html);
        const links = new Set();
        $('a[href]').each((_, el) => {
            const href = $(el).attr('href');
            if (href) {
                try {
                    const absoluteUrl = new URL(href, baseUrl).href.split('#')[0];
                    if (absoluteUrl.startsWith(this.state.baseUrl)) {
                        links.add(absoluteUrl);
                    }
                } catch (e) { /* Ignore invalid URLs */ }
            }
        });
        return Array.from(links);
    }

    rewriteUrl(originalUrl, baseUrl) {
        if (!originalUrl || originalUrl.startsWith('data:') || originalUrl.startsWith('#')) {
            return originalUrl;
        }
        try {
            const absoluteUrl = new URL(originalUrl, baseUrl).href;
            if (this.state.urlToLocalPath.has(absoluteUrl)) {
                return this.state.urlToLocalPath.get(absoluteUrl);
            }
        } catch (e) { /* Fallback for invalid URLs */ }
        return originalUrl;
    }

    getLocalPathForUrl(assetUrl) {
        const url = new URL(assetUrl);
        const pathname = url.pathname.endsWith('/') ? `${url.pathname}index.html` : url.pathname;
        const ext = path.extname(pathname) || '.html';
        const basename = path.basename(pathname, ext);
        const dirname = path.dirname(pathname).substring(1);

        const queryHash = url.search ? `_${crypto.createHash('md5').update(url.search).digest('hex').substring(0, 8)}` : '';

        const safeBasename = basename.replace(/[^a-z0-9_-]/gi, '_');
        const safeDirname = dirname.replace(/[^a-z0-9/_-]/gi, '_');

        return path.join(safeDirname, `${safeBasename}${queryHash}${ext}`);
    }
}

// --- Main Execution & CLI ---
async function main() {
    const cli = yargs(hideBin(process.argv))
        .command('replicate <url> [outputDir]', 'Replicate a website', (y) => {
            y.positional('url', { describe: 'The target URL to replicate', type: 'string' })
             .positional('outputDir', { describe: 'The directory to save the replica', type: 'string', default: './replicated-site' })
             .option('depth', { alias: 'd', type: 'number', default: 2, describe: 'Maximum crawl depth' })
             .option('incremental', { type: 'boolean', default: false, describe: 'Perform an incremental update based on the existing manifest.' })
             .option('responsive', { type: 'boolean', default: false, describe: 'Capture responsive screenshots' })
             .option('brotli', { type: 'boolean', default: false, describe: 'Enable Brotli compression for text assets' })
             .option('pageConcurrency', { type: 'number', default: 4, describe: 'Max pages to process concurrently' })
             .option('baseAssetConcurrency', { type: 'number', default: 10, describe: 'Max assets to download from the main domain concurrently' })
             .option('domainAssetConcurrency', { type: 'number', default: 3, describe: 'Max assets to download from external domains concurrently' });
        }, async (argv) => {
            const replicator = new UltimateWebsiteReplicator({
                maxCrawlDepth: argv.depth,
                incremental: argv.incremental,
                captureResponsive: argv.responsive,
                enableBrotli: argv.brotli,
                pageConcurrency: argv.pageConcurrency,
                baseAssetConcurrency: argv.baseAssetConcurrency,
                domainAssetConcurrency: argv.domainAssetConcurrency,
            });
            await replicator.replicate(argv.url, argv.outputDir);
        })
        .command('verify <outputDir>', 'Verify the integrity of a replicated site', (y) => {
            y.positional('outputDir', { describe: 'The directory of the replica to verify', type: 'string', demandOption: true });
        }, async (argv) => {
            const replicator = new UltimateWebsiteReplicator();
            const is_valid = await replicator.verify(argv.outputDir);
            process.exit(is_valid ? 0 : 1);
        })
        .demandCommand(1, 'You must provide a command: replicate or verify.')
        .help()
        .alias('h', 'help')
        .strict();

    try {
        await cli.parse();
    } catch (error) {
        logger.fatal(error, 'CLI process failed.');
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { UltimateWebsiteReplicator };
