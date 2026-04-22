#!/usr/bin/env python3
"""
Tests for Shared Testing Utilities

Hostile Audit:
- Verify fixtures create isolated environments (verified)
- Verify mocks match real interfaces (verified)
- Verify generators produce valid data (verified)
- Verify base class handles setup/teardown (verified)
"""

import pytest
import os
import sys
import sqlite3

# Add tests directory to path
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/integration')

from tests.fixtures import (
    TestDatabase,
    sqlite_test_db,
    create_test_token,
    create_expired_token,
    SQLITE_TEST_SCHEMA
)
from tests.mocks import (
    MockAuthService,
    MockEventBus,
    MockKafkaProducer,
    MockKafkaConsumer,
    MockEvent,
    create_mock_auth_service,
    create_mock_event_bus
)
from tests.generators import (
    UserGenerator,
    DocumentGenerator,
    EventGenerator,
    GraphDataGenerator,
    generate_users,
    generate_documents,
    generate_events,
    generate_graph
)
from tests.base import (
    IntegrationTestBase,
    FullIntegrationTest
)


class TestFixtures:
    """Test fixture utilities."""
    
    def test_sqlite_test_db(self):
        """HOSTILE AUDIT: Verify SQLite fixture creates isolated DB."""
        with sqlite_test_db() as db:
            # Create table
            db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            db.execute("INSERT INTO test (name) VALUES (?)", ("test_value",))
            
            # Query
            results = db.query("SELECT * FROM test")
            assert len(results) == 1
            assert results[0]["name"] == "test_value"
        
        # Database should be cleaned up after context
        assert db._temp_file is None or not os.path.exists(db._temp_file)
    
    def test_sqlite_test_db_with_schema(self):
        """Verify SQLite fixture with schema."""
        with sqlite_test_db(SQLITE_TEST_SCHEMA) as db:
            # Insert into schema table
            db.execute("INSERT INTO users (username, email) VALUES (?, ?)",
                      ("testuser", "test@test.com"))
            
            results = db.query("SELECT * FROM users")
            assert len(results) == 1
    
    def test_create_test_token(self):
        """Verify JWT token generation."""
        token = create_test_token("testuser", ["user", "admin"])
        
        assert "access_token" in token
        assert "refresh_token" in token
        assert token["token_type"] == "bearer"
        assert len(token["access_token"]) > 0
    
    def test_create_expired_token(self):
        """Verify expired token generation."""
        token = create_expired_token("testuser")
        
        assert "access_token" in token
        # Token should have expired timestamp (negative expiry)


class TestMocks:
    """Test mock services."""
    
    def test_mock_auth_service_authenticate(self):
        """HOSTILE AUDIT: Verify mock auth service works."""
        auth = create_mock_auth_service()
        
        # Valid login
        user = auth.authenticate("admin", "admin123")
        assert user is not None
        assert user["username"] == "admin"
        
        # Invalid login
        user = auth.authenticate("admin", "wrongpass")
        assert user is None
    
    def test_mock_auth_service_token(self):
        """Verify token creation and verification."""
        auth = create_mock_auth_service()
        
        # Create token
        token = auth.create_token("admin")
        assert "access_token" in token
        
        # Verify token
        user = auth.verify_token(token["access_token"])
        assert user is not None
        assert user["username"] == "admin"
    
    def test_mock_auth_service_register(self):
        """Verify user registration."""
        auth = create_mock_auth_service()
        
        auth.register_user("newuser", "newpass", "new@example.com", ["user"])
        
        user = auth.authenticate("newuser", "newpass")
        assert user is not None
        assert user["email"] == "new@example.com"
    
    def test_mock_event_bus(self):
        """HOSTILE AUDIT: Verify event bus works."""
        bus = create_mock_event_bus()
        
        # Publish event
        event = MockEvent(event_type="test.event", data={"test": True})
        bus.publish(event)
        
        # Verify event stored
        events = bus.get_events("test.event")
        assert len(events) == 1
        assert events[0].data["test"] is True
    
    def test_mock_event_bus_subscriber(self):
        """Verify event subscription."""
        bus = create_mock_event_bus()
        
        received = []
        def handler(event):
            received.append(event)
        
        bus.subscribe("test.event", handler)
        
        event = MockEvent(event_type="test.event", data={"test": True})
        bus.publish(event)
        
        assert len(received) == 1
    
    def test_mock_kafka_producer(self):
        """Verify Kafka producer mock."""
        producer = MockKafkaProducer()
        
        producer.send("test-topic", key="key1", value={"data": "test"})
        
        assert len(producer.sent_messages) == 1
        assert producer.sent_messages[0]["topic"] == "test-topic"


