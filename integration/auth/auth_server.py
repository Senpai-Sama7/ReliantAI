"""
ReliantAI Auth Service - Production JWT Authentication with RBAC
NO MOCKING - Real Redis, real bcrypt, real JWT
"""

import inspect
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional
import os

from fastapi import FastAPI, HTTPException, Depends, Request, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from shared.audit import emit_audit
except ImportError:
    from integration.shared.audit import emit_audit
from pydantic import BaseModel, Field
from jose import JWTError, jwt
import bcrypt
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import structlog

from rate_limiter import SlidingWindowRateLimiter
from user_store import SQLiteUserStore, UserStoreConflictError

# Configuration — lazy validation to avoid crashing at import time
_SECRET_KEY_RAW = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = "HS256"


def _require_secret_key() -> str:
    key = _SECRET_KEY_RAW
    if not key:
        raise RuntimeError(
            "FATAL: AUTH_SECRET_KEY environment variable is not set. "
            'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
        )
    if len(key) < 32:
        raise RuntimeError("FATAL: AUTH_SECRET_KEY must be at least 32 characters.")
    return key


SECRET_KEY: str = _SECRET_KEY_RAW or ""
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("AUTH_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
AUTH_DB_PATH_ENV = "AUTH_DB_PATH"
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60"))
REGISTER_RATE_LIMIT = int(os.getenv("AUTH_REGISTER_RATE_LIMIT", "5"))
TOKEN_RATE_LIMIT = int(os.getenv("AUTH_TOKEN_RATE_LIMIT", "10"))

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Logging
logger = structlog.get_logger()

# Metrics
token_issued = Counter("auth_token_issued_total", "Total tokens issued", ["token_type"])
token_validation = Counter(
    "auth_token_validation_total", "Total token validations", ["status"]
)
login_failures = Counter(
    "auth_login_failures_total", "Total login failures", ["reason"]
)
request_duration = Histogram(
    "auth_request_duration_seconds", "Request duration", ["endpoint"]
)
rate_limit_rejections = Counter(
    "auth_rate_limit_rejections_total", "Rejected auth requests", ["endpoint"]
)


# Models
class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    TECHNICIAN = "technician"


class User(BaseModel):
    username: str
    email: str
    tenant_id: str
    role: Role
    hashed_password: str


class Tenant(BaseModel):
    tenant_id: str
    name: str
    active: bool = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=8)
    tenant_id: str
    role: Role = Role.TECHNICIAN


class TokenVerifyResponse(BaseModel):
    valid: bool
    user_id: str
    username: str
    tenant_id: str
    role: str
    roles: list[str]


class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


# Role permissions hierarchy
ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN: [
        Permission.READ,
        Permission.WRITE,
        Permission.DELETE,
        Permission.ADMIN,
    ],
    Role.ADMIN: [Permission.READ, Permission.WRITE, Permission.DELETE],
    Role.OPERATOR: [Permission.READ, Permission.WRITE],
    Role.TECHNICIAN: [Permission.READ],
}

