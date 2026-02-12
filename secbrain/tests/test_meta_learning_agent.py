"""Tests for MetaLearningAgent."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from secbrain.agents.meta_learning_agent import MetaLearningAgent
from secbrain.core.context import RunContext
from secbrain.models.base import DryRunModelClient


class TestMetaLearningAgent:
    """Test MetaLearningAgent performance tracking and recommendations."""

    def _make_agent(self, run_context: RunContext) -> MetaLearningAgent:
        return MetaLearningAgent(
            run_context=run_context,
            worker_model=DryRunModelClient(),
        )

    @pytest.mark.asyncio
    async def test_run_basic(self, run_context: RunContext) -> None:
        """Runs meta-learning and returns learnings."""
        agent = self._make_agent(run_context)
        result = await agent.run(
            ingest_data={"program_name": "test-program"},
            recon_data={"assets": [{"id": "a1"}], "live_hosts_count": 1},
            hypothesis_data={"hypotheses": []},
            exploit_data={"tested_count": 0, "confirmed_count": 0},
            triage_data={"findings": []},
        )

        assert result.success is True
        assert "metrics" in result.data
        assert "recommendations" in result.data
        assert result.data["program"] == "test-program"

    @pytest.mark.asyncio
    async def test_run_kill_switch(self, run_context: RunContext) -> None:
        """Returns failure when kill-switch is active."""
        run_context.kill()
        agent = self._make_agent(run_context)
        result = await agent.run()

        assert result.success is False
        assert "kill" in result.message.lower()

    @pytest.mark.asyncio
    async def test_run_stores_learnings_to_file(
        self, run_context: RunContext, tmp_path: Path
    ) -> None:
        """Writes learnings JSON to workspace."""
        agent = self._make_agent(run_context)
        await agent.run(
            ingest_data={"program_name": "test"},
            recon_data={},
            hypothesis_data={"hypotheses": []},
            exploit_data={},
            triage_data={"findings": []},
        )

        learnings_dir = tmp_path / "learnings"
        assert learnings_dir.exists()
        files = list(learnings_dir.glob("*.json"))
        assert len(files) == 1

        data = json.loads(files[0].read_text())
        assert "metrics" in data
        assert "recommendations" in data

    def test_calculate_metrics_empty(self, run_context: RunContext) -> None:
        """Metrics with empty data return zero values."""
        agent = self._make_agent(run_context)
        metrics = agent._calculate_metrics({}, {}, {}, {})

        assert metrics["recon"]["assets_discovered"] == 0
        assert metrics["hypotheses"]["total_generated"] == 0
        assert metrics["exploitation"]["tested"] == 0
        assert metrics["exploitation"]["confirmation_rate"] == 0
        assert metrics["findings"]["total"] == 0

    def test_calculate_metrics_with_data(self, run_context: RunContext) -> None:
        """Metrics are computed from phase data."""
        agent = self._make_agent(run_context)
        metrics = agent._calculate_metrics(
            recon_data={"assets": [1, 2, 3], "live_hosts_count": 2},
            hypothesis_data={"hypotheses": [{"id": 1}], "by_vuln_type": {"xss": 1}},
            exploit_data={"tested_count": 10, "confirmed_count": 3},
            triage_data={"findings": [{"id": "f1"}], "by_severity": {"high": 1}},
        )

        assert metrics["recon"]["assets_discovered"] == 3
        assert metrics["recon"]["live_hosts"] == 2
        assert metrics["hypotheses"]["total_generated"] == 1
        assert metrics["exploitation"]["tested"] == 10
        assert metrics["exploitation"]["confirmed"] == 3
        assert metrics["exploitation"]["confirmation_rate"] == 0.3
        assert metrics["findings"]["total"] == 1

    @pytest.mark.asyncio
    async def test_analyze_effectiveness_empty(self, run_context: RunContext) -> None:
        """Empty data returns empty effectiveness."""
        agent = self._make_agent(run_context)
        analysis = await agent._analyze_effectiveness({}, {}, {})

        assert analysis["effective_types"] == {}
        assert analysis["ineffective_types"] == {}
        assert analysis["success_rates"] == {}

    @pytest.mark.asyncio
    async def test_analyze_effectiveness_with_matches(self, run_context: RunContext) -> None:
        """Tracks which hypothesis types led to findings."""
        agent = self._make_agent(run_context)
        analysis = await agent._analyze_effectiveness(
            hypothesis_data={
                "hypotheses": [
                    {"id": "h1", "vuln_type": "xss"},
                    {"id": "h2", "vuln_type": "xss"},
                    {"id": "h3", "vuln_type": "sqli"},
                ]
            },
            exploit_data={},
            triage_data={
                "findings": [
                    {"hypothesis_id": "h1"},
                ]
            },
        )

        assert analysis["effective_types"]["xss"] == 1
        assert analysis["ineffective_types"]["xss"] == 1
        assert analysis["ineffective_types"]["sqli"] == 1
        assert analysis["success_rates"]["xss"] == 0.5
        assert analysis["success_rates"]["sqli"] == 0.0

    def test_hypothesis_effectiveness_empty(self, run_context: RunContext) -> None:
        """Empty inputs return empty results."""
        agent = self._make_agent(run_context)
        result = agent._calculate_hypothesis_effectiveness([], [])
        assert result == {}

    def test_hypothesis_effectiveness_with_data(self, run_context: RunContext) -> None:
        """Tracks per-type generation and confirmation rates."""
        agent = self._make_agent(run_context)
        hypotheses = [
            {"id": "h1", "vuln_type": "xss", "confidence": 0.8},
            {"id": "h2", "vuln_type": "xss", "confidence": 0.6},
            {"id": "h3", "vuln_type": "sqli", "confidence": 0.9},
        ]
        findings = [
            {"hypothesis_id": "h1", "id": "f1"},
        ]
        result = agent._calculate_hypothesis_effectiveness(hypotheses, findings)

        assert result["xss"]["generated"] == 2
        assert result["xss"]["confirmed"] == 1
        assert result["xss"]["success_rate"] == 0.5
        assert result["xss"]["avg_confidence"] == 0.7
        assert result["sqli"]["generated"] == 1
        assert result["sqli"]["confirmed"] == 0
        assert result["sqli"]["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_recommendations_low_confirmation(self, run_context: RunContext) -> None:
        """Recommends improving quality when confirmation rate is low."""
        agent = self._make_agent(run_context)
        recs = await agent._generate_recommendations(
            {"exploitation": {"confirmation_rate": 0.05}, "findings": {"total": 1}},
            {"top_performing": [("xss", 0.5)]},
        )

        assert any("low confirmation" in r.lower() for r in recs)

    @pytest.mark.asyncio
    async def test_recommendations_no_findings(self, run_context: RunContext) -> None:
        """Recommends expanding scope when no findings."""
        agent = self._make_agent(run_context)
        recs = await agent._generate_recommendations(
            {"exploitation": {"confirmation_rate": 0.0}, "findings": {"total": 0}},
            {"top_performing": []},
        )

        assert any("no findings" in r.lower() for r in recs)

    @pytest.mark.asyncio
    async def test_recommendations_high_confirmation(self, run_context: RunContext) -> None:
        """Recommends expanding scope when confirmation rate is high."""
        agent = self._make_agent(run_context)
        recs = await agent._generate_recommendations(
            {"exploitation": {"confirmation_rate": 0.5}, "findings": {"total": 5}},
            {"top_performing": [("reentrancy", 0.8)]},
        )

        assert any("high confirmation" in r.lower() or "effective" in r.lower() for r in recs)

    def test_agent_metadata(self, run_context: RunContext) -> None:
        """Agent has correct name and phase."""
        agent = self._make_agent(run_context)
        assert agent.name == "meta_learning"
        assert agent.phase == "meta"
