import test from 'node:test';
import assert from 'node:assert/strict';
import { UltimateWebsiteReplicator } from '../../tools/replicator.mjs';

test('Path traversal protection', async () => {
  const replicator = new UltimateWebsiteReplicator();
  replicator.state.outputDir = '/safe/output';

  const maliciousPaths = [
    '../../../etc/passwd',
    '..\\..\\windows\\system32\\config\\sam',
    '/etc/shadow',
    'C:\\Windows\\System32\\drivers\\etc\\hosts'
  ];

  for (const p of maliciousPaths) {
    assert.throws(() => {
      replicator.resolveOutputPath(p);
    }, /Path traversal/);
  }
});

test('Memory pressure handling pauses queues', async () => {
  const replicator = new UltimateWebsiteReplicator({
    memoryThreshold: 0.0000001 // Very low threshold to trigger pause quickly
  });
  replicator.startMemoryMonitor(10);
  // Wait a moment for monitor to run at least once
  await new Promise(resolve => setTimeout(resolve, 50));
  try {
    assert.equal(replicator.pageQueue.isPaused, true);
  } finally {
    if (replicator.state.memoryMonitor) clearInterval(replicator.state.memoryMonitor);
  }
});
