import asyncio
from pathlib import Path

import pytest_asyncio

from secbrain.core.context import ProgramConfig, RunContext, ScopeConfig


@pytest_asyncio.fixture
async def run_context(tmp_path_factory):
    """Provide a dry-run RunContext for example smoke tests."""
    workspace: Path = tmp_path_factory.mktemp("workspace")
    scope = ScopeConfig(
        domains=["*.example.com", "example.com"],
        urls=["https://example.com"],
        excluded_paths=["/admin/*"],
        allowed_methods=["GET", "POST"],
    )
    program = ProgramConfig(
        name="Smoke Test",
        platform="test",
        focus_areas=[],
        rules=[],
        rewards={},
    )
    ctx = RunContext(
        scope=scope,
        program=program,
        workspace_path=workspace,
        dry_run=True,
    )
    # Ensure event loop exists for consumers that rely on it
    if not asyncio.get_event_loop().is_running():
        asyncio.get_event_loop()
    return ctx
