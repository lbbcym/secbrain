"""Tests for core logging module."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from secbrain.core.logging import (
    _StdlibBoundLogger,
    add_timestamp,
    log_error,
    log_event,
    log_finding,
    log_model_call,
    log_phase_transition,
    log_tool_call,
    setup_logging,
)

# ======================================================================
# _StdlibBoundLogger
# ======================================================================


class TestStdlibBoundLogger:
    """Test stdlib fallback bound logger."""

    def _make_logger(self) -> tuple[_StdlibBoundLogger, logging.Logger]:
        stdlib_logger = logging.getLogger("test_stdlib_bound")
        stdlib_logger.handlers.clear()
        stdlib_logger.setLevel(logging.DEBUG)
        return _StdlibBoundLogger(stdlib_logger), stdlib_logger

    def test_bind_creates_new_logger(self) -> None:
        """bind() returns a new logger with merged context."""
        logger, _ = self._make_logger()
        bound = logger.bind(run_id="r1", phase="recon")

        assert bound is not logger  # new instance
        assert bound._bound["run_id"] == "r1"
        assert bound._bound["phase"] == "recon"

    def test_bind_merges_context(self) -> None:
        """Successive bind() calls merge context."""
        logger, _ = self._make_logger()
        bound1 = logger.bind(run_id="r1")
        bound2 = bound1.bind(phase="exploit")

        assert "run_id" in bound2._bound
        assert "phase" in bound2._bound

    def test_info_logs_json(self, caplog: pytest.LogCaptureFixture) -> None:
        """info() logs a JSON-serialized message."""
        stdlib_logger = logging.getLogger("test_info")
        stdlib_logger.handlers.clear()
        stdlib_logger.setLevel(logging.DEBUG)
        bound = _StdlibBoundLogger(stdlib_logger, {"run_id": "r1"})

        with caplog.at_level(logging.INFO, logger="test_info"):
            bound.info("test_event", extra_key="val")

        assert len(caplog.records) == 1
        payload = json.loads(caplog.records[0].message)
        assert payload["event"] == "test_event"
        assert payload["run_id"] == "r1"
        assert payload["extra_key"] == "val"

    def test_error_logs_json(self, caplog: pytest.LogCaptureFixture) -> None:
        """error() logs at ERROR level."""
        stdlib_logger = logging.getLogger("test_error")
        stdlib_logger.handlers.clear()
        stdlib_logger.setLevel(logging.DEBUG)
        bound = _StdlibBoundLogger(stdlib_logger)

        with caplog.at_level(logging.ERROR, logger="test_error"):
            bound.error("failure", reason="timeout")

        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.ERROR


# ======================================================================
# add_timestamp
# ======================================================================


class TestAddTimestamp:
    """Test timestamp processor."""

    def test_adds_timestamp(self) -> None:
        """Adds ISO timestamp to event dict."""
        event_dict: dict[str, Any] = {"event": "test"}
        result = add_timestamp(None, "info", event_dict)

        assert "timestamp" in result
        assert "T" in result["timestamp"]  # ISO format


# ======================================================================
# setup_logging
# ======================================================================


class TestSetupLogging:
    """Test logging setup."""

    def test_requires_logs_path_or_workspace_path(self) -> None:
        """Raises ValueError when neither path is provided."""
        with pytest.raises(ValueError, match="requires"):
            setup_logging(run_id="test")

    def test_requires_run_id(self, tmp_path: Path) -> None:
        """Raises ValueError when run_id is missing."""
        with pytest.raises(ValueError, match="requires run_id"):
            setup_logging(logs_path=tmp_path)

    def test_setup_with_logs_path(self, tmp_path: Path) -> None:
        """Creates logger and log file in logs_path."""
        logger = setup_logging(logs_path=tmp_path, run_id="test-123", console_output=False)
        assert logger is not None

        # Check that a log file was created
        log_files = list(tmp_path.glob("run-*-test-123.jsonl"))
        assert len(log_files) == 1

    def test_setup_with_workspace_path(self, tmp_path: Path) -> None:
        """Derives logs_path from workspace_path."""
        logger = setup_logging(workspace_path=tmp_path, run_id="test-456", console_output=False)
        assert logger is not None

        logs_dir = tmp_path / "logs"
        assert logs_dir.exists()

    def test_logger_can_log(self, tmp_path: Path) -> None:
        """Logger successfully writes to file."""
        logger = setup_logging(logs_path=tmp_path, run_id="test-log", console_output=False)
        logger.info("test_event", key="value")

        # Verify something was written
        log_files = list(tmp_path.glob("*.jsonl"))
        assert len(log_files) == 1
        content = log_files[0].read_text()
        assert len(content) > 0


# ======================================================================
# log helper functions
# ======================================================================


class _FakeLogger:
    """Minimal logger recording calls for testing."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def info(self, event: str, **kwargs: Any) -> None:
        self.events.append((event, kwargs))

    def error(self, event: str, **kwargs: Any) -> None:
        self.events.append((event, kwargs))