redis_client: Optional[redis.Redis] = None
user_store: Optional[SQLiteUserStore] = None
rate_limiter: Optional[SlidingWindowRateLimiter] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and tear down service dependencies for the app lifecycle."""
    await initialize_services()
    try:
        yield
    finally:
        await shutdown_services()


# App
app = FastAPI(title="ReliantAI Auth Service", lifespan=lifespan)


def get_auth_db_path() -> Path:
    """Return the configured SQLite path for persisted users."""
    return Path(os.getenv(AUTH_DB_PATH_ENV, Path(__file__).with_name("auth.db")))


def get_redis_url() -> str:
    """Build the Redis URL from configured host and port."""
    return f"redis://{REDIS_HOST}:{REDIS_PORT}"


def serialize_user(user: User) -> dict[str, str]:
    """Serialize a user model to string fields for Redis and SQLite storage."""
    return user.model_dump(mode="json")


async def maybe_await(value: Any) -> Any:
    """Await async factories while also accepting synchronous test doubles."""
    if inspect.isawaitable(value):
        return await value
    return value


async def cache_user(user: User) -> None:
    """Write a persisted user into Redis for low-latency lookups."""
    if redis_client is None:
        return
    await redis_client.hset(f"user:{user.username}", mapping=serialize_user(user))


async def warm_user_cache() -> int:
    """Hydrate Redis from SQLite on service startup."""
    if redis_client is None or user_store is None:
        return 0

    hydrated = 0
    for user_data in await user_store.list_users():
        await redis_client.hset(f"user:{user_data['username']}", mapping=user_data)
        hydrated += 1
    return hydrated


async def initialize_services(
    redis_factory: Optional[Callable[..., Awaitable[Any] | Any]] = None,
    db_path: Optional[str | Path] = None,
) -> None:
    """Initialize Redis and the persistent SQLite user store."""
    global redis_client, user_store, rate_limiter

    user_store = SQLiteUserStore(db_path or get_auth_db_path())
    applied_migrations = await user_store.initialize()

    # Validate auth secret key at startup (not import time)
    if not SECRET_KEY or len(SECRET_KEY) < 32:
        raise RuntimeError(
            "FATAL: AUTH_SECRET_KEY environment variable is not set or too short. "
            'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
        )

    factory = redis_factory or redis.from_url
    redis_client = await maybe_await(
        factory(
            get_redis_url(),
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
    )
    await redis_client.ping()
    rate_limiter = SlidingWindowRateLimiter(redis_client)

    hydrated_users = await warm_user_cache()
    logger.info(
        "auth_service_started",
        redis_url=get_redis_url(),
        sqlite_path=str(user_store.db_path),
        hydrated_users=hydrated_users,
        applied_migrations=applied_migrations,
    )


async def shutdown_services() -> None:
    """Close service resources and clear globals for clean restarts."""
    global redis_client, user_store, rate_limiter

    if redis_client is not None:
        if hasattr(redis_client, "aclose"):
            await redis_client.aclose()
        else:
            await redis_client.close()
    redis_client = None
    user_store = None
    rate_limiter = None
    logger.info("auth_service_stopped")


# Core Functions
def hash_password(password: str) -> str:
    """Hash password with bcrypt cost factor 12. Truncates to 72 bytes (bcrypt limit)."""
    truncated = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(truncated, bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against bcrypt hash. Truncates to 72 bytes (bcrypt limit)."""
    truncated = plain.encode("utf-8")[:72]
    return bcrypt.checkpw(truncated, hashed.encode("utf-8"))


