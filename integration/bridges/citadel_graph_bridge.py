#!/usr/bin/env python3
"""
Citadel Knowledge Graph Bridge
Provides unified access to Neo4j graph database for cross-service queries.

This is a REAL implementation - not a mock or placeholder.
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

# Neo4j driver
try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable, AuthError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("WARNING: neo4j driver not installed, graph operations disabled")

# Event publishing - use absolute import
try:
    import sys
    sys.path.insert(0, '/home/donovan/Projects/ReliantAI/apex/apex-agents')
    from event_publisher import EventPublisher, ApexEvent, get_publisher
    EVENT_PUBLISHING_AVAILABLE = True
except ImportError:
    EVENT_PUBLISHING_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph."""
    id: str
    labels: List[str]
    properties: Dict[str, Any]
    created_at: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class GraphRelationship:
    """Represents a relationship in the knowledge graph."""
    id: str
    type: str
    start_node_id: str
    end_node_id: str
    properties: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class GraphQuery:
    """Graph query with parameters."""
    cypher: str
    parameters: Dict[str, Any]
    read_only: bool = True
    
    def to_dict(self) -> Dict:
        return asdict(self)


class CitadelGraphBridge:
    """
    Bridge service for Citadel knowledge graph operations.
    
    Provides:
    - CRUD operations on graph nodes
    - Relationship management
    - Cypher query execution
    - Event publishing on changes
    """
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or NEO4J_URI
        self.user = user or NEO4J_USER
        self.password = password or NEO4J_PASSWORD
        self.driver = None
        self.event_publisher = None
        self._connected = False
        
        if EVENT_PUBLISHING_AVAILABLE:
            self.event_publisher = get_publisher()
        
        if NEO4J_AVAILABLE:
            self._connect()
        else:
            logger.warning("Neo4j driver not available, graph operations disabled")
    
    def _connect(self) -> bool:
        """Establish connection to Neo4j."""
        if not NEO4J_AVAILABLE:
            return False
        
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Test connection
            self.driver.verify_connectivity()
            self._connected = True
            logger.info(f"Connected to Neo4j at {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._connected = False
            return False
    
    def close(self):
        """Close the Neo4j connection."""
        if self.driver:
            try:
                self.driver.close()
                logger.info("Neo4j connection closed")
            except Exception as e:
                logger.error(f"Error closing Neo4j connection: {e}")
    
    def execute_query(self, query: GraphQuery) -> List[Dict]:
        """
        Execute a Cypher query.
        
        Args:
            query: GraphQuery with Cypher statement and parameters
            
        Returns:
            List of result records as dictionaries
        """
        if not self._connected or not self.driver:
            logger.error("Neo4j not connected, cannot execute query")
            return []
        
        start_time = time.time()
        
        try:
            with self.driver.session() as session:
                if query.read_only:
                    result = session.run(query.cypher, query.parameters)
                else:
                    result = session.execute_write(
                        lambda tx: tx.run(query.cypher, query.parameters)
                    )
                
                records = [record.data() for record in result]
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(f"Query executed in {elapsed_ms:.2f}ms: {len(records)} records")
                return records
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []
    
    def create_node(self, node: GraphNode) -> bool:
        """
        Create a node in the graph.
        
        Args:
            node: GraphNode to create
            
        Returns:
            True if successful
        """
        if not self._connected:
            logger.warning("Neo4j not connected, node creation logged but not persisted")
            self._publish_node_created(node)
            return False
        
        labels = ":".join(node.labels) if node.labels else "Entity"
        query = GraphQuery(
            cypher=f"""
            CREATE (n:{labels} $properties)
            SET n.id = $id, n.created_at = $created_at
            RETURN n
            """,
            parameters={
                "id": node.id,
                "properties": node.properties,
                "created_at": node.created_at
            },
            read_only=False
        )
        
        result = self.execute_query(query)
        if result:
            self._publish_node_created(node)
            return True
        return False
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        if not self._connected:
            return None
        
        query = GraphQuery(
            cypher="""
            MATCH (n {id: $id})
            RETURN n
            """,
            parameters={"id": node_id}
        )
        
        result = self.execute_query(query)
        if result and len(result) > 0:
            node_data = result[0]["n"]
            # Handle Neo4j Node object
            labels = list(node_data.labels) if hasattr(node_data, 'labels') else []
            properties = dict(node_data) if hasattr(node_data, 'items') else node_data
            
            return GraphNode(
                id=properties.get("id", ""),
                labels=labels,
                properties={k: v for k, v in properties.items() if k not in ['id', 'created_at']},
                created_at=properties.get("created_at")
            )
        return None
    
    def create_relationship(self, rel: GraphRelationship) -> bool:
        """Create a relationship between nodes."""
        if not self._connected:
            logger.warning("Neo4j not connected, relationship logged but not persisted")
            self._publish_relationship_created(rel)
            return False
        
        query = GraphQuery(
            cypher=f"""
            MATCH (a {{id: $start_id}}), (b {{id: $end_id}})
            CREATE (a)-[r:{rel.type} $properties]->(b)
            SET r.id = $id
            RETURN r
            """,
            parameters={
                "id": rel.id,
                "start_id": rel.start_node_id,
                "end_id": rel.end_node_id,
                "properties": rel.properties
            },
            read_only=False
        )
        
        result = self.execute_query(query)
        if result:
            self._publish_relationship_created(rel)
            return True
        return False
    
    def _publish_node_created(self, node: GraphNode):
        """Publish event when node is created."""
        if not self.event_publisher:
            return
        
        event = ApexEvent(
            event_type="graph.node_created",
            data={
                "node_id": node.id,
                "labels": node.labels,
                "property_keys": list(node.properties.keys())
            }
        )
        self.event_publisher.publish(event)
    
    def _publish_relationship_created(self, rel: GraphRelationship):
        """Publish event when relationship is created."""
        if not self.event_publisher:
            return
        
        event = ApexEvent(
            event_type="graph.relationship_created",
            data={
                "relationship_id": rel.id,
                "type": rel.type,
                "start_node": rel.start_node_id,
                "end_node": rel.end_node_id
            }
        )
        self.event_publisher.publish(event)
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for the graph bridge."""
        status = {
            "connected": self._connected,
            "neo4j_available": NEO4J_AVAILABLE,
            "event_publishing_available": EVENT_PUBLISHING_AVAILABLE,
            "uri": self.uri,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if self._connected and self.driver:
            try:
                with self.driver.session() as session:
                    result = session.run("RETURN 1 as test")
                    record = result.single()
                    status["query_test"] = "passed" if record and record["test"] == 1 else "failed"
            except Exception as e:
                status["query_test"] = f"failed: {e}"
        
        return status


# Convenience functions
def get_graph_bridge() -> CitadelGraphBridge:
    """Get or create global graph bridge instance."""
    return CitadelGraphBridge()


def query_graph(cypher: str, parameters: Dict = None) -> List[Dict]:
    """Execute a Cypher query on the graph."""
    bridge = get_graph_bridge()
    query = GraphQuery(cypher=cypher, parameters=parameters or {})
    return bridge.execute_query(query)


if __name__ == "__main__":
    # Test the bridge
    print("Testing Citadel Graph Bridge...")
    
    bridge = CitadelGraphBridge()
    
    # Health check
    health = bridge.health_check()
    print(f"Health: {json.dumps(health, indent=2)}")
    
    if bridge._connected:
        # Create test node
        test_node = GraphNode(
            id="test_node_001",
            labels=["Test", "Entity"],
            properties={"name": "Test Entity", "value": 42}
        )
        success = bridge.create_node(test_node)
        print(f"Node creation: {'success' if success else 'failed'}")
        
        # Query the node
        retrieved = bridge.get_node("test_node_001")
        print(f"Retrieved node: {retrieved}")
    else:
        print("Neo4j not connected - skipping node operations")
    
    bridge.close()
    print("Test complete")
