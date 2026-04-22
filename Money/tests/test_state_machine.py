"""State-machine tests covering transitions, recovery, and analytics."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

import pytest

from state_machine import DispatchState, DispatchStateMachine, get_state_machine


def test_init_db_creates_tables(tmp_path) -> None:
    db_path = tmp_path / "state.db"
    sm = DispatchStateMachine(str(db_path))
    sm.init_db()

    conn = sqlite3.connect(db_path)
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    version = conn.execute("SELECT version FROM db_version").fetchone()[0]
    conn.close()

    assert "dispatch_events" in tables
    assert "dispatch_current_state" in tables
    assert version == 1


def test_can_transition_handles_valid_invalid_and_unknown_states(tmp_path) -> None:
    sm = DispatchStateMachine(str(tmp_path / "state.db"))

    assert sm.can_transition("received", "triaged") is True
    assert sm.can_transition("triaged", "dispatched") is False
    assert sm.can_transition("not-a-state", "triaged") is False


def test_transition_persists_timeline_and_rejects_invalid_skip(tmp_path) -> None:
    sm = DispatchStateMachine(str(tmp_path / "state.db"))
    sm.init_db()

    first = sm.transition("dispatch-1", DispatchState.RECEIVED, actor="system")
    second = sm.transition("dispatch-1", DispatchState.TRIAGED, actor="dispatcher", payload={"priority": "high"})

    assert first.to_state == "received"
    assert second.from_state == "received"
    assert sm.get_current_state("dispatch-1") == "triaged"
    assert len(sm.get_timeline("dispatch-1")) == 2

    with pytest.raises(ValueError, match="Invalid transition"):
        sm.transition("dispatch-1", DispatchState.DISPATCHED, actor="dispatcher")


def test_record_event_and_funnel_counts_include_zero_states(tmp_path) -> None:
    sm = DispatchStateMachine(str(tmp_path / "state.db"))
    sm.init_db()

    sm.transition("dispatch-1", DispatchState.RECEIVED, actor="system")
    sm.transition("dispatch-1", DispatchState.TRIAGED, actor="system")
    sm.transition("dispatch-2", DispatchState.RECEIVED, actor="system")
    sm.transition("dispatch-2", DispatchState.CANCELLED, actor="system")
    event = sm.record_event("dispatch-1", "customer_notified", actor="system", payload={"channel": "sms"})

    timeline = sm.get_timeline("dispatch-1")
    counts = sm.funnel_counts()

    assert event.event_type == "customer_notified"
    assert any(row["event_type"] == "customer_notified" for row in timeline)
    assert counts["triaged"] == 1
    assert counts["cancelled"] == 1
    assert counts["completed"] == 0
    assert counts["followed_up"] == 0


def test_get_time_in_state_returns_none_without_transitions(tmp_path) -> None:
    sm = DispatchStateMachine(str(tmp_path / "state.db"))
    sm.init_db()
    sm.record_event("dispatch-1", "customer_notified", actor="system")

    assert sm.get_time_in_state("dispatch-1") is None


def test_get_time_in_state_uses_latest_transition_timestamp(tmp_path) -> None:
    db_path = tmp_path / "state.db"
    sm = DispatchStateMachine(str(db_path))
    sm.init_db()
    sm.transition("dispatch-1", DispatchState.RECEIVED, actor="system")
    sm.transition("dispatch-1", DispatchState.TRIAGED, actor="system")

    received_time = (datetime.now() - timedelta(seconds=120)).isoformat()
    triaged_time = (datetime.now() - timedelta(seconds=90)).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            UPDATE dispatch_events
            SET created_at = ?
            WHERE dispatch_id = ? AND to_state = ?
            """,
            (received_time, "dispatch-1", "received"),
        )
        conn.execute(
            """
            UPDATE dispatch_events
            SET created_at = ?
            WHERE dispatch_id = ? AND to_state = ?
            """,
            (triaged_time, "dispatch-1", "triaged"),
        )
        conn.commit()

    assert sm.get_time_in_state("dispatch-1") >= 89


def test_rebuild_state_cache_restores_latest_state(tmp_path) -> None:
    db_path = tmp_path / "state.db"
    sm = DispatchStateMachine(str(db_path))
    sm.init_db()
    sm.transition("dispatch-1", DispatchState.RECEIVED, actor="system")
    sm.transition("dispatch-1", DispatchState.TRIAGED, actor="system")
    sm.transition("dispatch-1", DispatchState.QUALIFIED, actor="system")

    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM dispatch_current_state")
        conn.commit()

    assert sm.get_current_state("dispatch-1") is None

    sm.rebuild_state_cache()

    assert sm.get_current_state("dispatch-1") == "qualified"


def test_tx_rolls_back_on_exception(tmp_path) -> None:
    sm = DispatchStateMachine(str(tmp_path / "state.db"))
    sm.init_db()

    with pytest.raises(RuntimeError, match="rollback me"):
        with sm.tx() as conn:
            conn.execute(
                """
                INSERT INTO dispatch_events
                (dispatch_id, event_type, actor, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("dispatch-1", "manual", "system", "{}", datetime.now().isoformat()),
            )
            raise RuntimeError("rollback me")

    assert sm.get_timeline("dispatch-1") == []


def test_get_state_machine_initializes_and_uses_requested_path(tmp_path) -> None:
    db_path = tmp_path / "state.db"
    sm = get_state_machine(str(db_path))

    sm.transition("dispatch-1", DispatchState.RECEIVED, actor="system")

    assert db_path.exists()
    assert sm.get_current_state("dispatch-1") == "received"
