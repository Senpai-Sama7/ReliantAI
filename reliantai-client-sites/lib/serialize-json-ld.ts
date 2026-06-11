/**
 * Safe JSON-LD for embedding in a <script> tag.
 * - Escapes "<" as \u003c so API-sourced content containing "</script>"
 *   cannot terminate the script element (XSS breakout). The output parses
 *   back to the identical value via JSON.parse.
 * - Falls back to {} for null/undefined: JSON.stringify(undefined) returns
 *   undefined (not a string), which would otherwise throw at .replace().
 */
export function serializeJsonLd(data: unknown): string {
  return JSON.stringify(data ?? {}).replace(/</g, "\\u003c");
}
