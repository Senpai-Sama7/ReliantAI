/**
 * Shared Content-Security-Policy configuration.
 *
 * Single source of truth for CSP headers used by both next.config.ts
 * and vercel.json. Update this file; both deployments pick up the change.
 *
 * NOTE: 'unsafe-inline' and 'unsafe-eval' are required for Next.js
 * hydration and Turbopack HMR. When Next.js adds native nonce support,
 * migrate to nonce-based CSP for stronger XSS protection.
 *
 * Keep vercel.json Content-Security-Policy in sync — tests/unit/lib.test.ts
 * asserts parity with CSP_HEADER_VALUE.
 */
export const CSP_DIRECTIVES: string[] = [
  "default-src 'self'",
  // 'unsafe-inline' and 'unsafe-eval' required for Next.js hydration / Turbopack HMR
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' https://fonts.gstatic.com",
  "img-src 'self' data: https: blob:",
  "connect-src 'self' http://localhost:8000 https://api.reliantai.org",
  "frame-ancestors 'self'",
  "base-uri 'self'",
  "form-action 'self'",
];

export const CSP_HEADER_VALUE: string = CSP_DIRECTIVES.join("; ");
