import os
import requests
import googlemaps
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()
app = FastAPI(title="ReliantAI GrowthEngine", version="1.0.0")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.environ.get("API_KEY", "local-dev-api-key")
    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return api_key

class ScanRequest(BaseModel):
    lat: float
    lng: float
    radius_meters: int = 5000
    keyword: str = "home services"

class OutreachRequest(BaseModel):
    place_id: str
    name: str
    phone: str
    rating: float
    review_count: int

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/prospect/scan")
def scan_prospects(req: ScanRequest, _: str = Depends(verify_api_key)):
    google_api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not google_api_key:
        raise HTTPException(status_code=503, detail="GOOGLE_PLACES_API_KEY not configured")
        
    gmaps = googlemaps.Client(key=google_api_key)
    
    try:
        places = gmaps.places_nearby(
            location=(req.lat, req.lng),
            radius=req.radius_meters,
            keyword=req.keyword,
            type="store"
        )
        
        prospects = []
        for p in places.get('results', []):
            rating = p.get('rating', 0)
            reviews = p.get('user_ratings_total', 0)
            
            if rating >= 4.5 and reviews > 20:
                details = gmaps.place(place_id=p['place_id'], fields=['name', 'formatted_phone_number', 'website', 'rating', 'user_ratings_total'])
                detail_result = details.get('result', {})
                
                if not detail_result.get('website'):
                    prospects.append({
                        "place_id": p['place_id'],
                        "name": detail_result.get('name'),
                        "phone": detail_result.get('formatted_phone_number'),
                        "rating": detail_result.get('rating'),
                        "review_count": detail_result.get('user_ratings_total'),
                        "website": None
                    })
                    
        logger.info("prospects_scanned", count=len(prospects))
        return {"prospects": prospects}
    except Exception as e:
        logger.error("scan_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to scan places")

@app.post("/api/prospect/outreach")
def trigger_outreach(req: OutreachRequest, _: str = Depends(verify_api_key)):
    slug = req.name.lower().replace(" ", "-").replace("'", "")
    preview_url = f"https://reliantai.org/preview/{slug}"
    
    message = (
        f"Hey {req.name} team, I saw your {req.rating}-star rating on Google! "
        f"Your {req.review_count} reviews are amazing, but because you don't have a mobile-optimized website, "
        f"competitors might be stealing your local leads. I built a preview site for you: {preview_url} - Reply YES to claim it."
    )
    
    money_url = os.environ.get("MONEY_SERVICE_URL", "http://money:8000")
    dispatch_key = os.environ.get("DISPATCH_API_KEY", "")
    
    try:
        resp = requests.post(
            f"{money_url}/api/dispatch/sms",
            json={"to": req.phone, "body": message},
            headers={"X-API-Key": dispatch_key},
            timeout=10
        )
        resp.raise_for_status()
        logger.info("outreach_triggered", name=req.name, phone=req.phone, status=resp.status_code)
        return {"status": "outreach_queued", "preview_url": preview_url}
    except requests.HTTPError as e:
        logger.error("outreach_failed", status=resp.status_code, error=str(e))
        raise HTTPException(status_code=resp.status_code, detail="Failed to trigger outreach")
    except Exception as e:
        logger.error("outreach_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to trigger outreach")
