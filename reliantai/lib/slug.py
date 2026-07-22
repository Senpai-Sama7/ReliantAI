"""Slug validation and generation — never derived from place_id."""

from __future__ import annotations

import re
import uuid

# Match client-sites isValidSlug: lowercase alphanumerics, single hyphens, max 100.
_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SLUG_LENGTH = 100


def is_valid_slug(slug: str) -> bool:
    """Validate slug format (lowercase alphanumerics separated by single hyphens)."""
    if not slug or len(slug) > MAX_SLUG_LENGTH:
        return False
    return bool(_SLUG_PATTERN.match(slug))


def generate_slug(business_name: str, city: str) -> str:
    """Generate SEO slug from business name + city + short uuid nibble.

    Hard constraint: never use place_id for uniqueness.
    """
    base = f"{business_name}-{city}".lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    # Collapse accidental double hyphens from the regex
    base = re.sub(r"-{2,}", "-", base)

    suffix = uuid.uuid4().hex[:6]
    slug = f"{base}-{suffix}" if base else suffix

    if len(slug) > MAX_SLUG_LENGTH:
        # Keep the uniqueness suffix; trim the name/city portion.
        keep = MAX_SLUG_LENGTH - len(suffix) - 1
        slug = f"{base[:keep].rstrip('-')}-{suffix}"

    return slug
