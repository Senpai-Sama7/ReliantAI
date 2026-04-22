"""
Pytest configuration and shared fixtures.
"""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Generator, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.api.routes import data as data_routes
from src.core.cache import cache_manager
from src.config import get_settings
from src.core.database import Base, get_db
from src.etl.pipeline import pipeline as default_pipeline
from src.main import app

pytest_plugins = ["pytest_asyncio"]

# Use a test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
settings = get_settings()

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture
async def test_db(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session

@pytest.fixture
def test_session_factory(test_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory bound to the test engine."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

@pytest_asyncio.fixture
async def override_get_db(test_db: AsyncSession) -> AsyncGenerator[None, None]:
    """Override the get_db dependency."""
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def override_pipeline_session_factory(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> Generator[None, None, None]:
    """Run route-driven ETL work against the same test database as the API."""
    original_session_factory = default_pipeline.session_factory
    default_pipeline.session_factory = test_session_factory
    try:
        yield
    finally:
        default_pipeline.session_factory = original_session_factory


@pytest.fixture(autouse=True)
def mock_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set a dummy JWT secret for local token validation fallback."""
    monkeypatch.setenv("JWT_SECRET", "test_secret")
    # Also patch the validator's secret instance if it's already loaded
    import src.api.auth_integration as auth
    if auth.validator:
        monkeypatch.setattr(auth.validator, "_secret", "test_secret")

@pytest.fixture
def test_jwt_token() -> str:
    """Generate a valid test JWT."""
    payload = {
        "sub": "testuser",
        "username": "testuser",
        "tenant_id": "test-tenant",
        "roles": ["ADMIN", "USER"],
        "service_name": "bap-test"
    }
    return jwt.encode(payload, "test_secret", algorithm="HS256")

@pytest_asyncio.fixture
async def async_client(
    override_get_db: None
) -> AsyncGenerator[AsyncClient, None]:
    """Create an unauthenticated async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def authenticated_client(
    override_get_db: None, test_jwt_token: str
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client with authentication headers."""
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {test_jwt_token}"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac


@pytest.fixture(autouse=True)
def isolate_uploads_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    """Prevent upload tests from writing into the repository tree."""
    upload_root = tmp_path / "uploads"
    monkeypatch.setattr(data_routes.settings, "UPLOADS_DIR", str(upload_root))
    yield

@pytest_asyncio.fixture(autouse=True)
async def mock_cache_manager(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[None, None]:
    """Mock the global cache manager to use a local dictionary instead of Redis."""
    store: dict[str, str] = {}
    
    async def mock_connect() -> Any:
        return cache_manager
        
    async def mock_close() -> None:
        pass
        
    async def mock_get(key: str) -> Optional[Any]:
        import json
        value = store.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
        
    async def mock_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
        import json
        if not isinstance(value, str):
            value = json.dumps(value)
        store[key] = value
        return True
        
    async def mock_delete(key: str) -> int:
        if key in store:
            del store[key]
            return 1
        return 0
        
    async def mock_exists(key: str) -> bool:
        return key in store
        
    async def mock_clear() -> bool:
        store.clear()
        return True
    
    monkeypatch.setattr(cache_manager, "connect", mock_connect)
    monkeypatch.setattr(cache_manager, "close", mock_close)
    monkeypatch.setattr(cache_manager, "get", mock_get)
    monkeypatch.setattr(cache_manager, "set", mock_set)
    monkeypatch.setattr(cache_manager, "delete", mock_delete)
    monkeypatch.setattr(cache_manager, "exists", mock_exists)
    monkeypatch.setattr(cache_manager, "clear", mock_clear)
    
    yield

@pytest_asyncio.fixture
async def test_cache(mock_cache_manager: None) -> AsyncGenerator[Any, None]:
    """Provide the mocked cache manager."""
    yield cache_manager

@pytest.fixture(autouse=True)
def mock_gemini() -> Generator[MagicMock, None, None]:
    """Mock the Gemini client to avoid external API calls during tests."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Mocked AI forecast for the provided data."
    mock_client.models.generate_content = AsyncMock(return_value=mock_response)

    @asynccontextmanager
    async def fake_client() -> AsyncGenerator[MagicMock, None]:
        yield mock_client

    with patch("src.ai.llm_client._get_async_client", fake_client):
        yield mock_client
