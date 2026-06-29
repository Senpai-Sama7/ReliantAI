import * as csso from 'csso';

export class CSSProcessor {
  rewriteUrls(cssContent, urlRewriter) {
    const urlPattern = /url\s*\(\s*(['"]?)([^'"\)]+?)\1\s*\)/gi;
    return cssContent.replace(urlPattern, (match, quote, originalUrl) => {
      if (!originalUrl || originalUrl.startsWith('data:')) return match;
      const rewrittenUrl = urlRewriter(originalUrl);
      return `url(${quote}${rewrittenUrl}${quote})`;
    });
  }
  minify(cssContent) {
    try {
      return csso.minify(cssContent).css;
    } catch {
      return cssContent;
    }
  }
}
