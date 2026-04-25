import hmac
import os
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    api_key = os.environ.get("API_SECRET_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="API key not configured")
    provided = credentials.credentials.encode("utf-8")
    expected = api_key.encode("utf-8")
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True
