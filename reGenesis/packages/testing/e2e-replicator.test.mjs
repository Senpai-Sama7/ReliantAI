import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { mkdtemp, rm, readFile, stat } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { UltimateWebsiteReplicator } from '../../tools/replicator.mjs';

const pngData = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=',
  'base64'
);

test('replicator crawls a local site', async () => {
  const tmp = await mkdtemp(path.join(os.tmpdir(), 'regenesis-'));
  const out = path.join(tmp, 'out');
  const server = http.createServer((req, res) => {
    if (req.url === '/a.png') {
      res.setHeader('Content-Type', 'image/png');
      res.end(pngData);
    } else {
      res.setHeader('Content-Type', 'text/html');
      res.end("<html><body><img src='/a.png'></body></html>");
    }
  });
  await new Promise(r => server.listen(0, r));
  const port = server.address().port;

  const r = new UltimateWebsiteReplicator({
    respectRobotsTxt: false,
    imagePolicy: 'none',
    pageConcurrency: 1,
    baseAssetConcurrency: 2,
    domainAssetConcurrency: 2,
    captureResponsive: true,
    responsiveBreakpoints: [{ name: 'desk', width: 800, height: 600 }]
  });
  await r.replicate(`http://localhost:${port}/`, out);
  await new Promise(res => server.close(res));

  const html = await readFile(path.join(out, 'index.html'), 'utf8');
  assert.match(html, /a.png/);
  const st = await stat(path.join(out, 'a.png'));
  assert.ok(st.size > 0);
  const shot = await stat(path.join(out, 'index_desk.png'));
  assert.ok(shot.size > 0);

  await rm(tmp, { recursive: true, force: true });
});
