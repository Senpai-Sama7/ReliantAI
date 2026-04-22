#!/usr/bin/env python3
"""
Unit tests for Apex Event Publisher.

Run with: python -m pytest test_event_publisher.py -v
"""

import pytest
import json
import sys
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

# Mock kafka module before importing event_publisher
sys.modules['kafka'] = MagicMock()
sys.modules['kafka.errors'] = MagicMock()

from event_publisher import (
    ApexEvent,
    EventPublisher,
    publish_agent_started,
    publish_agent_completed,
    publish_agent_failed,
    publish_workflow_started,
    publish_workflow_completed,
    publish_hitl_required,
    get_publisher,
    KAFKA_AVAILABLE
)


class TestApexEvent:
    """Test suite for ApexEvent dataclass."""
    
    def test_event_creation(self):
        """Test basic event creation."""
        event = ApexEvent(
            event_type="test.event",
            data={"key": "value"},
            source="test-service"
        )
        
        assert event.event_type == "test.event"
        assert event.data == {"key": "value"}
        assert event.source == "test-service"
        assert event.event_id is not None
        assert event.timestamp is not None
    
    def test_event_defaults(self):
        """Test default values are auto-generated."""
        event = ApexEvent(
            event_type="test.event",
            data={}
        )
        
        assert event.event_id is not None
        assert event.timestamp is not None
        assert event.source == "apex-agents"
        assert isinstance(event.timestamp, str)
    
    def test_event_to_dict(self):
        """Test conversion to dictionary."""
        event = ApexEvent(
            event_type="test.event",
            data={"key": "value"},
            trace_id="trace-123",
            user_id="user-456"
        )
        
        d = event.to_dict()
        assert d["event_type"] == "test.event"
        assert d["data"] == {"key": "value"}
        assert d["trace_id"] == "trace-123"
        assert d["user_id"] == "user-456"
        assert "event_id" in d
        assert "timestamp" in d
    
    def test_event_to_json(self):
        """Test conversion to JSON string."""
        event = ApexEvent(
            event_type="test.event",
            data={"key": "value"}
        )
        
        json_str = event.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["event_type"] == "test.event"
        assert parsed["data"] == {"key": "value"}


class TestEventPublisher:
    """Test suite for EventPublisher."""
    
    @patch.dict('os.environ', {'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092'})
    def test_connect_success(self):
        """Test successful Kafka connection."""
        with patch('event_publisher.KafkaProducer') as mock_producer_class:
            mock_producer = MagicMock()
            mock_producer_class.return_value = mock_producer
            
            publisher = EventPublisher(bootstrap_servers="localhost:9092")
            
            assert publisher._connected is True
            mock_producer_class.assert_called_once()
    
    @patch.dict('os.environ', {'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092'})
    def test_connect_failure(self):
        """Test Kafka connection failure handling."""
        with patch('event_publisher.KafkaProducer') as mock_producer_class:
            mock_producer_class.side_effect = Exception("Connection refused")
            
            publisher = EventPublisher(bootstrap_servers="invalid:9092")
            
            assert publisher._connected is False
    
    def test_publish_without_kafka(self):
        """Test publishing when Kafka is unavailable."""
        with patch('event_publisher.KAFKA_AVAILABLE', False):
            publisher = EventPublisher()
            event = ApexEvent(event_type="test.event", data={"key": "value"})
            
            result = publisher.publish(event)
            
            # Should return False when Kafka unavailable
            assert result is False
    
    @patch.dict('os.environ', {'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092'})
    def test_publish_success(self):
        """Test successful event publishing."""
        with patch('event_publisher.KafkaProducer') as mock_producer_class:
            mock_future = MagicMock()
            mock_metadata = MagicMock()
            mock_metadata.partition = 0
            mock_metadata.offset = 42
            mock_future.get.return_value = mock_metadata
            
            mock_producer = MagicMock()
            mock_producer.send.return_value = mock_future
            mock_producer_class.return_value = mock_producer
            
            publisher = EventPublisher(bootstrap_servers="localhost:9092")
            event = ApexEvent(event_type="test.event", data={"key": "value"})
            
            result = publisher.publish(event)
            
            assert result is True
            mock_producer.send.assert_called_once()
            call_args = mock_producer.send.call_args
            assert call_args[0][0] == "events.test.event"  # Topic
            assert call_args[1]["key"] == event.event_id
    
    @patch.dict('os.environ', {'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092'})
    def test_publish_to_custom_topic(self):
        """Test publishing to custom topic."""
        with patch('event_publisher.KafkaProducer') as mock_producer_class:
            mock_future = MagicMock()
            mock_metadata = MagicMock()
            mock_metadata.partition = 0
            mock_metadata.offset = 1
            mock_future.get.return_value = mock_metadata
            
            mock_producer = MagicMock()
            mock_producer.send.return_value = mock_future
            mock_producer_class.return_value = mock_producer
            
            publisher = EventPublisher()
            event = ApexEvent(event_type="test.event", data={})
            
            result = publisher.publish(event, topic="custom.topic")
            
            assert result is True
            mock_producer.send.assert_called_once()
            call_args = mock_producer.send.call_args
            assert call_args[0][0] == "custom.topic"
    
    @patch.dict('os.environ', {'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092'})
    def test_publish_failure(self):
        """Test handling of publish failures."""
        with patch('event_publisher.KafkaProducer') as mock_producer_class:
            mock_producer = MagicMock()
            mock_future = MagicMock()
            mock_future.get.side_effect = Exception("KafkaError: Broker not available")
            mock_producer.send.return_value = mock_future
            mock_producer_class.return_value = mock_producer
            
            publisher = EventPublisher()
            event = ApexEvent(event_type="test.event", data={})
            
            result = publisher.publish(event)
            
            assert result is False
    
    @patch.dict('os.environ', {'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092'})
    def test_close(self):
        """Test publisher cleanup."""
        with patch('event_publisher.KafkaProducer') as mock_producer_class:
            mock_producer = MagicMock()
            mock_producer_class.return_value = mock_producer
            
            publisher = EventPublisher()
            publisher.close()
            
            mock_producer.close.assert_called_once()


