"""
Prospecting agent — continuously finds new home services businesses
that don't have good websites, research them, and queue them for site generation.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import structlog

from ..core.base import AgentConfig, AgentResult, BaseAgent
from ..core.memory import AgentMemory

logger = structlog.get_logger("agents.prospector")

# Trades we target, in priority order
TARGET_TRADES = [
    "hvac", "plumbing", "electrical", "roofing",
    "painting", "landscaping", "pest_control", "locksmith",
]

# States with high home-services demand
PRIORITY_STATES = ["TX", "FL", "CA", "AZ", "NY", "NC", "GA", "CO", "WA", "TN"]

# Large metro areas to target first
PRIORITY_CITIES = [
    ("Houston", "TX"), ("Dallas", "TX"), ("Austin", "TX"), ("San Antonio", "TX"),
    ("Miami", "FL"), ("Orlando", "FL"), ("Tampa", "FL"), ("Jacksonville", "FL"),
    ("Los Angeles", "CA"), ("San Diego", "CA"), ("Phoenix", "AZ"),
    ("New York", "NY"), ("Charlotte", "NC"), ("Atlanta", "GA"),
    ("Denver", "CO"), ("Seattle", "WA"), ("Nashville", "TN"),
]


class ProspectingAgent(BaseAgent):
    """
    Autonomous agent that finds and qualifies new prospects.

    On each iteration:
    1. Picks the next trade/city combo from the rotation
    2. Searches Google Places for businesses in that trade/area
    3. Filters for businesses with poor web presence (low reviews, no website)
    4. Researches each qualifying business via GBP API
    5. Inserts qualified prospects into the database
    6. Queues them for the pipeline (Celery task)
    """

    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig(
            name="prospector",
            poll_interval_seconds=float(os.environ.get("PROSPECTOR_POLL_SECONDS", "60")),
        ))
        self.memory = AgentMemory()
        self.places_api_key = os.environ.get("GOOGLE_PLACES_API_KEY", "")
        self._rotation_index = 0

    def _operation_name(self) -> str:
        return "prospect"

    async def _check_for_work(self) -> bool:
        """Always has work — there are always more businesses to find."""
        if not self.places_api_key:
            self.logger.warning("no_places_api_key", hint="Set GOOGLE_PLACES_API_KEY")
            return False
        return True

    async def _execute(self) -> dict[str, Any]:
        """Find and qualify new prospects."""
        trade, city, state = self._next_target()
        self.logger.info("searching", trade=trade, city=city, state=state)

        # Search Google Places
        places = await self._search_places(trade, city, state)
        self.logger.info("places_found", count=len(places), trade=trade, city=city)

        # Filter for businesses with poor web presence
        qualified = []
        for place in places:
            score = self._score_prospect(place)
            if score >= 50:  # Threshold for qualification
                qualified.append((place, score))

        self.logger.info("qualified", count=len(qualified), trade=trade, city=city)

        # Insert into DB and queue
        queued = 0
        for place, score in qualified:
            prospect_id = await self._insert_prospect(place, trade, city, state)
            if prospect_id:
                await self._queue_pipeline(prospect_id)
                queued += 1

        result = {
            "trade": trade,
            "city": city,
            "state": state,
            "found": len(places),
            "qualified": len(qualified),
            "queued": queued,
        }
        self.logger.info("prospecting_complete", **result)
        self.memory.log_event(self.name, "prospecting_run", result)
        return result

    def _next_target(self) -> tuple[str, str, str]:
        """Rotate through trade/city combinations."""
        idx = self._rotation_index
        trade = TARGET_TRADES[idx % len(TARGET_TRADES)]
        city, state = PRIORITY_CITIES[idx % len(PRIORITY_CITIES)]
        self._rotation_index = (idx + 1) % (len(TARGET_TRADES) * len(PRIORITY_CITIES))
        return trade, city, state

    def _score_prospect(self, place: dict) -> int:
        """
        Score a prospect 0-100 based on potential value.
        Higher score = better target for our service.
        """
        score = 0
        # Has reviews but no website = perfect target
        review_count = place.get("user_ratings_total", 0)
        if review_count > 0:
            score += min(review_count, 30)  # Up to 30 points for reviews
        if not place.get("website"):
            score += 40  # No website = prime target
        rating = place.get("rating", 0)
        if rating >= 4.0:
            score += 20  # Good rating = successful business
        elif rating >= 3.0:
            score += 10
        # Business status
        if place.get("business_status") == "OPERATIONAL":
            score += 10
        return min(score, 100)

    async def _search_places(self, trade: str, city: str, state: str) -> list[dict]:
        """Search Google Places API for businesses."""
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        # Get city coordinates roughly
        geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                geo = await client.get(geocode_url, params={
                    "address": f"{city}, {state}",
                    "key": self.places_api_key,
                })
                geo_data = geo.json()
                if geo_data.get("results"):
                    loc = geo_data["results"][0]["geometry"]["location"]
                else:
                    return []
            except Exception as e:
                self.logger.error("geocode_failed", error=str(e))
                return []

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url, params={
                    "location": f"{loc['lat']},{loc['lng']}",
                    "radius": 25000,
                    "keyword": f"{trade} contractor",
                    "key": self.places_api_key,
                    "type": "establishment",
                })
                data = resp.json()
                return data.get("results", [])
            except Exception as e:
                self.logger.error("places_search_failed", error=str(e))
                return []

    async def _insert_prospect(self, place: dict, trade: str, city: str, state: str) -> str | None:
        """Insert a new prospect into the database, skipping duplicates."""
        from ...db import get_db_session
        from ...db.models import Prospect

        place_id = place.get("place_id", "")
        business_name = place.get("name", "")
        phone = place.get("formatted_phone_number", "")
        address = place.get("formatted_address", "")
        lat = place.get("geometry", {}).get("location", {}).get("lat")
        lng = place.get("geometry", {}).get("location", {}).get("lng")
        rating = place.get("rating")
        review_count = place.get("user_ratings_total", 0)
        website = place.get("website", "")

        with get_db_session() as db:
            # Skip if already exists
            existing = db.query(Prospect).filter_by(place_id=place_id).first()
            if existing:
                self.logger.debug("prospect_exists", business_name=business_name)
                return None

            prospect = Prospect(
                place_id=place_id,
                business_name=business_name,
                trade=trade,
                city=city,
                state=state,
                phone=phone,
                address=address,
                lat=lat,
                lng=lng,
                google_rating=rating,
                review_count=review_count,
                website_url=website,
                status="identified",
            )
            db.add(prospect)
            db.flush()
            prospect_id = prospect.id

        self.logger.info(
            "prospect_inserted",
            business_name=business_name,
            trade=trade,
            city=city,
        )
        return prospect_id

    async def _queue_pipeline(self, prospect_id: str) -> None:
        """Queue a prospect for the full pipeline via Celery."""
        try:
            from ...tasks.prospect_tasks import run_prospect_pipeline
            run_prospect_pipeline.delay(prospect_id)
            self.logger.info("pipeline_queued", prospect_id=prospect_id)
        except Exception as e:
            self.logger.warning("queue_failed", prospect_id=prospect_id, error=str(e))
