"""Shared test fixtures for SecBrain test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the project root (the directory containing the `secbrain/` package) is on sys.path.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from secbrain.core.context import ProgramConfig, RunContext, ScopeConfig  # noqa: E402
from secbrain.models.base import DryRunModelClient  # noqa: E402

# ---------------------------------------------------------------------------
# Minimal RunContext helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def scope_config() -> ScopeConfig:
    """A minimal ScopeConfig for tests."""
    return ScopeConfig(
        domains=["*.example.com"],
        urls=["https://example.com"],
        foundry_root=None,
    )


@pytest.fixture
def program_config() -> ProgramConfig:
    """A minimal ProgramConfig for tests."""
    return ProgramConfig(name="test-program", platform="test")


@pytest.fixture
def run_context(
    tmp_path: Path,
    scope_config: ScopeConfig,
    program_config: ProgramConfig,
) -> RunContext:
    """A RunContext backed by a temporary workspace directory."""
    return RunContext(
        workspace_path=tmp_path,
        dry_run=True,
        scope=scope_config,
        program=program_config,
    )


@pytest.fixture
def dry_run_model() -> DryRunModelClient:
    """A DryRunModelClient instance for testing."""
    return DryRunModelClient()
