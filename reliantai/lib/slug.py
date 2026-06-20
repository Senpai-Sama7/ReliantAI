"""URL slug validation — mirrors reliantai-client-sites/lib/slug.ts."""

from __future__ import annotations

import re

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SLUG_LENGTH = 100


def is_valid_slug(slug: str) -> bool:
    return (
        bool(slug)
        and len(slug) <= MAX_SLUG_LENGTH
        and SLUG_PATTERN.fullmatch(slug) is not None
    )
