/**
 * Allow only http/https URLs in rendered links (blocks javascript:, data:, etc.).
 */
export function sanitizeHttpUrl(
  url: string | undefined | null,
): string | null {
  if (!url || typeof url !== "string") return null;
  const trimmed = url.trim();
  if (!trimmed) return null;
  let target = trimmed;
  if (!/^https?:\/\//i.test(target)) {
    if (target.includes(".") && !target.startsWith(".")) {
      target = `https://${target}`;
    }
  }
  try {
    const parsed = new URL(target);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return parsed.href;
    }
  } catch {
    return null;
  }
  return null;
}

const DEFAULT_CHECKOUT_BASE = "https://reliantai.org";

/**
 * Resolve checkout origin for PreviewBanner CTAs.
 * Rejects non-http(s) values so a mis-set NEXT_PUBLIC_CHECKOUT_BASE_URL
 * cannot become an open redirect.
 */
export function resolveCheckoutBaseUrl(
  raw: string | undefined | null,
  fallback: string = DEFAULT_CHECKOUT_BASE,
): string {
  const safe = sanitizeHttpUrl(raw);
  if (safe) {
    // Origin only — strip path/query so we always append /checkout ourselves.
    try {
      const parsed = new URL(safe);
      return parsed.origin;
    } catch {
      /* fall through */
    }
  }
  const fallbackSafe = sanitizeHttpUrl(fallback) ?? DEFAULT_CHECKOUT_BASE;
  try {
    return new URL(fallbackSafe).origin;
  } catch {
    return DEFAULT_CHECKOUT_BASE;
  }
}
