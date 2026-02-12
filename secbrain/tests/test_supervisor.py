"""Tests for SupervisorAgent."""

from __future__ import annotations

import pytest

from secbrain.agents.base import AgentResult
from secbrain.agents.supervisor import SupervisorAgent
from secbrain.core.context import RunContext
from secbrain.models.base import DryRunModelClient


class TestSupervisorAgent:
    """Test SupervisorAgent orchestration logic."""

    def _make_agent(self, run_context: RunContext) -> SupervisorAgent:
        return SupervisorAgent(
            run_context=run_context,
            worker_model=DryRunModelClient(),
        )

    # ------------------------------------------------------------------
    # Status check
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_status_check_operational(self, run_context: RunContext) -> None:
        """Status check returns success when system is operational."""
        agent = self._make_agent(run_context)
        result = await agent.run(action="check")

        assert result.success is True
        assert "operational" in result.message.lower()
        assert result.data["run_id"] == run_context.run_id
        assert result.data["dry_run"] is True

    @pytest.mark.asyncio
    async def test_status_check_killed(self, run_context: RunContext) -> None:
        """Status check fails when kill-switch is activated."""
        run_context.kill()
        agent = self._make_agent(run_context)
        result = await agent.run(action="check")

        assert result.success is False
        assert "kill" in result.message.lower()

    # ------------------------------------------------------------------
    # Pre-phase check
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_pre_phase_check_passes(self, run_context: RunContext) -> None:
        """Pre-phase check passes for an allowed phase."""
        agent = self._make_agent(run_context)
        result = await agent.run(action="pre_phase", phase_name="recon")

        assert result.success is True
        assert "recon" in result.message.lower()
        assert run_context.session.current_phase == "recon"

    @pytest.mark.asyncio
    async def test_pre_phase_check_killed(self, run_context: RunContext) -> None:
        """Pre-phase check fails when kill-switch is activated."""
        run_context.kill()
        agent = self._make_agent(run_context)
        result = await agent.run(action="pre_phase", phase_name="recon")

        assert result.success is False
        assert "kill" in result.message.lower()

    @pytest.mark.asyncio
    async def test_pre_phase_check_not_in_phases(self, run_context: RunContext) -> None:
        """Pre-phase check fails when phase not in requested phases."""
        run_context.phases = ["recon", "exploit"]
        agent = self._make_agent(run_context)
        result = await agent.run(action="pre_phase", phase_name="triage")

        assert result.success is False
        assert "triage" in result.message.lower()

    # ------------------------------------------------------------------
    # Post-phase check
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_post_phase_check_success(self, run_context: RunContext) -> None:
        """Post-phase check succeeds after a successful phase."""
        agent = self._make_agent(run_context)
        phase_result = AgentResult(agent="test", phase="recon", success=True, message="ok")
        result = await agent.run(action="post_phase", phase_name="recon", result=phase_result)

        assert result.success is True
        assert result.data["phase"] == "recon"
        assert result.data["phase_success"] is True

    @pytest.mark.asyncio
    async def test_post_phase_check_with_failure(self, run_context: RunContext) -> None:
        """Post-phase check records failure but still succeeds."""
        agent = self._make_agent(run_context)
        phase_result = AgentResult(
            agent="test", phase="recon", success=False, message="error", errors=["boom"]
        )
        result = await agent.run(action="post_phase", phase_name="recon", result=phase_result)

        assert result.success is True
        assert result.data["phase_success"] is False

    @pytest.mark.asyncio
    async def test_post_phase_check_killed(self, run_context: RunContext) -> None:
        """Post-phase check fails when kill-switch is activated."""
        run_context.kill()
        agent = self._make_agent(run_context)
        result = await agent.run(action="post_phase", phase_name="recon", result=None)

        assert result.success is False

    # ------------------------------------------------------------------
    # Approval handling
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_approval_auto_approve_dry_run(self, run_context: RunContext) -> None:
        """Approval auto-approves in dry-run mode."""
        agent = self._make_agent(run_context)
        result = await agent.run(
            action="approval",
            request={"action": "run_exploit", "reason": "test", "risk_level": "low"},
        )

        assert result.success is True
        assert "auto-approved" in result.message.lower() or "dry-run" in result.message.lower()
        assert result.data["approved"] is True

    @pytest.mark.asyncio
    async def test_approval_no_request(self, run_context: RunContext) -> None:
        """Approval fails when no request is provided."""
        agent = self._make_agent(run_context)
        result = await agent.run(action="approval", request=None)

        assert result.success is False

    @pytest.mark.asyncio
    async def test_approval_requires_approval_non_dry_run(
        self, tmp_path, scope_config, program_config
    ) -> None:
        """Approval requires human approval in non-dry-run mode."""
        ctx = RunContext(
            workspace_path=tmp_path,
            dry_run=False,
            scope=scope_config,
            program=program_config,
        )
        agent = SupervisorAgent(run_context=ctx, worker_model=DryRunModelClient())
        result = await agent.run(
            action="approval",
            request={"action": "run_exploit", "reason": "testing", "risk_level": "high"},
        )

        assert result.requires_approval is True

    # ------------------------------------------------------------------
    # Next-phase logic
    # ------------------------------------------------------------------

    def test_get_next_phase_normal(self, run_context: RunContext) -> None:
        """Next phase returns the correct successor."""
        agent = self._make_agent(run_context)
        assert agent._get_next_phase("recon") == "hypothesis"
        assert agent._get_next_phase("hypothesis") == "exploit"
        assert agent._get_next_phase("exploit") == "static"

    def test_get_next_phase_last(self, run_context: RunContext) -> None:
        """No next phase after the last phase."""
        agent = self._make_agent(run_context)
        assert agent._get_next_phase("report") is None

    def test_get_next_phase_unknown(self, run_context: RunContext) -> None:
        """Unknown phase returns None."""
        agent = self._make_agent(run_context)
        assert agent._get_next_phase("nonexistent") is None

    def test_get_next_phase_skips_disabled(self, run_context: RunContext) -> None:
        """Skips phases not in the requested set."""
        run_context.phases = ["recon", "exploit"]
        agent = self._make_agent(run_context)
        # hypothesis is between recon and exploit but not in phases
        assert agent._get_next_phase("recon") == "exploit"

    # ------------------------------------------------------------------
    # Scope and ACL helpers
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_enforce_scope_in_scope(self, run_context: RunContext) -> None:
        """Returns True for in-scope targets."""
        agent = self._make_agent(run_context)
        assert await agent.enforce_scope("https://sub.example.com/api") is True

    @pytest.mark.asyncio
    async def test_enforce_scope_out_of_scope(self, run_context: RunContext) -> None:
        """Returns False for out-of-scope targets."""
        agent = self._make_agent(run_context)
        assert await agent.enforce_scope("https://evil.com/hack") is False

    @pytest.mark.asyncio
    async def test_check_tool_allowed(self, run_context: RunContext) -> None:
        """ACL allows http_client in any phase (allowed_phases=[])."""
        agent = self._make_agent(run_context)
        assert await agent.check_tool_allowed("http_client") is True

    @pytest.mark.asyncio
    async def test_request_approval_helper(self, run_context: RunContext) -> None:
        """request_approval() delegates to _handle_approval."""
        agent = self._make_agent(run_context)
        result = await agent.request_approval("exploit", "testing", "low")

        assert result.success is True
        assert result.data["approved"] is True

    # ------------------------------------------------------------------
    # Agent metadata
    # ------------------------------------------------------------------

    def test_agent_name_and_phase(self, run_context: RunContext) -> None:
        """Agent has correct name and phase."""
        agent = self._make_agent(run_context)
        assert agent.name == "supervisor"
        assert agent.phase == "orchestration"
