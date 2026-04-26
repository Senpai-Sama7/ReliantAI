import os
import httpx
import structlog
from crewai.tools import BaseTool

log = structlog.get_logger()


class GBPScraperTool(BaseTool):
    name: str = "gbp_profile_scraper"
    description: str = (
        "Scrape a Google Business Profile using the Places Details API. "
        "Returns photos, editorial summary, opening hours, and completeness score."
    )

    def _run(self, place_id: str) -> str:
        if not place_id:
            return str({"error": "place_id required"})

        api_key = os.environ.get("GOOGLE_PLACES_API_KEY", "")
        if not api_key:
            return str({"error": "GOOGLE_PLACES_API_KEY not set"})

        fields = ",".join([
            "photos", "editorial_summary", "opening_hours",
            "business_status", "rating", "user_ratings_total",
            "reviews", "name",
        ])

        params = {
            "place_id": place_id,
            "fields": fields,
            "key": api_key,
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(
                    "https://maps.googleapis.com/maps/api/place/details/json",
                    params=params,
                )
            if resp.status_code != 200:
                return str({"error": f"HTTP {resp.status_code}"})

            data = resp.json().get("result", {})
            photos = [p.get("photo_reference", "") for p in data.get("photos", [])[:10]]
            summary = data.get("editorial_summary", {}).get("overview", "")
            hours = data.get("opening_hours", {}).get("weekday_text", [])
            reviews = data.get("reviews", [])
            rating = data.get("rating", 0)
            review_count = data.get("user_ratings_total", 0)

            completeness = self._estimate_completeness(data)
            response_rate = self._estimate_review_response_rate(reviews)

            result = {
                "photos": photos,
                "summary": summary,
                "hours": hours,
                "business_status": data.get("business_status"),
                "rating": rating,
                "review_count": review_count,
                "profile_completeness": completeness,
                "review_response_rate": response_rate,
                "reviews": [
                    {
                        "author": r.get("author_name"),
                        "rating": r.get("rating"),
                        "text": r.get("text", "")[:300],
                        "time": r.get("relative_time_description"),
                        "has_response": bool(r.get("owner_response")),
                    }
                    for r in reviews[:5]
                ],
            }
            log.info("gbp_scrape_complete", place_id=place_id, completeness=completeness)
            return str(result)
        except httpx.TimeoutException:
            log.error("gbp_scrape_timeout", place_id=place_id)
            return str({"error": "timeout"})
        except httpx.HTTPStatusError as e:
            log.error("gbp_scrape_http_error", place_id=place_id, status_code=e.response.status_code)
            return str({"error": f"http_error_{e.response.status_code}"})
        except (httpx.RequestError, ValueError, KeyError) as e:
            log.error("gbp_scrape_failed", place_id=place_id, error=str(e))
            return str({"error": str(e)[:100]})

    def _estimate_completeness(self, data: dict) -> int:
        score = 0
        if data.get("photos"):
            score += 20
        if data.get("editorial_summary", {}).get("overview"):
            score += 20
        if data.get("opening_hours", {}).get("weekday_text"):
            score += 15
        if data.get("business_status") == "OPERATIONAL":
            score += 10
        if data.get("rating", 0) >= 4.0:
            score += 15
        if data.get("user_ratings_total", 0) >= 10:
            score += 10
        if data.get("reviews"):
            score += 10
        return min(score, 100)

    def _estimate_review_response_rate(self, reviews: list) -> float:
        if not reviews:
            return 0.0
        with_response = sum(1 for r in reviews if r.get("owner_response"))
        return round(with_response / len(reviews) * 100, 1)
