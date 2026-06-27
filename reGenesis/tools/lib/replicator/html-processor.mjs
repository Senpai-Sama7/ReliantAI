import * as cheerio from 'cheerio';
import { minify as minifyHtml } from 'html-minifier-terser';

export class HTMLProcessor {
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
    this.urlAttributes.forEach((attrs, tag) => {
      $(tag).each((_, el) => {
        const $el = $(el);
        for (const attr of attrs) {
          const val = $el.attr(attr);
          if (!val) continue;
          if (attr.includes('srcset')) $el.attr(attr, this.processSrcset(val, urlRewriter));
          else $el.attr(attr, urlRewriter(val));
        }
      });
    });
    $('[style]').each((_, el) => {
      const $el = $(el);
      const style = $el.attr('style') || '';
      $el.attr('style', cssProcessor.rewriteUrls(style, urlRewriter));
    });
    $('style').each((_, el) => {
      const $el = $(el);
      const css = $el.html() || '';
      $el.html(cssProcessor.rewriteUrls(css, urlRewriter));
    });
    $('meta[property="og:image"], meta[name="twitter:image"]').each((_, el) => {
      const $el = $(el);
      const val = $el.attr('content');
      if (val) $el.attr('content', urlRewriter(val));
    });
    $('script[type="application/ld+json"]').each((_, el) => {
      const $el = $(el);
      try {
        const data = JSON.parse($el.html() || '{}');
        const traverse = (obj) => {
          for (const k of Object.keys(obj)) {
            const v = obj[k];
            if (typeof v === 'string' && /^https?:/.test(v)) obj[k] = urlRewriter(v);
            else if (v && typeof v === 'object') traverse(v);
          }
        };
        traverse(data);
        $el.html(JSON.stringify(data));
      } catch {}
    });
    return $.html();
  }

  async minify(htmlContent) {
    try {
      return await minifyHtml(htmlContent, {
        collapseWhitespace: true,
        removeComments: true,
        minifyCSS: true,
        minifyJS: true,
      });
    } catch {
      return htmlContent;
    }
  }
}