def create_token(data: dict, expires_delta: timedelta) -> str:
    """Create JWT token with expiration"""
    to_encode = data.copy()
    issued_at = datetime.now(UTC)
    expire = issued_at + expires_delta
    to_encode.update({"exp": expire, "iat": issued_at, "iss": "auth-service-key"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_user(username: str) -> Optional[User]:
    """Get a user from Redis, falling back to SQLite on cache miss."""
    if redis_client is not None:
        try:
            user_data = await redis_client.hgetall(f"user:{username}")
        except Exception as exc:
            logger.warning(
                "redis_user_lookup_failed", username=username, error=str(exc)
            )
        else:
            if user_data:
                return User(**user_data)

    if user_store is None:
        return None

    user_data = await user_store.get_user(username)
    if not user_data:
        return None

    user = User(**user_data)
    try:
        await cache_user(user)
    except Exception as exc:
        logger.warning("redis_user_rehydrate_failed", username=username, error=str(exc))
    return user


async def store_user(user: User):
    """Store user durably in SQLite, then write through into Redis."""
    if user_store is None:
        raise RuntimeError("User store has not been initialized")

    try:
        await user_store.create_user(serialize_user(user))
    except UserStoreConflictError as exc:
        raise HTTPException(
            status_code=400, detail="Username or email already exists"
        ) from exc

    try:
        await cache_user(user)
    except Exception as exc:
        logger.warning(
            "redis_user_cache_write_failed", username=user.username, error=str(exc)
        )


async def revoke_token(token: str):
    """Add token to revocation list"""
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")
    await redis_client.setex(f"revoked:{token}", 86400 * 7, "1")


async def is_token_revoked(token: str) -> bool:
    """Check if token is revoked. Fail-closed: assume revoked if Redis unavailable."""
    if redis_client is None:
        return True
    return await redis_client.exists(f"revoked:{token}") > 0


def has_permission(role: Role, permission: Permission) -> bool:
    """Check if role has permission"""
    return permission in ROLE_PERMISSIONS.get(role, [])


async def track_failed_login(username: str) -> bool:
    """Track failed login attempts, return True if account should be locked"""
    if redis_client is None:
        return False
    key = f"failed_login:{username}"
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, 900)  # 15 minutes
    return count >= 5


async def reset_failed_login(username: str):
    """Reset failed login counter"""
    if redis_client is None:
        return
    await redis_client.delete(f"failed_login:{username}")


async def is_account_locked(username: str) -> bool:
    """Check if account is locked due to failed attempts"""
    if redis_client is None:
        return False
    count = await redis_client.get(f"failed_login:{username}")
    return bool(count and int(count) >= 5)


def get_client_identifier(request: Request) -> str:
    """Resolve the client IP, honoring forwarded headers when present."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


async def enforce_rate_limit(request: Request, endpoint: str, limit: int) -> None:
    """Reject requests that exceed the configured sliding-window limit."""
    if rate_limiter is None:
        raise RuntimeError("Rate limiter has not been initialized")

    decision = await rate_limiter.check(
        scope=endpoint,
        identifier=get_client_identifier(request),
        limit=limit,
        window_seconds=RATE_LIMIT_WINDOW_SECONDS,
    )
    if decision.allowed:
        return

    rate_limit_rejections.labels(endpoint=endpoint).inc()
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Rate limit exceeded for /{endpoint}",
        headers={"Retry-After": str(decision.retry_after)},
    )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Dependency to get current user from token"""
    try:
        if await is_token_revoked(token):
            raise HTTPException(status_code=401, detail="Token revoked")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")

        role_str = payload.get("role")
        try:
            role = Role(role_str) if role_str else Role.TECHNICIAN
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid role in token")
        return {
            "username": payload.get("sub"),
            "tenant_id": payload.get("tenant_id"),
            "role": role,
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_permission(permission: Permission):
    """Dependency to require specific permission"""

    async def permission_checker(current_user: dict = Depends(get_current_user)):
        if not has_permission(current_user["role"], permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission.value} required",
            )
        return current_user

    return permission_checker


def require_tenant(tenant_id: str):
    """Dependency to enforce tenant isolation"""

    async def tenant_checker(current_user: dict = Depends(get_current_user)):
        # Super admin can access all tenants
        if current_user["role"] == Role.SUPER_ADMIN:
            return current_user

        # Others must match tenant_id
        if current_user["tenant_id"] != tenant_id:
            raise HTTPException(
                status_code=403, detail="Access denied: tenant isolation violation"
            )
        return current_user

    return tenant_checker


# Endpoints
@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest, request: Request, background_tasks: BackgroundTasks
):
    """Register new user"""
    with request_duration.labels(endpoint="register").time():
        await enforce_rate_limit(request, "register", REGISTER_RATE_LIMIT)

        # Prevent role escalation
        if req.role not in {Role.TECHNICIAN, Role.OPERATOR}:
            login_failures.labels(reason="role_escalation").inc()
            background_tasks.add_task(
                emit_audit,
                action="register_role_escalation_attempt",
                actor=req.username,
                target=req.role.value,
                tenant_id=req.tenant_id,
                source_service="auth_service",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Self-registration is not allowed for role: {req.role.value}",
            )

        # Create user
        user = User(
            username=req.username,
            email=req.email,
            tenant_id=req.tenant_id,
            role=req.role,
            hashed_password=hash_password(req.password),
        )
        try:
            await store_user(user)
        except HTTPException:
            login_failures.labels(reason="user_exists").inc()
            raise

        logger.info("user_registered", username=req.username, tenant_id=req.tenant_id)
        background_tasks.add_task(
            emit_audit,
            action="user_registered",
            actor=req.username,
            tenant_id=req.tenant_id,
            source_service="auth_service",
            details={"email": req.email, "role": req.role.value},
        )
        return {"message": "User registered successfully", "username": req.username}