class TestConvenienceFunctions:
    """Test suite for convenience publishing functions."""
    
    @patch('event_publisher.EventPublisher')
    def test_publish_agent_started(self, mock_publisher_class):
        """Test publish_agent_started function."""
        mock_publisher = MagicMock()
        mock_publisher.publish.return_value = True
        mock_publisher_class.return_value = mock_publisher
        
        # Reset global state
        import event_publisher
        event_publisher._publisher = None
        
        result = publish_agent_started(
            agent_id="agent-123",
            agent_type="task_agent",
            trace_id="trace-456",
            user_id="user-789"
        )
        
        assert result is True
        mock_publisher.publish.assert_called_once()
        call_args = mock_publisher.publish.call_args
        event = call_args[0][0]
        assert event.event_type == "agent.started"
        assert event.data["agent_id"] == "agent-123"
        assert event.data["agent_type"] == "task_agent"
        assert event.trace_id == "trace-456"
        assert event.user_id == "user-789"
    
    @patch('event_publisher.EventPublisher')
    def test_publish_agent_completed(self, mock_publisher_class):
        """Test publish_agent_completed function."""
        mock_publisher = MagicMock()
        mock_publisher.publish.return_value = True
        mock_publisher_class.return_value = mock_publisher
        
        # Reset global state
        import event_publisher
        event_publisher._publisher = None
        
        result = publish_agent_completed(
            agent_id="agent-123",
            result={"status": "success", "output": "done"}
        )
        
        assert result is True
        mock_publisher.publish.assert_called_once()
        call_args = mock_publisher.publish.call_args
        event = call_args[0][0]
        assert event.event_type == "agent.completed"
        assert event.data["agent_id"] == "agent-123"
        assert event.data["result"]["status"] == "success"
    
    @patch('event_publisher.EventPublisher')
    def test_publish_agent_failed(self, mock_publisher_class):
        """Test publish_agent_failed function."""
        mock_publisher = MagicMock()
        mock_publisher.publish.return_value = True
        mock_publisher_class.return_value = mock_publisher
        
        # Reset global state
        import event_publisher
        event_publisher._publisher = None
        
        result = publish_agent_failed(
            agent_id="agent-123",
            error="Connection timeout"
        )
        
        assert result is True
        call_args = mock_publisher.publish.call_args
        event = call_args[0][0]
        assert event.event_type == "agent.failed"
        assert event.data["error"] == "Connection timeout"
    
    @patch('event_publisher.EventPublisher')
    def test_publish_workflow_started(self, mock_publisher_class):
        """Test publish_workflow_started function."""
        mock_publisher = MagicMock()
        mock_publisher.publish.return_value = True
        mock_publisher_class.return_value = mock_publisher
        
        # Reset global state
        import event_publisher
        event_publisher._publisher = None
        
        result = publish_workflow_started(
            workflow_id="wf-123",
            task="Process customer request"
        )
        
        assert result is True
        call_args = mock_publisher.publish.call_args
        event = call_args[0][0]
        assert event.event_type == "workflow.started"
        assert event.data["workflow_id"] == "wf-123"
    
    @patch('event_publisher.EventPublisher')
    def test_publish_workflow_completed(self, mock_publisher_class):
        """Test publish_workflow_completed function."""
        mock_publisher = MagicMock()
        mock_publisher.publish.return_value = True
        mock_publisher_class.return_value = mock_publisher
        
        # Reset global state
        import event_publisher
        event_publisher._publisher = None
        
        result = publish_workflow_completed(
            workflow_id="wf-123",
            output={"result": "success"}
        )
        
        assert result is True
        call_args = mock_publisher.publish.call_args
        event = call_args[0][0]
        assert event.event_type == "workflow.completed"
    
    @patch('event_publisher.EventPublisher')
    def test_publish_hitl_required(self, mock_publisher_class):
        """Test publish_hitl_required function."""
        mock_publisher = MagicMock()
        mock_publisher.publish.return_value = True
        mock_publisher_class.return_value = mock_publisher
        
        # Reset global state
        import event_publisher
        event_publisher._publisher = None
        
        result = publish_hitl_required(
            decision_id="dec-123",
            task_summary="Approve $10,000 transaction"
        )
        
        assert result is True
        call_args = mock_publisher.publish.call_args
        event = call_args[0][0]
        assert event.event_type == "hitl.required"
        assert event.data["decision_id"] == "dec-123"
        assert event.data["task_summary"] == "Approve $10,000 transaction"


class TestGlobalPublisher:
    """Test suite for global publisher singleton."""
    
    @patch('event_publisher.EventPublisher')
    def test_get_publisher_singleton(self, mock_publisher_class):
        """Test that get_publisher returns singleton instance."""
        mock_publisher = MagicMock()
        mock_publisher_class.return_value = mock_publisher
        
        # Reset global state
        import event_publisher
        event_publisher._publisher = None
        
        publisher1 = get_publisher()
        publisher2 = get_publisher()
        
        assert publisher1 is publisher2
        mock_publisher_class.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
