"""
Enhanced State Machine + Event Sourcing for HVAC Dispatch
Based on Citadel's proven pipeline patterns.

Provides:
- Strict state transitions (no skipping allowed)
- Immutable event log (complete audit trail)
- Transition validation
- Pipeline analytics
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Iterator, Set
from pathlib import Path

from config import setup_logging
from database import get_database_path, open_sqlite_connection

logger = setup_logging("state_machine")


class DispatchState(str, Enum):
    """Valid states in the HVAC dispatch pipeline"""
    RECEIVED = "received"           # Initial contact
    TRIAGED = "triaged"             # Urgency assessed
    QUALIFIED = "qualified"         # Address/service confirmed
    SCHEDULED = "scheduled"         # Time slot proposed
    CONFIRMED = "confirmed"         # Customer confirmed
    DISPATCHED = "dispatched"       # Tech assigned & en route
    ARRIVED = "arrived"             # Tech on-site
    IN_PROGRESS = "in_progress"     # Work being done
    COMPLETED = "completed"         # Job finished
    FOLLOWED_UP = "followed_up"     # Post-service check
    CANCELLED = "cancelled"         # Terminal: cancelled
    ESCALATED = "escalated"         # Terminal: safety issue


# Valid state transitions (current -> allowed next states)
VALID_TRANSITIONS: Dict[DispatchState, Set[DispatchState]] = {
    DispatchState.RECEIVED:     {DispatchState.TRIAGED, DispatchState.CANCELLED, DispatchState.ESCALATED},
    DispatchState.TRIAGED:      {DispatchState.QUALIFIED, DispatchState.CANCELLED, DispatchState.ESCALATED},
    DispatchState.QUALIFIED:    {DispatchState.SCHEDULED, DispatchState.CANCELLED, DispatchState.ESCALATED},
    DispatchState.SCHEDULED:    {DispatchState.CONFIRMED, DispatchState.CANCELLED},
    DispatchState.CONFIRMED:    {DispatchState.DISPATCHED, DispatchState.CANCELLED},
    DispatchState.DISPATCHED:   {DispatchState.ARRIVED, DispatchState.CANCELLED, DispatchState.ESCALATED},
    DispatchState.ARRIVED:      {DispatchState.IN_PROGRESS, DispatchState.ESCALATED},
    DispatchState.IN_PROGRESS:  {DispatchState.COMPLETED, DispatchState.ESCALATED},
    DispatchState.COMPLETED:    {DispatchState.FOLLOWED_UP},
    DispatchState.FOLLOWED_UP:  set(),  # Terminal
    DispatchState.CANCELLED:    set(),  # Terminal
    DispatchState.ESCALATED:    set(),  # Terminal
}


@dataclass
class DispatchEvent:
    """Immutable event record for state changes"""
    event_id: Optional[int]
    dispatch_id: str
    event_type: str                # 'state_transition', 'tech_assigned', 'customer_notified', etc.
    from_state: Optional[str]
    to_state: Optional[str]
    actor: str                     # 'system', 'customer', tech_name, 'dispatch_ai'
    run_id: Optional[str]          # For linking to CrewAI runs
    payload_json: str              # Additional event data
    created_at: str
    
    @classmethod
    def new(
        cls,
        dispatch_id: str,
        event_type: str,
        actor: str,
        from_state: Optional[str] = None,
        to_state: Optional[str] = None,
        run_id: Optional[str] = None,
        payload: Optional[Dict] = None
    ) -> DispatchEvent:
        """Create a new event with current timestamp"""
        return cls(
            event_id=None,
            dispatch_id=dispatch_id,
            event_type=event_type,
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            run_id=run_id,
            payload_json=json.dumps(payload or {}),
            created_at=datetime.now().isoformat()
        )


class DispatchStateMachine:
    """
    Manages dispatch state transitions with event sourcing.
    
    Usage:
        sm = DispatchStateMachine()
        sm.init_db()  # Create tables
        
        # Transition with validation
        sm.transition(dispatch_id, DispatchState.TRIAGED, actor='system')
        
        # Get event timeline
        events = sm.get_timeline(dispatch_id)
        
        # Get funnel counts
        counts = sm.funnel_counts()
    """
    
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or get_database_path()
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        """Transaction context with WAL mode and proper pragmas"""
        conn = open_sqlite_connection(self.db_path, check_same_thread=False)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_db(self) -> None:
        """Initialize database schema with events table"""
        with self.tx() as conn:
            conn.executescript(
                """
                -- Dispatch events (event sourcing)
                CREATE TABLE IF NOT EXISTS dispatch_events (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    dispatch_id     TEXT    NOT NULL,
                    event_type      TEXT    NOT NULL,
                    from_state      TEXT,
                    to_state        TEXT,
                    actor           TEXT    NOT NULL,
                    run_id          TEXT,
                    payload_json    TEXT    NOT NULL DEFAULT '{}',
                    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_events_dispatch 
                    ON dispatch_events(dispatch_id);
                CREATE INDEX IF NOT EXISTS idx_events_created 
                    ON dispatch_events(created_at);
                
                -- Current state cache (can be rebuilt from events)
                CREATE TABLE IF NOT EXISTS dispatch_current_state (
                    dispatch_id     TEXT    PRIMARY KEY,
                    current_state   TEXT    NOT NULL,
                    last_event_id   INTEGER,
                    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                
                -- DB version for migrations
                CREATE TABLE IF NOT EXISTS db_version (
                    version INTEGER PRIMARY KEY
                );
                INSERT OR IGNORE INTO db_version (version) VALUES (1);
                """
            )
        logger.info("State machine database initialized")
    
    def can_transition(self, from_state: str, to_state: str) -> bool:
        """Check if a state transition is valid"""
        try:
            current = DispatchState(from_state)
            next_state = DispatchState(to_state)
            return next_state in VALID_TRANSITIONS.get(current, set())
        except ValueError:
            return False
    
    def transition(
        self,
        dispatch_id: str,
        to_state: DispatchState,
        actor: str,
        run_id: Optional[str] = None,
        payload: Optional[Dict] = None
    ) -> DispatchEvent:
        """
        Perform a state transition with validation.
        
        Raises:
            ValueError: If transition is invalid
        """
        with self.tx() as conn:
            # Get current state
            row = conn.execute(
                "SELECT current_state FROM dispatch_current_state WHERE dispatch_id = ?",
                (dispatch_id,)
            ).fetchone()
            
            from_state = row["current_state"] if row else None
            
            # Validate transition
            if from_state:
                if not self.can_transition(from_state, to_state.value):
                    raise ValueError(
                        f"Invalid transition: {from_state} -> {to_state.value}"
                    )
            
            # Create event
            event = DispatchEvent.new(
                dispatch_id=dispatch_id,
                event_type="state_transition",
                actor=actor,
                from_state=from_state,
                to_state=to_state.value,
                run_id=run_id,
                payload=payload
            )
            
            # Insert event
            cursor = conn.execute(
                """
                INSERT INTO dispatch_events 
                (dispatch_id, event_type, from_state, to_state, actor, run_id, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event.dispatch_id, event.event_type, event.from_state, event.to_state,
                 event.actor, event.run_id, event.payload_json, event.created_at)
            )
            
            # Update current state cache
            conn.execute(
                """
                INSERT INTO dispatch_current_state (dispatch_id, current_state, last_event_id, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(dispatch_id) DO UPDATE SET
                    current_state = excluded.current_state,
                    last_event_id = excluded.last_event_id,
                    updated_at = excluded.updated_at
                """,
                (dispatch_id, to_state.value, cursor.lastrowid, datetime.now().isoformat())
            )
            
            logger.info(
                f"Dispatch {dispatch_id}: {from_state} -> {to_state.value} by {actor}"
            )
            return event
    
    def record_event(
        self,
        dispatch_id: str,
        event_type: str,
        actor: str,
        payload: Optional[Dict] = None,
        run_id: Optional[str] = None
    ) -> DispatchEvent:
        """
        Record a non-state-transition event (e.g., tech notified, SMS sent).
        """
        event = DispatchEvent.new(
            dispatch_id=dispatch_id,
            event_type=event_type,
            actor=actor,
            run_id=run_id,
            payload=payload
        )
        
        with self.tx() as conn:
            conn.execute(
                """
                INSERT INTO dispatch_events 
                (dispatch_id, event_type, actor, run_id, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event.dispatch_id, event.event_type, event.actor,
                 event.run_id, event.payload_json, event.created_at)
            )
        
        logger.info(f"Event recorded for {dispatch_id}: {event_type} by {actor}")
        return event
    
    def get_current_state(self, dispatch_id: str) -> Optional[str]:
        """Get current state of a dispatch"""
        with self.tx() as conn:
            row = conn.execute(
                "SELECT current_state FROM dispatch_current_state WHERE dispatch_id = ?",
                (dispatch_id,)
            ).fetchone()
            return row["current_state"] if row else None
    
    def get_timeline(self, dispatch_id: str) -> List[Dict]:
        """Get full event timeline for a dispatch"""
        with self.tx() as conn:
            rows = conn.execute(
                """
                SELECT * FROM dispatch_events 
                WHERE dispatch_id = ? 
                ORDER BY created_at ASC, id ASC
                """,
                (dispatch_id,)
            ).fetchall()
            
            return [dict(row) for row in rows]
    
    def funnel_counts(self) -> Dict[str, int]:
        """Get count of dispatches in each state"""
        with self.tx() as conn:
            # Current states
            rows = conn.execute(
                """
                SELECT current_state, COUNT(*) as count 
                FROM dispatch_current_state 
                GROUP BY current_state
                """
            ).fetchall()
            
            counts = {row["current_state"]: row["count"] for row in rows}
            
            # Include zero counts for all valid states
            for state in DispatchState:
                if state.value not in counts:
                    counts[state.value] = 0
            
            return counts
    
    def get_time_in_state(self, dispatch_id: str) -> Optional[int]:
        """Get seconds since last state change"""
        timeline = self.get_timeline(dispatch_id)
        if not timeline:
            return None
        
        last_transition = None
        for event in reversed(timeline):
            if event["event_type"] == "state_transition":
                last_transition = event["created_at"]
                break
        
        if not last_transition:
            return None
        
        last_time = datetime.fromisoformat(last_transition)
        return int((datetime.now() - last_time).total_seconds())
    
    def rebuild_state_cache(self) -> None:
        """Rebuild current_state cache from events (recovery)"""
        with self.tx() as conn:
            # Clear cache
            conn.execute("DELETE FROM dispatch_current_state")
            
            # Get latest state for each dispatch
            rows = conn.execute(
                """
                SELECT 
                    dispatch_id,
                    to_state,
                    MAX(id) as last_event_id
                FROM dispatch_events
                WHERE event_type = 'state_transition'
                GROUP BY dispatch_id
                """
            ).fetchall()
            
            for row in rows:
                conn.execute(
                    """
                    INSERT INTO dispatch_current_state 
                    (dispatch_id, current_state, last_event_id, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (row["dispatch_id"], row["to_state"], row["last_event_id"], datetime.now().isoformat())
                )
        
        logger.info("State cache rebuilt from events")


# Convenience functions
def get_state_machine(db_path: str | None = None) -> DispatchStateMachine:
    """Get initialized state machine"""
    sm = DispatchStateMachine(db_path)
    sm.init_db()
    return sm
