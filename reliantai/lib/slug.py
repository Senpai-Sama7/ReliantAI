"""Slug validation and generation utilities."""

import re


def is_valid_slug(slug: str) -> bool:
    """Validate slug format (alphanumeric, hyphens, underscores only)."""
    if not slug or len(slug) > 255:
        return False
    return bool(re.match(r"^[a-z0-9_-]+$", slug))


def generate_slug(business_name: str, city: str, place_id: str) -> str:
    """Generate a SEO-friendly slug from business name and city."""
    # Normalize: lowercase, remove special chars, replace spaces with hyphens
    base = f"{business_name}-{city}".lower()
    base = re.sub(r"[^a-z0-9]+", "-", base)
    base = base.strip("-")
    
    # Add place ID suffix for uniqueness
    place_suffix = place_id[-8:] if len(place_id) > 8 else place_id
    slug = f"{base}-{place_suffix}"
    
    # Ensure valid length
    if len(slug) > 255:
        slug = slug[:255]
    
    return slug
