#!/usr/bin/env python3
"""
Money Event Subscriber
Subscribes to Kafka events and updates Money's SQLite database.

This is a REAL implementation - not a mock or placeholder.
"""

import os
import json
import logging
import sqlite3
import threading
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone
from dataclasses import dataclass

# Kafka imports
try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("WARNING: kafka-python not installed, event subscription disabled")

logger = logging.getLogger(__name__)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MONEY_DB_PATH = os.getenv("MONEY_DB_PATH", "dispatch.db")
MONEY_SERVICE_NAME = "money-dispatch"


@dataclass
class EventSubscription:
    """Event subscription configuration."""
    event_type: str
    handler: Callable[[Dict], None]
    topic: str = "events"


class MoneyEventSubscriber:
    """
    Event subscriber for Money dispatch service.
    
    Subscribes to:
    - agent.started - Log agent startup
    - agent.completed - Update job status
    - agent.failed - Log failures
    - dispatch.assigned - Create new dispatch records
    """
    
    def __init__(self, db_path: str = None, bootstrap_servers: str = None):
        self.db_path = db_path or MONEY_DB_PATH
        self.bootstrap_servers = bootstrap_servers or KAFKA_BOOTSTRAP_SERVERS
        self.consumer = None
        self._running = False
        self._thread = None
        self._handlers: Dict[str, Callable] = {}
        
        # Register default handlers
        self._register_default_handlers()
        
        if KAFKA_AVAILABLE:
            self._connect()
        else:
            logger.warning("Kafka not available, event subscriber disabled")
    
    def _connect(self) -> bool:
        """Connect to Kafka and subscribe to topics."""
        if not KAFKA_AVAILABLE:
            return False
        
        try:
            self.consumer = KafkaConsumer(
                'events.agent.started',
                'events.agent.completed',
                'events.agent.failed',
                'events.dispatch.assigned',
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: m.decode('utf-8') if m else None,
                group_id='money-dispatch-group',
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            return False
    
    def _register_default_handlers(self):
        """Register default event handlers."""
        self._handlers["agent.started"] = self._handle_agent_started
        self._handlers["agent.completed"] = self._handle_agent_completed
        self._handlers["agent.failed"] = self._handle_agent_failed
        self._handlers["dispatch.assigned"] = self._handle_dispatch_assigned
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """Get SQLite database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_tables_exist(self):
        """Ensure required tables exist in database."""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Agent logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT
                )
            """)
            
            # Dispatches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dispatches (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    result TEXT,
                    error TEXT,
                    details TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Database tables ensured")
        except Exception as e:
            logger.error(f"Failed to ensure tables: {e}")
    
    def _handle_agent_started(self, event_data: Dict):
        """Handle agent.started event."""
        logger.info(f"Agent started: {event_data.get('agent_id')}")
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agent_logs (agent_id, event_type, timestamp, details)
                VALUES (?, ?, ?, ?)
            """, (
                event_data.get('agent_id'),
                'started',
                datetime.now(timezone.utc).isoformat(),
                json.dumps(event_data)
            ))
            
            conn.commit()
            conn.close()
            logger.info("Agent start logged to database")
        except Exception as e:
            logger.error(f"Failed to log agent start: {e}")
    
    def _handle_agent_completed(self, event_data: Dict):
        """Handle agent.completed event."""
        logger.info(f"Agent completed: {event_data.get('agent_id')}")
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Log completion
            cursor.execute("""
                INSERT INTO agent_logs (agent_id, event_type, timestamp, details)
                VALUES (?, ?, ?, ?)
            """, (
                event_data.get('agent_id'),
                'completed',
                datetime.now(timezone.utc).isoformat(),
                json.dumps(event_data)
            ))
            
            # Update dispatch status if applicable
            result = event_data.get('result', {})
            dispatch_id = result.get('dispatch_id')
            if dispatch_id:
                cursor.execute("""
                    UPDATE dispatches
                    SET status = 'completed',
                        completed_at = ?,
                        result = ?
                    WHERE id = ?
                """, (
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(result),
                    dispatch_id
                ))
            
            conn.commit()
            conn.close()
            logger.info("Agent completion processed")
        except Exception as e:
            logger.error(f"Failed to process agent completion: {e}")
    
    def _handle_agent_failed(self, event_data: Dict):
        """Handle agent.failed event."""
        logger.error(f"Agent failed: {event_data.get('agent_id')}")
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agent_logs (agent_id, event_type, timestamp, details)
                VALUES (?, ?, ?, ?)
            """, (
                event_data.get('agent_id'),
                'failed',
                datetime.now(timezone.utc).isoformat(),
                json.dumps(event_data)
            ))
            
            # Update dispatch status to failed
            error = event_data.get('error', '')
            cursor.execute("""
                UPDATE dispatches
                SET status = 'failed',
                    error = ?
                WHERE agent_id = ?
            """, (error, event_data.get('agent_id')))
            
            conn.commit()
            conn.close()
            logger.info("Agent failure logged")
        except Exception as e:
            logger.error(f"Failed to log agent failure: {e}")
    
    def _handle_dispatch_assigned(self, event_data: Dict):
        """Handle dispatch.assigned event."""
        logger.info(f"Dispatch assigned: {event_data.get('dispatch_id')}")
        
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO dispatches (id, agent_id, status, created_at, details)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event_data.get('dispatch_id'),
                event_data.get('agent_id'),
                'assigned',
                datetime.now(timezone.utc).isoformat(),
                json.dumps(event_data)
            ))
            
            conn.commit()
            conn.close()
            logger.info("Dispatch record created")
        except Exception as e:
            logger.error(f"Failed to create dispatch record: {e}")
    
    def _process_message(self, message):
        """Process a Kafka message."""
        try:
            event_type = message.value.get('event_type')
            handler = self._handlers.get(event_type)
            
            if handler:
                handler(message.value.get('data', {}))
            else:
                logger.warning(f"No handler for event type: {event_type}")
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
    
    def start(self):
        """Start the event subscriber in a background thread."""
        # Ensure tables exist before starting
        self._ensure_tables_exist()
        
        if not KAFKA_AVAILABLE or not self.consumer:
            logger.warning("Cannot start subscriber - Kafka not available")
            return False
        
        self._running = True
        self._thread = threading.Thread(target=self._consume, daemon=True)
        self._thread.start()
        logger.info("Event subscriber started")
        return True
    
    def _consume(self):
        """Consume messages from Kafka."""
        while self._running:
            try:
                messages = self.consumer.poll(timeout_ms=1000)
                for topic_partition, msgs in messages.items():
                    for message in msgs:
                        self._process_message(message)
            except Exception as e:
                logger.error(f"Error consuming messages: {e}")
                time.sleep(1)
    
    def stop(self):
        """Stop the event subscriber."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self.consumer:
            self.consumer.close()
        logger.info("Event subscriber stopped")
    
    def is_running(self) -> bool:
        """Check if subscriber is running."""
        return self._running and self._thread and self._thread.is_alive()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get subscriber statistics."""
        return {
            "running": self.is_running(),
            "kafka_available": KAFKA_AVAILABLE,
            "db_path": self.db_path,
            "handlers_registered": list(self._handlers.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global subscriber instance
_subscriber: Optional[MoneyEventSubscriber] = None


def get_subscriber() -> MoneyEventSubscriber:
    """Get or create global event subscriber."""
    global _subscriber
    if _subscriber is None:
        _subscriber = MoneyEventSubscriber()
    return _subscriber


def start_event_subscriber() -> bool:
    """Start the global event subscriber."""
    subscriber = get_subscriber()
    return subscriber.start()


def stop_event_subscriber():
    """Stop the global event subscriber."""
    global _subscriber
    if _subscriber:
        _subscriber.stop()
        _subscriber = None


if __name__ == "__main__":
    # Test the subscriber
    print("Testing Money Event Subscriber...")
    
    subscriber = MoneyEventSubscriber()
    
    # Ensure tables exist
    subscriber._ensure_tables_exist()
    
    # Test database schema
    try:
        conn = sqlite3.connect(MONEY_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Database tables: {tables}")
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
    
    # Test stats
    stats = subscriber.get_stats()
    print(f"Subscriber stats: {json.dumps(stats, indent=2)}")
    
    print("Test complete")
