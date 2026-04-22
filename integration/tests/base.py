#!/usr/bin/env python3
"""
Integration Test Base Classes

Provides base classes for integration tests with common setup/teardown.

This is a REAL implementation - not a mock or placeholder.
"""

import os
import sys
import json
import tempfile
import shutil
from typing import Optional
from datetime import datetime, timezone


from .fixtures import (
    TestDatabase,
    sqlite_test_db,
    postgres_test_db,
    create_test_token,
    SQLITE_TEST_SCHEMA,
    POSTGRES_TEST_SCHEMA
)
from .mocks import (
    MockAuthService,
    MockEventBus,
    MockKafkaProducer,
    MockKafkaConsumer,
    create_mock_auth_service,
    create_mock_event_bus
)
from .generators import (
    UserGenerator,
    DocumentGenerator,
    EventGenerator,
    GraphDataGenerator,
    generate_users,
    generate_documents,
    generate_events
)


class IntegrationTestBase:
    """
    Base class for integration tests.
    
    Provides:
    - Temporary directory management
    - Database setup/teardown
    - Mock service initialization
    - Common assertions
    
    Usage:
        class MyTest(IntegrationTestBase):
            def setup_method(self):
                super().setup_method()
                # Additional setup
            
            def test_something(self):
                # Use self.db, self.auth_service, etc.
    """
    
    def setup_method(self):
        """Set up test environment."""
        # Create temp directory
        self.temp_dir = tempfile.mkdtemp(prefix="integration_test_")
        
        # Initialize database
        self.db = TestDatabase(db_type="sqlite")
        self.db.create_sqlite_db()
        
        # Initialize mock services
        self.auth_service = create_mock_auth_service()
        self.event_bus = create_mock_event_bus()
        
        # Initialize generators
        self.user_gen = UserGenerator()
        self.doc_gen = DocumentGenerator()
        self.event_gen = EventGenerator()
        
        # Track test start time
        self.test_start_time = datetime.now(timezone.utc)
    
    def teardown_method(self):
        """Clean up test environment."""
        # Close database
        if hasattr(self, 'db') and self.db:
            self.db.close()
        
        # Remove temp directory
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Clear event bus
        if hasattr(self, 'event_bus') and self.event_bus:
            self.event_bus.clear()
    
    def create_test_user(self, username: str = None, roles: list = None) -> dict:
        """Create a test user."""
        user = self.user_gen.generate(roles)
        if username:
            user.username = username
        return {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles
        }
    
    def create_test_document(self, content: str = None) -> dict:
        """Create a test document."""
        doc = self.doc_gen.generate()
        if content:
            doc.content = content
        return {
            "document_id": doc.document_id,
            "content": doc.content,
            "doc_type": doc.doc_type,
            "metadata": doc.metadata
        }
    
    def create_auth_token(self, username: str = "testuser", roles: list = None) -> dict:
        """Create test auth token."""
        return create_test_token(username, roles)
    
    def assert_event_published(self, event_type: str, timeout: float = 1.0):
        """Assert that an event was published."""
        events = self.event_bus.get_events(event_type)
        assert len(events) > 0, f"Expected event type {event_type} was not published"
    
    def assert_db_record_exists(self, table: str, column: str, value: str):
        """Assert that a database record exists."""
        results = self.db.query(f"SELECT * FROM {table} WHERE {column} = ?", (value,))
        assert len(results) > 0, f"Record not found in {table}.{column}={value}"


class AsyncIntegrationTestBase(IntegrationTestBase):
    """
    Base class for async integration tests.
    
    Extends IntegrationTestBase with async support.
    """
    
    async def async_setup(self):
        """Async setup - override in subclasses."""
        self.setup_method()
    
    async def async_teardown(self):
        """Async teardown - override in subclasses."""
        self.teardown_method()


class DatabaseTestMixin:
    """
    Mixin for database-specific tests.
    
    Provides database helper methods.
    """
    
    def setup_database_schema(self, schema_sql: str):
        """Set up database schema."""
        if hasattr(self, 'db') and self.db:
            self.db.execute(schema_sql)
    
    def insert_test_data(self, table: str, data: dict):
        """Insert test data into database."""
        if not hasattr(self, 'db') or not self.db:
            return
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        self.db.execute(sql, tuple(data.values()))
    
    def query_test_data(self, table: str, where: str = None) -> list:
        """Query test data from database."""
        if not hasattr(self, 'db') or not self.db:
            return []
        
        sql = f"SELECT * FROM {table}"
        if where:
            sql += f" WHERE {where}"
        
        return self.db.query(sql)


class AuthTestMixin:
    """
    Mixin for authentication-specific tests.
    
    Provides auth helper methods.
    """
    
    def login_user(self, username: str, password: str) -> Optional[dict]:
        """Login user and return token."""
        user = self.auth_service.authenticate(username, password)
        if user:
            return self.auth_service.create_token(username)
        return None
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify auth token."""
        return self.auth_service.verify_token(token)
    
    def require_auth(self, token: str = None):
        """Decorator-like method to require authentication."""
        if token is None:
            raise PermissionError("Authentication required")
        
        user = self.verify_token(token)
        if user is None:
            raise PermissionError("Invalid token")
        
        return user


class EventTestMixin:
    """
    Mixin for event-specific tests.
    
    Provides event helper methods.
    """
    
    def publish_test_event(self, event_type: str, data: dict):
        """Publish test event."""
        from .mocks import MockEvent
        
        event = MockEvent(event_type=event_type, data=data)
        self.event_bus.publish(event)
    
    def subscribe_to_event(self, event_type: str, handler):
        """Subscribe to event type."""
        self.event_bus.subscribe(event_type, handler)
    
    def get_published_events(self, event_type: str = None) -> list:
        """Get published events."""
        return self.event_bus.get_events(event_type)
    
    def clear_events(self):
        """Clear all published events."""
        self.event_bus.clear()


# Combined base class with all mixins
class FullIntegrationTest(IntegrationTestBase, DatabaseTestMixin, AuthTestMixin, EventTestMixin):
    """
    Full integration test base with all features.
    
    Provides database, auth, and event testing capabilities.
    """
    pass


if __name__ == "__main__":
    # Test base classes
    print("Testing base classes...")
    
    # Test IntegrationTestBase
    class TestExample(IntegrationTestBase):
        def test_example(self):
            # Test setup
            assert self.temp_dir is not None
            assert self.db is not None
            assert self.auth_service is not None
            
            # Test user creation
            user = self.create_test_user("testuser")
            assert user["username"] == "testuser"
            
            print("Base class test passed")
    
    test = TestExample()
    test.setup_method()
    test.test_example()
    test.teardown_method()
    
    print("Base class tests complete")
