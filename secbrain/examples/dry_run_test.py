#!/usr/bin/env python3
"""
Dry-run test for SecBrain.

This script tests the SecBrain system in dry-run mode to verify:
1. Configuration loading works
2. All agents can be instantiated
3. The workflow orchestration runs without errors
4. Logging is functional

Usage:
    python examples/dry_run_test.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


async def main() -> int:
    """Run the dry-run test."""
    from secbrain.core.context import ProgramConfig, RunContext, ScopeConfig
    from secbrain.core.logging import log_event, setup_logging
    from secbrain.workflows.bug_bounty_run import BugBountyWorkflow

    print("=" * 60)
    print("SecBrain Dry-Run Test")
    print("=" * 60)

    # Create test workspace
    workspace = Path(__file__).parent / "test_workspace"
    workspace.mkdir(exist_ok=True)

    # Create scope config
    scope = ScopeConfig(
        domains=["*.example.com", "api.example.com"],
        urls=["https://example.com", "https://api.example.com"],
        excluded_paths=["/admin/*", "/internal/*"],
        allowed_methods=["GET", "POST"],
    )

    # Create program config
    program = ProgramConfig(
        name="Test Program",
        platform="test",
        focus_areas=["API Security", "Authentication"],
        rules=["No automated scanning", "Report within 24h"],
        rewards={"critical": "$10000", "high": "$5000"},
    )

    # Create run context in dry-run mode
    run_context = RunContext(
        scope=scope,
        program=program,
        workspace_path=workspace,
        dry_run=True,
        phases=["ingest", "plan"],  # Only run first two phases for test
    )

    print(f"\nRun ID: {run_context.run_id}")
    print(f"Workspace: {workspace}")
    print(f"Dry Run: {run_context.dry_run}")
    print(f"Phases: {run_context.requested_phases}")

    # Set up logging
    logger = setup_logging(
        workspace_path=workspace,
        run_id=run_context.run_id,
    )

    log_event(logger, "test_started", message="Dry-run test initiated")

    # Create and run workflow
    print("\nStarting workflow...")
    workflow = BugBountyWorkflow(run_context, logger=logger)

    result = await workflow.run(phases=["ingest", "plan"])

    # Print results
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Success: {result.success}")
    print(f"Phases Completed: {[p.value for p in result.phases_completed]}")
    print(f"Phases Failed: {[p.value for p in result.phases_failed]}")
    print(f"Duration: {result.total_duration_seconds:.2f}s")

    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")

    # Check phase results
    print("\nPhase Details:")
    for phase_name, phase_result in result.phase_results.items():
        status = "✓" if phase_result.success else "✗"
        print(f"  [{status}] {phase_name}: {phase_result.duration_seconds:.2f}s")

    log_event(logger, "test_completed", success=result.success)

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

    return 0 if result.success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
