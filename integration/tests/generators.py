#!/usr/bin/env python3
"""
Test Data Generators

Provides generators for creating test data.

This is a REAL implementation - not a mock or placeholder.
"""

import uuid
import random
import string
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass


@dataclass
class UserData:
    """User data structure."""
    username: str
    email: str
    full_name: str
    roles: List[str]
    disabled: bool = False


@dataclass
class DocumentData:
    """Document data structure."""
    document_id: str
    content: str
    doc_type: str
    metadata: Dict[str, Any]
    source: Optional[str] = None


@dataclass
class EventData:
    """Event data structure."""
    event_type: str
    data: Dict[str, Any]
    event_id: str
    timestamp: str
    source: str


class DataGenerator:
    """Base class for data generators."""
    
    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
    
    def _random_string(self, length: int = 10) -> str:
        """Generate random string."""
        return ''.join(random.choices(string.ascii_lowercase, k=length))
    
    def _random_email(self) -> str:
        """Generate random email."""
        domains = ["example.com", "test.com", "reliantai.local"]
        return f"{self._random_string(8)}@{random.choice(domains)}"


class UserGenerator(DataGenerator):
    """Generator for user data."""
    
    def generate(self, roles: List[str] = None) -> UserData:
        """Generate a single user."""
        username = self._random_string(8)
        return UserData(
            username=username,
            email=self._random_email(),
            full_name=f"User {username.capitalize()}",
            roles=roles or ["user"],
            disabled=False
        )
    
    def generate_many(self, count: int, roles: List[str] = None) -> List[UserData]:
        """Generate multiple users."""
        return [self.generate(roles) for _ in range(count)]
    
    def generate_admin(self) -> UserData:
        """Generate admin user."""
        return UserData(
            username="admin",
            email="admin@reliantai.local",
            full_name="Administrator",
            roles=["admin", "user"],
            disabled=False
        )


class DocumentGenerator(DataGenerator):
    """Generator for document data."""
    
    DOC_TEMPLATES = {
        "hvac": [
            "HVAC systems require regular maintenance every 6 months.",
            "Filter replacement is essential for optimal performance.",
            "Thermostat calibration ensures accurate temperature control.",
            "Duct cleaning improves air quality and system efficiency."
        ],
        "general": [
            "This is a sample document for testing purposes.",
            "Document content varies based on the use case.",
            "Metadata helps categorize and search documents.",
            "Testing with realistic content is important."
        ]
    }
    
    def generate(self, doc_type: str = "txt", category: str = "general") -> DocumentData:
        """Generate a single document."""
        templates = self.DOC_TEMPLATES.get(category, self.DOC_TEMPLATES["general"])
        content = random.choice(templates)
        
        # Add some randomness to content
        content += f" Additional details: {self._random_string(20)}."
        
        return DocumentData(
            document_id=f"doc_{uuid.uuid4().hex[:8]}",
            content=content,
            doc_type=doc_type,
            metadata={
                "category": category,
                "created_by": self._random_string(6),
                "priority": random.choice(["low", "medium", "high"])
            },
            source=f"/test/documents/{self._random_string(10)}.{doc_type}"
        )
    
    def generate_many(self, count: int, doc_type: str = "txt") -> List[DocumentData]:
        """Generate multiple documents."""
        return [self.generate(doc_type) for _ in range(count)]
    
    def generate_chunked(self, chunks: int = 5) -> DocumentData:
        """Generate document with chunk markers."""
        content = " ".join([f"Chunk {i}: {self._random_string(50)}" for i in range(chunks)])
        
        return DocumentData(
            document_id=f"doc_{uuid.uuid4().hex[:8]}",
            content=content,
            doc_type="txt",
            metadata={"chunked": True, "chunk_count": chunks},
            source=None
        )


