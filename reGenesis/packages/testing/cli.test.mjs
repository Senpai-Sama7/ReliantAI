import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

const cli = path.resolve('tools/replicator.mjs');

test('replicator --help', () => {
  const res = spawnSync('node', [cli, '--help'], { encoding: 'utf8' });
  assert.equal(res.status, 0);
  assert.match(res.stdout, /Replicate a website/);
});

test('replicator verify fails on missing dir', () => {
  const res = spawnSync('node', [cli, 'verify', 'nope'], { encoding: 'utf8' });
  assert.notEqual(res.status, 0);
});
