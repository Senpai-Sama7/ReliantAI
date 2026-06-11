// Slugs come from the platform's generate_slug(business_name, city):
// lowercase alphanumerics separated by single hyphens. Anything else is
// rejected before it can reach the API URL path (prevents traversal like
// "../admin" being interpolated into the fetch URL).
const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export const MAX_SLUG_LENGTH = 100;

export function isValidSlug(slug: string): boolean {
  return (
    slug.length > 0 && slug.length <= MAX_SLUG_LENGTH && SLUG_PATTERN.test(slug)
  );
}
