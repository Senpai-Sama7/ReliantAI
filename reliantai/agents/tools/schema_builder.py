import structlog
from typing import Dict, List, Optional

log = structlog.get_logger()

TRADE_TO_SCHEMA_TYPE = {
    "hvac": "HVACBusiness",
    "plumbing": "Plumber",
    "electrical": "Electrician",
    "roofing": "RoofingContractor",
    "painting": "HousePainter",
    "landscaping": "LandscapingBusiness",
}


def _format_geo_coordinates(lat: Optional[float], lng: Optional[float]) -> Dict:
    return {
        "@type": "GeoCoordinates",
        "latitude": float(lat),
        "longitude": float(lng),
    }


def _format_address(address_str: str) -> Dict:
    return {
        "@type": "PostalAddress",
        "streetAddress": address_str.split(",")[0] if address_str else "",
        "addressLocality": "",
        "addressRegion": "",
        "postalCode": "",
        "addressCountry": "US",
    }


def _format_reviews(reviews_data: Optional[Dict]) -> List:
    reviews = reviews_data.get("reviews", [])
    return [
        {
            "@type": "Review",
            "author": {"@type": "Person", "name": r.get("author", "Customer")},
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": r.get("rating", 5),
                "bestRating": 5,
            },
            "reviewBody": r.get("text", "")[:200],
        }
        for r in reviews[:3]
    ]


def build_local_business_schema(
    business_data: Dict,
    review_data: Optional[Dict] = None,
    competitor_keywords: Optional[List] = None,
) -> Dict:
    trade = business_data.get("trade", "hvac")
    schema_type = TRADE_TO_SCHEMA_TYPE.get(trade, "LocalBusiness")
    slug = business_data.get("slug", "")
    name = business_data.get("name", "")
    city = business_data.get("city", "")
    state = business_data.get("state", "")
    phone = business_data.get("phone", "")
    website = business_data.get("website", "")
    description = business_data.get("summary", "")
    lat = business_data.get("lat")
    lng = business_data.get("lng")
    address = business_data.get("address", "")
    rating = business_data.get("rating")
    review_count = business_data.get("review_count", 0)
    years = business_data.get("years_in_business")

    schema = {
        "@context": "https://schema.org",
        "@type": [schema_type, "LocalBusiness"],
        "@id": f"https://preview.reliantai.org/{slug}#business",
        "name": name,
        "description": description or f"{name} provides professional {trade} services in {city}, {state}.",
        "url": f"https://preview.reliantai.org/{slug}",
        "telephone": phone,
        "image": business_data.get("photos", [None])[0],
        "logo": business_data.get("logo"),
        "priceRange": "$$",
        "address": _format_address(address),
    }

    if lat and lng:
        schema["geo"] = _format_geo_coordinates(lat, lng)

    if rating and review_count:
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": float(rating),
            "reviewCount": int(review_count),
            "bestRating": 5,
            "worstRating": 1,
        }

    if review_data and isinstance(review_data, dict):
        schema["review"] = _format_reviews(review_data)

    social_urls = []
    for key in ["facebook_url", "instagram_url", "linkedin_url", "youtube_url", "yelp_url"]:
        url = business_data.get(key) or business_data.get(key.replace("_url", ""))
        if url:
            social_urls.append(url)
    if social_urls:
        schema["sameAs"] = social_urls

    services = business_data.get("service_specialties", "")
    if services:
        items = [s.strip() for s in services.split(",") if s.strip()]
        schema["hasOfferCatalog"] = {
            "@type": "OfferCatalog",
            "name": f"{name} Services",
            "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": item}}
                for item in items
            ],
        }

    if competitor_keywords:
        schema["keywords"] = ", ".join(competitor_keywords[:10])

    if years:
        schema["foundingDate"] = str(years)

    if business_data.get("hours"):
        schema["openingHoursSpecification"] = business_data["hours"]

    log.info("schema_built", trade=trade, schema_type=schema_type, slug=slug)
    return schema
