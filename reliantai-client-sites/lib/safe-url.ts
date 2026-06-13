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
