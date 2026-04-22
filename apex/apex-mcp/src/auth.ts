import crypto from 'node:crypto';
import { NextFunction, Request, Response } from 'express';

const API_KEY_ENV = 'APEX_MCP_API_KEY';
const ALLOWED_TOOLS_ENV = 'APEX_MCP_ALLOWED_TOOLS';

function getConfiguredApiKey(): string {
  return (process.env[API_KEY_ENV] ?? '').trim();
}

function getProvidedApiKey(req: Request): string {
  const headerKey = req.header('x-api-key')?.trim();
  if (headerKey) return headerKey;

  const authHeader = req.header('authorization')?.trim();
  if (authHeader?.startsWith('Bearer ')) {
    return authHeader.slice('Bearer '.length).trim();
  }

  return '';
}

export function requireApiKey(req: Request, res: Response, next: NextFunction): void {
  const expected = getConfiguredApiKey();
  if (expected.length < 16) {
    res.status(503).json({ success: false, error: `${API_KEY_ENV} is not configured` });
    return;
  }

  const provided = getProvidedApiKey(req);
  if (
    !provided ||
    provided.length !== expected.length ||
    !crypto.timingSafeEqual(Buffer.from(provided), Buffer.from(expected))
  ) {
    res.status(401).json({ success: false, error: 'Missing or invalid API key' });
    return;
  }

  next();
}

export function isToolAllowed(name: string): boolean {
  const configured = (process.env[ALLOWED_TOOLS_ENV] ?? '')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);

  return configured.length === 0 || configured.includes(name);
}
