import assert from 'node:assert/strict';
import test from 'node:test';

import { isToolAllowed, requireApiKey } from './auth';

function mockResponse() {
  return {
    statusCode: 200,
    body: null as unknown,
    status(code: number) {
      this.statusCode = code;
      return this;
    },
    json(payload: unknown) {
      this.body = payload;
      return this;
    },
  };
}

test('requireApiKey rejects when key is missing', () => {
  process.env.APEX_MCP_API_KEY = 'super-secret-api-key';
  const req = { header: () => undefined } as any;
  const res = mockResponse();
  let nextCalled = false;

  requireApiKey(req, res as any, () => {
    nextCalled = true;
  });

  assert.equal(nextCalled, false);
  assert.equal(res.statusCode, 401);
});

test('requireApiKey accepts a valid bearer token', () => {
  process.env.APEX_MCP_API_KEY = 'super-secret-api-key';
  const req = {
    header(name: string) {
      if (name === 'authorization') return 'Bearer super-secret-api-key';
      return undefined;
    },
  } as any;
  const res = mockResponse();
  let nextCalled = false;

  requireApiKey(req, res as any, () => {
    nextCalled = true;
  });

  assert.equal(nextCalled, true);
  assert.equal(res.statusCode, 200);
});

test('isToolAllowed enforces configured allowlist', () => {
  process.env.APEX_MCP_ALLOWED_TOOLS = 'brave_search, notion';

  assert.equal(isToolAllowed('brave_search'), true);
  assert.equal(isToolAllowed('stripe'), false);
});