class EventGenerator(DataGenerator):
    """Generator for event data."""
    
    EVENT_TYPES = [
        "agent.started",
        "agent.completed",
        "agent.failed",
        "document.ingested",
        "user.login",
        "user.logout",
        "dispatch.assigned",
        "dispatch.completed"
    ]
    
    def generate(self, event_type: str = None) -> EventData:
        """Generate a single event."""
        event_type = event_type or random.choice(self.EVENT_TYPES)
        
        # Generate appropriate data based on event type
        if "agent" in event_type:
            data = {
                "agent_id": f"agent_{self._random_string(6)}",
                "agent_type": random.choice(["scheduler", "dispatcher", "analyzer"])
            }
        elif "document" in event_type:
            data = {
                "document_id": f"doc_{uuid.uuid4().hex[:8]}",
                "doc_type": random.choice(["pdf", "txt", "md"])
            }
        elif "user" in event_type:
            data = {
                "username": self._random_string(8),
                "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
            }
        else:
            data = {"test": True, "value": random.randint(1, 100)}
        
        return EventData(
            event_type=event_type,
            data=data,
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            source="test_generator"
        )
    
    def generate_many(self, count: int, event_type: str = None) -> List[EventData]:
        """Generate multiple events."""
        return [self.generate(event_type) for _ in range(count)]
    
    def generate_agent_lifecycle(self, agent_id: str = None) -> List[EventData]:
        """Generate complete agent lifecycle events."""
        agent_id = agent_id or f"agent_{self._random_string(6)}"
        
        return [
            EventData(
                event_type="agent.started",
                data={"agent_id": agent_id, "timestamp": datetime.now(timezone.utc).isoformat()},
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                source="test"
            ),
            EventData(
                event_type="agent.completed",
                data={
                    "agent_id": agent_id,
                    "result": {"status": "success", "output": "Task completed"}
                },
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                timestamp=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
                source="test"
            )
        ]


class GraphDataGenerator(DataGenerator):
    """Generator for graph database data."""
    
    NODE_LABELS = ["Person", "Document", "Entity", "Organization", "Product"]
    RELATIONSHIP_TYPES = ["KNOWS", "WORKS_WITH", "CREATED", "CONTAINS", "REFERENCES"]
    
    def generate_node(self, labels: List[str] = None) -> Dict[str, Any]:
        """Generate graph node."""
        return {
            "id": f"node_{uuid.uuid4().hex[:8]}",
            "labels": labels or [random.choice(self.NODE_LABELS)],
            "properties": {
                "name": self._random_string(10).capitalize(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    def generate_relationship(self, start_id: str = None, end_id: str = None) -> Dict[str, Any]:
        """Generate graph relationship."""
        return {
            "id": f"rel_{uuid.uuid4().hex[:8]}",
            "type": random.choice(self.RELATIONSHIP_TYPES),
            "start_node_id": start_id or f"node_{uuid.uuid4().hex[:8]}",
            "end_node_id": end_id or f"node_{uuid.uuid4().hex[:8]}",
            "properties": {
                "weight": random.uniform(0.1, 1.0),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    def generate_graph(self, node_count: int = 10, edge_count: int = 15) -> Dict[str, List]:
        """Generate complete graph structure."""
        nodes = [self.generate_node() for _ in range(node_count)]
        edges = []
        
        for _ in range(edge_count):
            start = random.choice(nodes)
            end = random.choice(nodes)
            if start["id"] != end["id"]:
                edges.append(self.generate_relationship(start["id"], end["id"]))
        
        return {"nodes": nodes, "edges": edges}


# Convenience functions
def generate_users(count: int = 1, roles: List[str] = None) -> List[UserData]:
    """Generate test users."""
    gen = UserGenerator()
    return gen.generate_many(count, roles)


def generate_documents(count: int = 1, doc_type: str = "txt") -> List[DocumentData]:
    """Generate test documents."""
    gen = DocumentGenerator()
    return gen.generate_many(count, doc_type)


def generate_events(count: int = 1, event_type: str = None) -> List[EventData]:
    """Generate test events."""
    gen = EventGenerator()
    return gen.generate_many(count, event_type)


def generate_graph(node_count: int = 10, edge_count: int = 15) -> Dict[str, List]:
    """Generate test graph."""
    gen = GraphDataGenerator()
    return gen.generate_graph(node_count, edge_count)


if __name__ == "__main__":
    # Test generators
    print("Testing data generators...")
    
    # Users
    users = generate_users(3, ["user"])
    print(f"Generated {len(users)} users")
    
    # Documents
    docs = generate_documents(2, "txt")
    print(f"Generated {len(docs)} documents")
    
    # Events
    events = generate_events(3)
    print(f"Generated {len(events)} events")
    
    # Graph
    graph = generate_graph(5, 8)
    print(f"Generated graph with {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    
    print("Generator tests complete")
