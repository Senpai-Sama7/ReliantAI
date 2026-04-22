"""
Pytest fixtures for MAL integration tests.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock
import asyncpg


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def mock_db_pool():
    """Mock database pool for testing."""
    pool = AsyncMock(spec=asyncpg.Pool)
    conn = AsyncMock(spec=asyncpg.Connection)
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    return pool


@pytest_asyncio.fixture
async def engine(mock_db_pool):
    """Create a MetacognitiveEngine with mocked DB."""
    from ..engine import MetacognitiveEngine
    engine = MetacognitiveEngine(db_pool=mock_db_pool)
    return engine


@pytest_asyncio.fixture
async def healing_orchestrator(mock_db_pool):
    """Create a SelfHealingOrchestrator with mocked DB."""
    from ..healing_orchestrator import SelfHealingOrchestrator
    orchestrator = SelfHealingOrchestrator(db_pool=mock_db_pool)
    return orchestrator


@pytest_asyncio.fixture
async def feedback_collector(mock_db_pool):
    """Create a FeedbackCollector with mocked DB."""
    from ..feedback_collector import FeedbackCollector
    collector = FeedbackCollector(db_pool=mock_db_pool)
    return collector


@pytest_asyncio.fixture
async def intent_predictor(mock_db_pool):
    """Create an IntentPredictor with mocked DB."""
    from ..intent_predictor import IntentPredictor
    predictor = IntentPredictor(db_pool=mock_db_pool)
    return predictor


@pytest_asyncio.fixture
async def optimizer(mock_db_pool):
    """Create an AutonomousOptimizer with mocked DB."""
    from ..optimizer import AutonomousOptimizer
    opt = AutonomousOptimizer(db_pool=mock_db_pool)
    return opt


@pytest_asyncio.fixture
async def consolidator(mock_db_pool):
    """Create a KnowledgeConsolidator with mocked DB."""
    from ..knowledge_consolidator import KnowledgeConsolidator
    cons = KnowledgeConsolidator(db_pool=mock_db_pool)
    return cons


@pytest_asyncio.fixture
async def mal_system(mock_db_pool):
    """Create a full MetacognitiveAutonomySystem with mocked dependencies."""
    from ..main import MetacognitiveAutonomySystem
    from ..engine import MetacognitiveEngine
    from ..healing_orchestrator import SelfHealingOrchestrator
    from ..feedback_collector import FeedbackCollector
    from ..intent_predictor import IntentPredictor
    from ..optimizer import AutonomousOptimizer
    from ..knowledge_consolidator import KnowledgeConsolidator
    
    system = MetacognitiveAutonomySystem()
    system.engine = MetacognitiveEngine(db_pool=mock_db_pool)
    system.healing = SelfHealingOrchestrator(db_pool=mock_db_pool)
    system.feedback = FeedbackCollector(db_pool=mock_db_pool)
    system.predictor = IntentPredictor(db_pool=mock_db_pool)
    system.optimizer = AutonomousOptimizer(db_pool=mock_db_pool)
    system.consolidator = KnowledgeConsolidator(db_pool=mock_db_pool)
    
    return system
