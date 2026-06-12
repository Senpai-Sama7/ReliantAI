/**
 * Allow only http/https URLs in rendered links (blocks javascript:, data:, etc.).
 */
export function sanitizeHttpUrl(
  url: string | undefined | null,
): string | null {
  if (!url || typeof url !== "string") return null;
  const trimmed = url.trim();
  if (!trimmed) return null;
  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return parsed.href;
    }
  } catch {
    return null;
  }
  return null;
}
