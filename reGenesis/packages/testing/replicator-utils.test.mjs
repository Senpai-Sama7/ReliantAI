import test from 'node:test';
import assert from 'node:assert/strict';
import { UltimateWebsiteReplicator } from '../../tools/replicator.mjs';
import { CSSProcessor } from '../../tools/lib/replicator/css-processor.mjs';
import { HTMLProcessor } from '../../tools/lib/replicator/html-processor.mjs';

test('getLocalPathForUrl is deterministic and safe', () => {
  const r = new UltimateWebsiteReplicator();
  const p1 = r.getLocalPathForUrl('https://example.com/a/b?x=1');
  const p2 = r.getLocalPathForUrl('https://example.com/a/b?x=1');
  assert.equal(p1, p2);
  assert.ok(!p1.includes('..'));
});

test('CSSProcessor rewrites and minifies', () => {
  const cssP = new CSSProcessor();
  const css = "body { background:url('/img.png'); color: red; }";
  const rewritten = cssP.rewriteUrls(css, (u) => `/static${u}`);
  assert.ok(rewritten.includes("url('/static/img.png')"));
  const min = cssP.minify(rewritten);
  assert.equal(min, "body{background:url(/static/img.png);color:red}");
});

test('HTMLProcessor rewrites URLs', () => {
  const cssP = new CSSProcessor();
  const htmlP = new HTMLProcessor();
  const html = "<img src='/a.png' style=\"background:url(/b.png)\">";
  const rewritten = htmlP.rewriteUrls(html, (u) => `/x${u}`, cssP);
  assert.ok(rewritten.includes("src=\"/x/a.png\""));
  assert.ok(rewritten.includes("url(/x/b.png)"));
});
