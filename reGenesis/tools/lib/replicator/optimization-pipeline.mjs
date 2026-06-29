import { Transform, PassThrough } from 'node:stream';
import sharp from 'sharp';
import { optimize as optimizeSvg } from 'svgo';

export function createOptimizationPipeline(contentType, options, cssProcessor, plugins = []) {
  const streams = [];

  if (contentType.startsWith('text/css') && options.minifyCSS) {
    streams.push(new Transform({
      construct() { this._chunks = []; },
      transform(chunk, _enc, cb) { this._chunks.push(chunk); cb(); },
      flush(cb) {
        const buf = Buffer.concat(this._chunks).toString();
        try { this.push(cssProcessor.minify(buf)); }
        catch { this.push(buf); }
        cb();
      }
    }));
  }

  if (options.imagePolicy !== 'none' && contentType.startsWith('image/')) {
    if (contentType.includes('svg')) {
      streams.push(new Transform({
        readableHighWaterMark: 1 << 20,
        writableHighWaterMark: 1 << 20,
        construct() { this._chunks = []; },
        transform(chunk, _enc, cb) { this._chunks.push(chunk); cb(); },
        flush(cb) {
          const buf = Buffer.concat(this._chunks);
          try { this.push(Buffer.from(optimizeSvg(buf.toString()).data)); }
          catch { this.push(buf); }
          cb();
        }
      }));
    } else {
      const s = sharp();
      if (options.imagePolicy === 'avif') s.avif({ quality: 75 });
      else if (options.imagePolicy === 'webp') s.webp({ quality: 80 });
      streams.push(s);
    }
  }

  for (const plugin of plugins) {
    try {
      const s = plugin(contentType);
      if (s) streams.push(s);
    } catch {}
  }

  if (streams.length === 0) return [new PassThrough()];
  return streams;
}