@app.post("/token", response_model=TokenResponse)
async def login(
    request: Request,
    background_tasks: BackgroundTasks,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """Issue access and refresh tokens"""
    with request_duration.labels(endpoint="token").time():
        await enforce_rate_limit(request, "token", TOKEN_RATE_LIMIT)
        # Check account lockout
        if await is_account_locked(form_data.username):
            login_failures.labels(reason="account_locked").inc()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to too many failed login attempts. Try again in 15 minutes.",
            )

        # Get user
        user = await get_user(form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            await track_failed_login(form_data.username)
            login_failures.labels(reason="invalid_credentials").inc()
            background_tasks.add_task(
                emit_audit,
                action="login_failed",
                actor=form_data.username,
                source_service="auth_service",
                details={"reason": "invalid_credentials"},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Reset failed login counter on success
        await reset_failed_login(form_data.username)

        # Create tokens
        access_token = create_token(
            {
                "sub": user.username,
                "tenant_id": user.tenant_id,
                "role": user.role.value,
                "type": "access",
            },
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_token(
            {"sub": user.username, "tenant_id": user.tenant_id, "type": "refresh"},
            timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )

        token_issued.labels(token_type="access").inc()
        token_issued.labels(token_type="refresh").inc()
        logger.info("tokens_issued", username=user.username, tenant_id=user.tenant_id)

        background_tasks.add_task(
            emit_audit,
            action="user_login",
            actor=user.username,
            tenant_id=user.tenant_id,
            source_service="auth_service",
            details={"role": user.role.value},
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


@app.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: str = Body(..., embed=True)):
    """Refresh access token using refresh token"""
    with request_duration.labels(endpoint="refresh").time():
        try:
            # Check revocation
            if await is_token_revoked(refresh_token):
                token_validation.labels(status="revoked").inc()
                raise HTTPException(status_code=401, detail="Token has been revoked")

            # Decode refresh token
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")

            username = payload.get("sub")
            tenant_id = payload.get("tenant_id")

            # Get user for role
            user = await get_user(username)
            if not user:
                raise HTTPException(status_code=401, detail="User not found")

            # Create new access token
            access_token = create_token(
                {
                    "sub": username,
                    "tenant_id": tenant_id,
                    "role": user.role.value,
                    "type": "access",
                },
                timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            )

            token_issued.labels(token_type="access").inc()
            token_validation.labels(status="success").inc()

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )
        except JWTError as e:
            token_validation.labels(status="invalid").inc()
            raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/verify", response_model=TokenVerifyResponse)
@app.post("/verify", response_model=TokenVerifyResponse)
async def verify(token: str = Depends(oauth2_scheme)):
    """Verify JWT token"""
    with request_duration.labels(endpoint="verify").time():
        try:
            # Check revocation
            if await is_token_revoked(token):
                token_validation.labels(status="revoked").inc()
                raise HTTPException(status_code=401, detail="Token has been revoked")

            # Decode token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "access":
                raise HTTPException(status_code=401, detail="Invalid token type")

            token_validation.labels(status="success").inc()
            username = payload.get("sub") or ""
            role = payload.get("role") or ""
            return TokenVerifyResponse(
                valid=True,
                user_id=username,
                username=username,
                tenant_id=payload.get("tenant_id"),
                role=role,
                roles=[role] if role else [],
            )
        except JWTError as e:
            token_validation.labels(status="invalid").inc()
            raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/revoke")
async def revoke(token: str = Depends(oauth2_scheme)):
    """Revoke token"""
    with request_duration.labels(endpoint="revoke").time():
        await revoke_token(token)
        logger.info("token_revoked")
        return {"message": "Token revoked successfully"}


@app.get("/health")
async def health():
    """Health check — returns minimal status only, no internal details"""
    try:
        await redis_client.ping()
        if user_store is not None:
            await user_store.ping()
        return {"status": "healthy"}
    except Exception:
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/metrics")
async def metrics(
    _current_user: dict = Depends(get_current_user),
):
    """Prometheus metrics — requires authentication"""
    return Response(content=generate_latest(), media_type="text/plain")


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = "default-src 'none'"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return response


# RBAC Test Endpoints
@app.get("/protected/read")
async def protected_read(
    current_user: dict = Depends(require_permission(Permission.READ)),
):
    """Test endpoint requiring READ permission"""
    return {"message": "Read access granted", "user": current_user["username"]}


@app.post("/protected/write")
async def protected_write(
    current_user: dict = Depends(require_permission(Permission.WRITE)),
):
    """Test endpoint requiring WRITE permission"""
    return {"message": "Write access granted", "user": current_user["username"]}


@app.delete("/protected/delete")
async def protected_delete(
    current_user: dict = Depends(require_permission(Permission.DELETE)),
):
    """Test endpoint requiring DELETE permission"""
    return {"message": "Delete access granted", "user": current_user["username"]}


@app.get("/protected/admin")
async def protected_admin(
    current_user: dict = Depends(require_permission(Permission.ADMIN)),
):
    """Test endpoint requiring ADMIN permission"""
    return {"message": "Admin access granted", "user": current_user["username"]}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("AUTH_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