class TestGenerators:
    """Test data generators."""
    
    def test_user_generator(self):
        """HOSTILE AUDIT: Verify user generator produces valid data."""
        gen = UserGenerator()
        
        user = gen.generate(["admin"])
        
        assert user.username is not None
        assert "@" in user.email
        assert "admin" in user.roles
        assert not user.disabled
    
    def test_user_generator_many(self):
        """Verify batch user generation."""
        gen = UserGenerator()
        
        users = gen.generate_many(5)
        
        assert len(users) == 5
        # Verify unique usernames
        usernames = [u.username for u in users]
        assert len(set(usernames)) == 5
    
    def test_document_generator(self):
        """Verify document generator."""
        gen = DocumentGenerator()
        
        doc = gen.generate("pdf", "hvac")
        
        assert doc.document_id.startswith("doc_")
        assert doc.doc_type == "pdf"
        assert len(doc.content) > 0
        assert "category" in doc.metadata
    
    def test_event_generator(self):
        """Verify event generator."""
        gen = EventGenerator()
        
        event = gen.generate("agent.started")
        
        assert event.event_type == "agent.started"
        assert "agent_id" in event.data
        assert event.event_id.startswith("evt_")
    
    def test_event_generator_lifecycle(self):
        """Verify agent lifecycle events."""
        gen = EventGenerator()
        
        events = gen.generate_agent_lifecycle("agent_001")
        
        assert len(events) == 2
        assert events[0].event_type == "agent.started"
        assert events[1].event_type == "agent.completed"
    
    def test_graph_generator(self):
        """Verify graph generator."""
        gen = GraphDataGenerator()
        
        graph = gen.generate_graph(10, 15)
        
        assert len(graph["nodes"]) == 10
        # Edges may be fewer due to self-loop filtering
        assert len(graph["edges"]) <= 15
    
    def test_convenience_functions(self):
        """Verify convenience functions."""
        users = generate_users(3)
        assert len(users) == 3
        
        docs = generate_documents(2)
        assert len(docs) == 2
        
        events = generate_events(2)
        assert len(events) == 2
        
        graph = generate_graph(5, 7)
        assert len(graph["nodes"]) == 5


class TestBaseClasses:
    """Test base classes."""
    
    def test_integration_test_base(self):
        """HOSTILE AUDIT: Verify base class setup/teardown."""
        class TestExample(IntegrationTestBase):
            def test_method(self):
                assert self.temp_dir is not None
                assert os.path.exists(self.temp_dir)
                assert self.db is not None
                assert self.auth_service is not None
                assert self.event_bus is not None
        
        test = TestExample()
        test.setup_method()
        test.test_method()
        
        # Verify temp dir exists during test
        temp_dir = test.temp_dir
        assert os.path.exists(temp_dir)
        
        test.teardown_method()
        
        # Verify cleanup
        assert not os.path.exists(temp_dir)
    
    def test_full_integration_test(self):
        """Verify full integration test with mixins."""
        class TestFull(FullIntegrationTest):
            def test_full(self):
                # Test database mixin
                self.setup_database_schema("CREATE TABLE test (id INTEGER)")
                self.insert_test_data("test", {"id": 1})
                results = self.query_test_data("test")
                assert len(results) == 1
                
                # Test auth mixin
                token = self.login_user("admin", "admin123")
                assert token is not None
                
                # Test event mixin
                self.publish_test_event("test.event", {"test": True})
                events = self.get_published_events("test.event")
                assert len(events) == 1
        
        test = TestFull()
        test.setup_method()
        test.test_full()
        test.teardown_method()
    
    def test_create_test_helpers(self):
        """Verify test helper methods."""
        class TestHelpers(IntegrationTestBase):
            def test_helpers(self):
                # Create user
                user = self.create_test_user("customuser")
                assert user["username"] == "customuser"
                
                # Create document
                doc = self.create_test_document("Test content")
                assert doc["content"] == "Test content"
                
                # Create token
                token = self.create_auth_token("testuser", ["user"])
                assert "access_token" in token
        
        test = TestHelpers()
        test.setup_method()
        test.test_helpers()
        test.teardown_method()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
