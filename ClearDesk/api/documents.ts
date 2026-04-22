import crypto from 'crypto';
import type { VercelRequest, VercelResponse } from '@vercel/node';

const SESSION_COOKIE = 'cleardesk_sync_session';
const SESSION_TTL_SECONDS = 30 * 24 * 60 * 60;
const SHARE_TTL_SECONDS = 10 * 60;

type SyncClaims = {
  syncId: string;
  type: 'session' | 'share';
  exp: number;
};

const kvUrl = (key: string) => {
  const { CLOUDFLARE_ACCOUNT_ID: acct, CLOUDFLARE_KV_NAMESPACE_ID: ns } = process.env;
  return `https://api.cloudflare.com/client/v4/accounts/${acct}/storage/kv/namespaces/${ns}/values/${key}`;
};

const headers = () => ({
  'Authorization': `Bearer ${process.env.CLOUDFLARE_API_TOKEN}`,
  'Content-Type': 'application/json',
});

const syncConfigured = () => {
  const {
    CLOUDFLARE_ACCOUNT_ID,
    CLOUDFLARE_KV_NAMESPACE_ID,
    CLOUDFLARE_API_TOKEN,
    CLEARDESK_SYNC_SECRET,
  } = process.env;

  return Boolean(
    CLOUDFLARE_ACCOUNT_ID &&
    CLOUDFLARE_KV_NAMESPACE_ID &&
    CLOUDFLARE_API_TOKEN &&
    CLEARDESK_SYNC_SECRET
  );
};

const parseCookies = (header?: string): Record<string, string> =>
  Object.fromEntries(
    (header || '')
      .split(';')
      .map((part) => part.trim())
      .filter(Boolean)
      .map((part) => {
        const index = part.indexOf('=');
        if (index === -1) {
          return [part, ''];
        }

        return [part.slice(0, index), decodeURIComponent(part.slice(index + 1))];
      })
  );

const signToken = (claims: SyncClaims) => {
  const secret = process.env.CLEARDESK_SYNC_SECRET!;
  const payload = Buffer.from(JSON.stringify(claims)).toString('base64url');
  const signature = crypto.createHmac('sha256', secret).update(payload).digest('base64url');
  return `${payload}.${signature}`;
};

const verifyToken = (token: string | undefined, expectedType: SyncClaims['type']): SyncClaims | null => {
  if (!token) {
    return null;
  }

  const [payload, signature] = token.split('.');
  if (!payload || !signature) {
    return null;
  }

  const secret = process.env.CLEARDESK_SYNC_SECRET!;
  const expectedSignature = crypto.createHmac('sha256', secret).update(payload).digest('base64url');
  const actualSignature = Buffer.from(signature);
  const expectedSignatureBytes = Buffer.from(expectedSignature);
  if (actualSignature.length !== expectedSignatureBytes.length) {
    return null;
  }
  if (!crypto.timingSafeEqual(actualSignature, expectedSignatureBytes)) {
    return null;
  }

  try {
    const claims = JSON.parse(Buffer.from(payload, 'base64url').toString('utf-8')) as SyncClaims;
    if (claims.type !== expectedType || claims.exp < Date.now()) {
      return null;
    }
    return claims;
  } catch {
    return null;
  }
};

// SECURITY FIX: Added Secure flag for production HTTPS
const serializeSessionCookie = (token: string) => {
  const isProduction = process.env.NODE_ENV === 'production';
  const secureFlag = isProduction ? '; Secure' : '';
  return `${SESSION_COOKIE}=${encodeURIComponent(token)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${SESSION_TTL_SECONDS}${secureFlag}`;
};

const getSessionClaims = (req: VercelRequest) => {
  const cookies = parseCookies(req.headers.cookie);
  return verifyToken(cookies[SESSION_COOKIE], 'session');
};

const getStorageKey = (syncId: string) =>
  `documents:${crypto.createHash('sha256').update(syncId).digest('hex')}`;

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (!syncConfigured()) {
    if (req.method === 'GET') {
      return res.json({ documents: [] });
    }

    return res.json({ ok: true, warning: 'Cloud sync not configured — data saved locally only' });
  }

  try {
    if (req.method === 'POST') {
      const action = req.body?.action as string | undefined;

      if (action === 'init') {
        const currentSession = getSessionClaims(req);
        const syncId = currentSession?.syncId || crypto.randomBytes(32).toString('hex');
        const sessionToken = signToken({
          syncId,
          type: 'session',
          exp: Date.now() + SESSION_TTL_SECONDS * 1000,
        });
        res.setHeader('Set-Cookie', serializeSessionCookie(sessionToken));
        return res.json({ ok: true });
      }

      if (action === 'share') {
        const currentSession = getSessionClaims(req);
        if (!currentSession) {
          return res.status(401).json({ error: 'Sync session required' });
        }

        const expiresAt = Date.now() + SHARE_TTL_SECONDS * 1000;
        const shareToken = signToken({
          syncId: currentSession.syncId,
          type: 'share',
          exp: expiresAt,
        });
        return res.json({ ok: true, shareToken, expiresAt: new Date(expiresAt).toISOString() });
      }

      if (action === 'import') {
        const shareToken = req.body?.shareToken as string | undefined;
        const shareClaims = verifyToken(shareToken, 'share');
        if (!shareClaims) {
          return res.status(401).json({ error: 'Invalid or expired share code' });
        }

        const sessionToken = signToken({
          syncId: shareClaims.syncId,
          type: 'session',
          exp: Date.now() + SESSION_TTL_SECONDS * 1000,
        });
        res.setHeader('Set-Cookie', serializeSessionCookie(sessionToken));

        const response = await fetch(kvUrl(getStorageKey(shareClaims.syncId)), { headers: headers() });
        if (response.status === 404) {
          return res.json({ ok: true, documents: [] });
        }
        if (!response.ok) {
          return res.status(502).json({ error: 'KV read failed' });
        }

        const data = await response.text();
        try {
          return res.json({ ok: true, documents: JSON.parse(data) });
        } catch {
          return res.json({ ok: true, documents: [] });
        }
      }

      return res.status(400).json({ error: 'Invalid sync action' });
    }

    const session = getSessionClaims(req);
    if (!session) {
      return res.status(401).json({ error: 'Sync session required' });
    }

    const key = getStorageKey(session.syncId);

    if (req.method === 'GET') {
      const response = await fetch(kvUrl(key), { headers: headers() });
      if (response.status === 404) {
        return res.json({ documents: [] });
      }
      if (!response.ok) {
        return res.status(502).json({ error: 'KV read failed' });
      }

      const data = await response.text();
      try {
        return res.json({ documents: JSON.parse(data) });
      } catch {
        return res.json({ documents: [] });
      }
    }

    if (req.method === 'PUT') {
      const { documents } = req.body;
      if (!Array.isArray(documents)) {
        return res.status(400).json({ error: 'documents must be an array' });
      }
      if (documents.length > 500) {
        return res.status(400).json({ error: 'Too many documents' });
      }

      const response = await fetch(kvUrl(key), {
        method: 'PUT',
        headers: headers(),
        body: JSON.stringify(documents),
      });
      if (!response.ok) {
        return res.status(502).json({ error: 'KV write failed' });
      }
      return res.json({ ok: true });
    }

    return res.status(405).json({ error: 'Method not allowed' });
  } catch {
    return res.status(500).json({ error: 'Sync failed' });
  }
}
