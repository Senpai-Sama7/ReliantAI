import json
import time
import httpx
from crewai.tools import BaseTool


class GooglePlacesTool(BaseTool):
    name: str = "google_places_search"
    description: str = (
        "Search for businesses on Google Places. "
        "Pass query='business name city state' for text search, "
        "or place_id='ChIJ...' for details on a specific place."
    )

    def _run(self, query: str = None, place_id: str = None) -> str:
        api_key = __import__("os").environ.get("GOOGLE_PLACES_API_KEY", "")
        if not api_key:
            return str({"error": "GOOGLE_PLACES_API_KEY not set"})

        if place_id:
            return self._details(api_key, place_id)
        if query:
            return self._search(api_key, query)
        return str({"error": "Provide query or place_id"})

    def _search(self, api_key: str, query: str) -> str:
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {"query": query, "key": api_key}
        for attempt in range(4):
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url, params=params)
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            if resp.status_code != 200:
                return str({"error": f"HTTP {resp.status_code}"})
            data = resp.json()
            if not data.get("results"):
                return str({"results": [], "status": data.get("status")})
            results = []
            for r in data["results"][:5]:
                results.append({
                    "place_id": r.get("place_id"),
                    "name": r.get("name"),
                    "address": r.get("formatted_address"),
                    "rating": r.get("rating"),
                    "review_count": r.get("user_ratings_total"),
                    "lat": r.get("geometry", {}).get("location", {}).get("lat"),
                    "lng": r.get("geometry", {}).get("location", {}).get("lng"),
                })
            return str({"results": results, "status": data.get("status")})
        return str({"error": "rate_limited"})

    def _details(self, api_key: str, place_id: str) -> str:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        fields = ",".join([
            "reviews", "name", "rating", "user_ratings_total",
            "formatted_phone_number", "website", "opening_hours",
            "address_components", "geometry", "photos",
            "business_status", "editorial_summary",
        ])
        params = {
            "place_id": place_id,
            "fields": fields,
            "reviews_sort": "most_relevant",
            "key": api_key,
        }
        for attempt in range(4):
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url, params=params)
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            if resp.status_code != 200:
                return str({"error": f"HTTP {resp.status_code}"})
            data = resp.json().get("result", {})
            formatted = {
                "name": data.get("name"),
                "phone": data.get("formatted_phone_number"),
                "website": data.get("website"),
                "rating": data.get("rating"),
                "review_count": data.get("user_ratings_total"),
                "address": self._extract_address(data.get("address_components", [])),
                "lat": data.get("geometry", {}).get("location", {}).get("lat"),
                "lng": data.get("geometry", {}).get("location", {}).get("lng"),
                "hours": data.get("opening_hours", {}).get("weekday_text", []),
                "business_status": data.get("business_status"),
                "summary": data.get("editorial_summary", {}).get("overview", ""),
                "reviews": self._format_reviews(data.get("reviews", [])),
            }
            return str(formatted)
        return str({"error": "rate_limited"})

    def _format_reviews(self, reviews: list) -> list:
        formatted = []
        for r in reviews[:5]:
            formatted.append({
                "author": r.get("author_name"),
                "rating": r.get("rating"),
                "text": r.get("text", "")[:300],
                "time": r.get("relative_time_description"),
            })
        return formatted

    def _extract_address(self, components: list) -> str:
        parts = []
        for c in components:
            types = c.get("types", [])
            if "street_number" in types or "route" in types:
                parts.append(c.get("long_name", ""))
            elif "locality" in types:
                parts.append(c.get("long_name", ""))
            elif "administrative_area_level_1" in types:
                parts.append(c.get("short_name", ""))
            elif "postal_code" in types:
                parts.append(c.get("long_name", ""))
        return ", ".join(p for p in parts if p)
