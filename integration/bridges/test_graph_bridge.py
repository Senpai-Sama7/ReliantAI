#!/usr/bin/env python3
"""
Comprehensive tests for Citadel Graph Bridge.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# Mock neo4j before import
sys.modules['neo4j'] = MagicMock()
sys.modules['neo4j.exceptions'] = MagicMock()

# Add paths for imports
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/integration/bridges')
sys.path.insert(0, '/home/donovan/Projects/ReliantAI/apex/apex-agents')

from graph_models import (
    NodeCreateRequest,
    NodeResponse,
    RelationshipCreateRequest,
    GraphQueryRequest
)
from citadel_graph_bridge import (
    GraphNode,
    GraphRelationship,
    GraphQuery,
    CitadelGraphBridge,
    get_graph_bridge,
    query_graph
)


class TestGraphNode:
    """Test GraphNode dataclass."""
    
    def test_node_creation(self):
        """Test basic node creation."""
        node = GraphNode(
            id="node_001",
            labels=["Person", "User"],
            properties={"name": "John", "age": 30}
        )
        
        assert node.id == "node_001"
        assert node.labels == ["Person", "User"]
        assert node.properties["name"] == "John"
        assert node.created_at is not None
    
    def test_node_defaults(self):
        """Test default values are auto-generated."""
        node = GraphNode(
            id="node_002",
            labels=["Test"],
            properties={}
        )
        
        assert node.created_at is not None
        assert isinstance(node.created_at, str)
    
    def test_node_to_dict(self):
        """Test node serialization."""
        node = GraphNode(
            id="node_002",
            labels=["Test"],
            properties={"key": "value"}
        )
        
        d = node.to_dict()
        assert d["id"] == "node_002"
        assert d["labels"] == ["Test"]
        assert d["properties"]["key"] == "value"


class TestGraphRelationship:
    """Test GraphRelationship dataclass."""
    
    def test_relationship_creation(self):
        """Test relationship creation."""
        rel = GraphRelationship(
            id="rel_001",
            type="KNOWS",
            start_node_id="node_001",
            end_node_id="node_002",
            properties={"since": "2024"}
        )
        
        assert rel.id == "rel_001"
        assert rel.type == "KNOWS"
        assert rel.start_node_id == "node_001"
        assert rel.end_node_id == "node_002"
    
    def test_relationship_to_dict(self):
        """Test relationship serialization."""
        rel = GraphRelationship(
            id="rel_002",
            type="WORKS_WITH",
            start_node_id="a",
            end_node_id="b",
            properties={}
        )
        
        d = rel.to_dict()
        assert d["type"] == "WORKS_WITH"


class TestGraphQuery:
    """Test GraphQuery dataclass."""
    
    def test_query_creation(self):
        """Test query creation."""
        query = GraphQuery(
            cypher="MATCH (n) RETURN n",
            parameters={"limit": 10},
            read_only=True
        )
        
        assert query.cypher == "MATCH (n) RETURN n"
        assert query.parameters["limit"] == 10
        assert query.read_only is True
    
    def test_query_defaults(self):
        """Test query defaults."""
        query = GraphQuery(
            cypher="MATCH (n) RETURN n",
            parameters={}
        )
        
        assert query.read_only is True


class TestCitadelGraphBridge:
    """Test CitadelGraphBridge class."""
    
    @patch.dict('os.environ', {
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USER': 'neo4j',
        'NEO4J_PASSWORD': 'password'
    })
    @patch('citadel_graph_bridge.GraphDatabase')
    def test_connect_success(self, mock_db_class):
        """Test successful Neo4j connection."""
        mock_driver = MagicMock()
        mock_db_class.driver.return_value = mock_driver
        
        bridge = CitadelGraphBridge()
        
        assert bridge.uri == "bolt://localhost:7687"
        mock_db_class.driver.assert_called_once()
    
    @patch.dict('os.environ', {'NEO4J_URI': 'bolt://invalid:7687'})
    @patch('citadel_graph_bridge.GraphDatabase')
    def test_connect_failure(self, mock_db_class):
        """Test connection failure handling."""
        mock_db_class.driver.side_effect = Exception("Connection refused")
        
        bridge = CitadelGraphBridge()
        
        assert bridge._connected is False
    
    @patch.dict('os.environ', {'NEO4J_URI': 'bolt://localhost:7687'})
    @patch('citadel_graph_bridge.GraphDatabase')
    def test_execute_query(self, mock_db_class):
        """Test query execution."""
        # Setup mock
        mock_record = MagicMock()
        mock_record.data.return_value = {"n": {"id": "node_001", "name": "Test"}}
        
        mock_result = MagicMock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        
        mock_session = MagicMock()
        mock_session.run.return_value = mock_result
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)
        
        mock_driver = MagicMock()
        mock_driver.session.return_value = mock_session
        mock_db_class.driver.return_value = mock_driver
        
        bridge = CitadelGraphBridge()
        bridge._connected = True
        bridge.driver = mock_driver
        
        query = GraphQuery(
            cypher="MATCH (n) RETURN n LIMIT 1",
            parameters={}
        )
        result = bridge.execute_query(query)
        
        assert len(result) == 1
        mock_session.run.assert_called_once()
    
    @patch.dict('os.environ', {'NEO4J_URI': 'bolt://localhost:7687'})
    @patch('citadel_graph_bridge.GraphDatabase')
    @patch('citadel_graph_bridge.CitadelGraphBridge._publish_node_created')
    def test_create_node(self, mock_publish, mock_db_class):
        """Test node creation."""
        mock_record = MagicMock()
        mock_record.data.return_value = {"n": {"id": "node_001"}}
        
        mock_result = MagicMock()
        mock_result.__iter__ = Mock(return_value=iter([mock_record]))
        
        mock_session = MagicMock()
        # For write operations, execute_write calls the lambda which calls tx.run
        mock_session.execute_write = Mock(return_value=mock_result)
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)
        
        mock_driver = MagicMock()
        mock_driver.session.return_value = mock_session
        mock_db_class.driver.return_value = mock_driver
        
        bridge = CitadelGraphBridge()
        bridge._connected = True
        bridge.driver = mock_driver
        
        node = GraphNode(
            id="node_001",
            labels=["Test"],
            properties={"name": "Test Node"}
        )
        
        result = bridge.create_node(node)
        assert result is True
    
    @patch('citadel_graph_bridge.NEO4J_AVAILABLE', False)
    def test_create_node_without_connection(self):
        """Test node creation when Neo4j not available."""
        bridge = CitadelGraphBridge()
        
        node = GraphNode(
            id="node_001",
            labels=["Test"],
            properties={}
        )
        
        result = bridge.create_node(node)
        assert result is False
    
    @patch.dict('os.environ', {'NEO4J_URI': 'bolt://localhost:7687'})
    @patch('citadel_graph_bridge.GraphDatabase')
    def test_health_check(self, mock_db_class):
        """Test health check endpoint."""
        mock_driver = MagicMock()
        mock_db_class.driver.return_value = mock_driver
        
        bridge = CitadelGraphBridge()
        bridge._connected = True
        bridge.driver = mock_driver
        
        health = bridge.health_check()
        
        assert health["connected"] is True
        assert health["neo4j_available"] is True
        assert "timestamp" in health
    
    @patch.dict('os.environ', {'NEO4J_URI': 'bolt://localhost:7687'})
    @patch('citadel_graph_bridge.GraphDatabase')
    def test_close(self, mock_db_class):
        """Test bridge cleanup."""
        mock_driver = MagicMock()
        mock_db_class.driver.return_value = mock_driver
        
        bridge = CitadelGraphBridge()
        bridge.close()
        
        mock_driver.close.assert_called_once()


class TestGraphModels:
    """Test Pydantic models."""
    
    def test_node_create_request(self):
        """Test NodeCreateRequest model."""
        req = NodeCreateRequest(
            id="node_001",
            labels=["Person"],
            properties={"name": "John"}
        )
        
        assert req.id == "node_001"
        assert req.labels == ["Person"]
    
    def test_node_response(self):
        """Test NodeResponse model."""
        resp = NodeResponse(
            id="node_001",
            labels=["Person"],
            properties={"name": "John"},
            created_at="2024-01-01T00:00:00"
        )
        
        assert resp.id == "node_001"
    
    def test_relationship_create_request(self):
        """Test RelationshipCreateRequest model."""
        req = RelationshipCreateRequest(
            id="rel_001",
            type="KNOWS",
            start_node_id="a",
            end_node_id="b"
        )
        
        assert req.type == "KNOWS"
    
    def test_graph_query_request(self):
        """Test GraphQueryRequest model."""
        req = GraphQueryRequest(
            cypher="MATCH (n) RETURN n",
            parameters={"limit": 10},
            read_only=True
        )
        
        assert req.cypher == "MATCH (n) RETURN n"
        assert req.parameters["limit"] == 10
        assert req.read_only is True


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @patch('citadel_graph_bridge.CitadelGraphBridge')
    def test_get_graph_bridge(self, mock_bridge_class):
        """Test get_graph_bridge creates new instance."""
        mock_instance = MagicMock()
        mock_bridge_class.return_value = mock_instance
        
        bridge = get_graph_bridge()
        
        assert bridge is mock_instance
        mock_bridge_class.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