class TestLogEvent:
    """Test log_event helper."""

    def test_basic_event(self) -> None:
        logger = _FakeLogger()
        log_event(logger, "test_event")

        assert len(logger.events) == 1
        assert logger.events[0][0] == "test_event"

    def test_with_context(self) -> None:
        logger = _FakeLogger()
        log_event(logger, "test_event", agent="recon", phase="recon", tool="httpx")

        _, kwargs = logger.events[0]
        assert kwargs["agent"] == "recon"
        assert kwargs["phase"] == "recon"
        assert kwargs["tool"] == "httpx"

    def test_skips_none_fields(self) -> None:
        logger = _FakeLogger()
        log_event(logger, "test_event", agent=None, phase=None)

        _, kwargs = logger.events[0]
        assert "agent" not in kwargs
        assert "phase" not in kwargs


class TestLogToolCall:
    """Test log_tool_call helper."""

    def test_success_call(self) -> None:
        logger = _FakeLogger()
        log_tool_call(logger, "httpx", "request", target="example.com", success=True)

        _, kwargs = logger.events[0]
        assert kwargs["tool"] == "httpx"
        assert kwargs["result"] == "success"

    def test_failure_call(self) -> None:
        logger = _FakeLogger()
        log_tool_call(logger, "httpx", "request", success=False)

        _, kwargs = logger.events[0]
        assert kwargs["result"] == "failure"


class TestLogModelCall:
    """Test log_model_call helper."""

    def test_with_tokens(self) -> None:
        logger = _FakeLogger()
        log_model_call(logger, "gpt-4", prompt_tokens=100, completion_tokens=50, duration_ms=200.0)

        _, kwargs = logger.events[0]
        assert kwargs["model"] == "gpt-4"
        assert kwargs["prompt_tokens"] == 100
        assert kwargs["completion_tokens"] == 50


class TestLogPhaseTransition:
    """Test log_phase_transition helper."""

    def test_phase_transition(self) -> None:
        logger = _FakeLogger()
        log_phase_transition(logger, "recon", "hypothesis")

        _, kwargs = logger.events[0]
        assert kwargs["phase"] == "hypothesis"
        assert kwargs["from_phase"] == "recon"


class TestLogFinding:
    """Test log_finding helper."""

    def test_finding(self) -> None:
        logger = _FakeLogger()
        log_finding(logger, "critical", "xss", "example.com")

        _, kwargs = logger.events[0]
        assert kwargs["result"] == "critical"
        assert kwargs["vuln_type"] == "xss"
        assert kwargs["target"] == "example.com"


class TestLogError:
    """Test log_error helper."""

    def test_error_logging(self) -> None:
        logger = _FakeLogger()
        log_error(logger, "connection_timeout", agent="recon", recoverable=True)

        _, kwargs = logger.events[0]
        assert kwargs["error"] == "connection_timeout"
        assert kwargs["agent"] == "recon"
        assert kwargs["recoverable"] is True
