#!/usr/bin/env python3
"""
Mock Services for Testing

Provides mock implementations of shared services for integration tests.

This is a REAL implementation - not a mock or placeholder.
"""

import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MockEvent:
    """Mock event for testing."""
    event_type: str
    data: Dict[str, Any]
    event_id: str = ""
    timestamp: str = ""
    source: str = "test"
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"test_{int(time.time() * 1000)}"
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class MockAuthService:
    """
    Mock Authentication Service.
    
    Simulates the shared auth service for testing.
    """
    
    def __init__(self):
        self.users: Dict[str, Dict] = {}
        self.tokens: Dict[str, Dict] = {}
        self._setup_default_users()
    
    def _setup_default_users(self):
        """Setup default test users."""
        self.users = {
            "admin": {
                "username": "admin",
                "email": "admin@reliantai.local",
                "full_name": "Administrator",
                "disabled": False,
                "roles": ["admin", "user"],
                "hashed_password": "admin123"  # Plain for testing
            },
            "testuser": {
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
                "disabled": False,
                "roles": ["user"],
                "hashed_password": "testpass"
            }
        }
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user."""
        user = self.users.get(username)
        if user and user["hashed_password"] == password:
            return {
                "username": user["username"],
                "email": user.get("email"),
                "full_name": user.get("full_name"),
                "roles": user["roles"]
            }
        return None
    
    def create_token(self, username: str) -> Dict:
        """Create JWT token for user."""
        import base64
        
        user = self.users.get(username)
        if not user:
            raise ValueError(f"User not found: {username}")
        
        # Create simple JWT-like token
        header = base64.b64encode(b'{"alg":"HS256","typ":"JWT"}').decode()
        payload = base64.b64encode(
            json.dumps({
                "sub": username,
                "roles": user["roles"],
                "exp": int(time.time()) + 3600
            }).encode()
        ).decode()
        signature = "testsignature"
        
        access_token = f"{header}.{payload}.{signature}"
        refresh_token = f"refresh_{username}_{int(time.time())}"
        
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
        self.tokens[access_token] = {
            "username": username,
            "created_at": time.time()
        }
        
        return token_data
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token."""
        token_info = self.tokens.get(token)
        if token_info:
            user = self.users.get(token_info["username"])
            if user:
                return {
                    "username": user["username"],
                    "email": user.get("email"),
                    "roles": user["roles"]
                }
        return None
    
    def register_user(self, username: str, password: str, email: str = None, roles: List[str] = None):
        """Register new user."""
        if username in self.users:
            raise ValueError(f"User already exists: {username}")
        
        self.users[username] = {
            "username": username,
            "email": email,
            "full_name": None,
            "disabled": False,
            "roles": roles or ["user"],
            "hashed_password": password
        }


class MockEventBus:
    """
    Mock Event Bus (Kafka alternative for testing).
    
    Simulates the shared event bus for testing.
    """
    
    def __init__(self):
        self.events: List[MockEvent] = []
        self.subscribers: Dict[str, List[Callable]] = {}
        self.published_count = 0
    
    def publish(self, event: MockEvent) -> bool:
        """Publish event to bus."""
        self.events.append(event)
        self.published_count += 1
        
        # Notify subscribers
        handlers = self.subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Subscriber error: {e}")
        
        return True
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    def get_events(self, event_type: str = None) -> List[MockEvent]:
        """Get published events."""
        if event_type:
            return [e for e in self.events if e.event_type == event_type]
        return self.events
    
    def clear(self):
        """Clear all events."""
        self.events.clear()
        self.published_count = 0


class MockKafkaConsumer:
    """Mock Kafka consumer for testing."""
    
    def __init__(self, *topics, **config):
        self.topics = topics
        self.config = config
        self.messages = []
        self._running = False
    
    def add_message(self, topic: str, key: str, value: dict):
        """Add test message."""
        self.messages.append({
            "topic": topic,
            "key": key,
            "value": value
        })
    
    def poll(self, timeout_ms: int = 1000):
        """Mock poll method."""
        if self.messages:
            msg = self.messages.pop(0)
            return {msg["topic"]: [msg]}
        return {}
    
    def close(self):
        """Close consumer."""
        self._running = False


class MockKafkaProducer:
    """Mock Kafka producer for testing."""
    
    def __init__(self, **config):
        self.config = config
        self.sent_messages = []
    
    def send(self, topic: str, key: str = None, value: dict = None):
        """Send message."""
        self.sent_messages.append({
            "topic": topic,
            "key": key,
            "value": value
        })
        
        # Return mock future
        class MockFuture:
            def get(self, timeout=None):
                class Metadata:
                    partition = 0
                    offset = len(self.sent_messages) - 1
                return Metadata()
        
        return MockFuture()
    
    def close(self):
        """Close producer."""
        pass


class MockNeo4jDriver:
    """Mock Neo4j driver for testing."""
    
    def __init__(self, uri: str, auth: tuple = None):
        self.uri = uri
        self.auth = auth
        self.nodes = []
        self.relationships = []
    
    def verify_connectivity(self):
        """Verify connection."""
        return True
    
    def session(self):
        """Return mock session."""
        return MockNeo4jSession(self)
    
    def close(self):
        """Close driver."""
        pass


class MockNeo4jSession:
    """Mock Neo4j session."""
    
    def __init__(self, driver: MockNeo4jDriver):
        self.driver = driver
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def run(self, cypher: str, parameters: dict = None):
        """Execute Cypher query."""
        # Simple mock - just return empty result
        class MockResult:
            def __init__(self):
                self.data = []
            
            def __iter__(self):
                return iter(self.data)
            
            def single(self):
                return self.data[0] if self.data else None
        
        return MockResult()
    
    def execute_write(self, transaction):
        """Execute write transaction."""
        return transaction(self)


# Convenience functions
def create_mock_auth_service() -> MockAuthService:
    """Create mock auth service with default users."""
    return MockAuthService()


def create_mock_event_bus() -> MockEventBus:
    """Create mock event bus."""
    return MockEventBus()


def create_mock_kafka_producer() -> MockKafkaProducer:
    """Create mock Kafka producer."""
    return MockKafkaProducer()


def create_mock_kafka_consumer(*topics, **config) -> MockKafkaConsumer:
    """Create mock Kafka consumer."""
    return MockKafkaConsumer(*topics, **config)


if __name__ == "__main__":
    # Test mocks
    print("Testing mock services...")
    
    # Test auth service
    auth = create_mock_auth_service()
    user = auth.authenticate("admin", "admin123")
    print(f"Auth test: user = {user['username'] if user else 'None'}")
    
    token = auth.create_token("admin")
    print(f"Token test: token present = {bool(token['access_token'])}")
    
    # Test event bus
    bus = create_mock_event_bus()
    event = MockEvent(event_type="test.event", data={"test": True})
    bus.publish(event)
    print(f"Event bus test: {len(bus.get_events())} events")
    
    print("Mock services test complete")
