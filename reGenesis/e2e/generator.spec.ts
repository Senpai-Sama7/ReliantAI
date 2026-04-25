import { test, expect } from '@playwright/test';
import { spawn } from 'node:child_process';
import path from 'node:path';

const root = process.cwd();
const brief = path.join(root, 'packages/schemas/examples/brand-brief.example.json');
const outDir = path.join(root, 'out-e2e');

function runNode(args: string[], env: NodeJS.ProcessEnv = {}) {
  return new Promise<{ code: number | null; stdout: string; stderr: string }>((resolve) => {
    const child = spawn(process.execPath, args, { env: { ...process.env, ...env }, cwd: root });
    let stdout = '', stderr = '';
    child.stdout.on('data', (d) => (stdout += String(d)));
    child.stderr.on('data', (d) => (stderr += String(d)));
    child.on('close', (code) => resolve({ code, stdout, stderr }));
  });
}

test('generator fails clearly without GEMINI_API_KEY', async () => {
  const { code, stderr } = await runNode([
    path.join(root, 'tools/generate.mjs'),
    '--brief', brief,
    '--outputDir', outDir,
    '--dry-run',
  ], { GEMINI_API_KEY: '' });
  expect(code).not.toBe(0);
  expect(stderr).toMatch(/GEMINI_API_KEY is required/i);
});

test('generator dry-run succeeds when GEMINI_API_KEY is set', async () => {
  test.skip(!process.env.GEMINI_API_KEY, 'No GEMINI_API_KEY in env');
  const { code, stdout, stderr } = await runNode([
    path.join(root, 'tools/generate.mjs'),
    '--brief', brief,
    '--outputDir', outDir,
    '--dry-run',
  ]);
  expect(stderr).toBe('');
  expect(code).toBe(0);
  expect(stdout).toMatch(/DRY RUN/i);
});
