from __future__ import annotations

import json
import logging
from pathlib import Path

import orchestrator


def _read_last_log_line(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    assert text
    return text.splitlines()[-1]


def _flush_root_handlers() -> None:
    for handler in logging.getLogger().handlers:
        handler.flush()


def test_json_logging_emits_valid_json_with_run_id(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "orchestrator-json.log"
    monkeypatch.setenv("CITADEL_LOG_FORMAT", "json")
    orchestrator.setup_logging(str(log_path))

    logger = logging.getLogger("citadel.orchestrator")
    logger.info('message with "quotes" and newline\\nline2', extra={"run_id": "run-123"})
    _flush_root_handlers()

    record = json.loads(_read_last_log_line(log_path))
    assert record["message"] == 'message with "quotes" and newline\\nline2'
    assert record["run_id"] == "run-123"
    assert record["level"] == "INFO"
    assert record["logger"] == "citadel.orchestrator"
    assert "timestamp" in record


def test_json_logging_always_includes_run_id_key(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "orchestrator-json-default.log"
    monkeypatch.setenv("CITADEL_LOG_FORMAT", "json")
    orchestrator.setup_logging(str(log_path))

    logging.getLogger("citadel.orchestrator").info("no explicit run id")
    _flush_root_handlers()

    record = json.loads(_read_last_log_line(log_path))
    assert "run_id" in record
    assert record["run_id"] is None
