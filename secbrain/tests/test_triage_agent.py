"""Tests for TriageAgent and EconomicAnalyzer."""

from __future__ import annotations

import pytest

from secbrain.agents.triage_agent import EconomicAnalyzer, TriageAgent
from secbrain.core.context import RunContext
from secbrain.models.base import DryRunModelClient

# ======================================================================
# EconomicAnalyzer
# ======================================================================


class TestEconomicAnalyzer:
    """Test EconomicAnalyzer profitability analysis."""

    def test_empty_attempts(self) -> None:
        """Returns SKIP with zeroes for empty input."""
        analyzer = EconomicAnalyzer()
        result = analyzer.analyze_attempts([])

        assert result["decision"] == "SKIP"
        assert result["reason"] == "no_attempts"
        assert result["max_profit_eth"] == 0.0
        assert result["max_profit_usd"] == 0.0

    def test_single_profitable_attempt(self) -> None:
        """Detects a profitable attempt above threshold."""
        analyzer = EconomicAnalyzer(min_profit_usd=100.0)
        attempts = [
            {
                "profit_eth": 1.0,
                "profit_usd_estimate": 3000.0,
                "gas_used": 100_000,
                "gas_price_wei": 50e9,
            }
        ]
        result = analyzer.analyze_attempts(attempts)

        assert result["decision"] == "PURSUE"
        assert result["max_profit_usd"] == 3000.0
        assert result["max_profit_eth"] == 1.0
        assert result["gas_cost_usd_est"] > 0

    def test_zero_profit_attempt(self) -> None:
        """Returns SKIP for zero-profit attempts."""
        analyzer = EconomicAnalyzer()
        result = analyzer.analyze_attempts([{"profit_eth": 0, "profit_usd_estimate": 0}])

        assert result["decision"] == "SKIP"
        assert "no profit" in result["reason"].lower() or result["reason"] == "no_attempts"

    def test_marginal_profit(self) -> None:
        """Returns CONSIDER for profit below threshold but positive."""
        analyzer = EconomicAnalyzer(min_profit_usd=500.0)
        result = analyzer.analyze_attempts([
            {"profit_eth": 0.05, "profit_usd_estimate": 150.0}
        ])

        assert result["decision"] == "CONSIDER"
        assert result["max_profit_usd"] == 150.0

    def test_high_gas_ratio_skip(self) -> None:
        """Returns SKIP when gas cost is too high relative to profit."""
        analyzer = EconomicAnalyzer(min_profit_usd=100.0, gas_ratio_threshold=0.1)
        result = analyzer.analyze_attempts([
            {
                "profit_eth": 0.01,
                "profit_usd_estimate": 30.0,
                "gas_used": 5_000_000,
                "gas_price_wei": 200e9,
            }
        ])

        assert result["decision"] == "SKIP"
        assert "gas" in result["reason"].lower()

    def test_multiple_attempts_picks_best(self) -> None:
        """Picks the best profit across multiple attempts."""
        analyzer = EconomicAnalyzer(min_profit_usd=100.0)
        result = analyzer.analyze_attempts([
            {"profit_eth": 0.1, "profit_usd_estimate": 300.0},
            {"profit_eth": 2.0, "profit_usd_estimate": 6000.0},
            {"profit_eth": 0.5, "profit_usd_estimate": 1500.0},
        ])

        assert result["max_profit_eth"] == 2.0
        assert result["max_profit_usd"] == 6000.0
        assert result["decision"] == "PURSUE"

    def test_extracts_profit_from_breakdown(self) -> None:
        """Uses profit_breakdown when present and larger."""
        analyzer = EconomicAnalyzer(min_profit_usd=100.0)
        result = analyzer.analyze_attempts([
            {
                "profit_eth": 0.01,
                "profit_usd_estimate": 30.0,
                "profit_breakdown": {"token_a": 500.0, "token_b": 200.0},
            }
        ])

        assert result["max_profit_usd"] == 700.0

    def test_custom_eth_price(self) -> None:
        """Uses attempt-provided eth_price_usd."""
        analyzer = EconomicAnalyzer(min_profit_usd=100.0, default_eth_price=3000.0)
        result = analyzer.analyze_attempts([
            {"profit_eth": 0.1, "eth_price_usd": 4000}
        ])

        # profit_usd should be computed from eth price
        assert result["max_profit_usd"] > 0

    def test_invalid_profit_values(self) -> None:
        """Handles non-numeric profit values gracefully."""
        analyzer = EconomicAnalyzer()
        result = analyzer.analyze_attempts([
            {"profit_eth": "invalid", "profit_usd_estimate": None}
        ])

        assert result["decision"] == "SKIP"

    def test_gas_info_extraction(self) -> None:
        """Extracts and computes gas cost correctly."""
        analyzer = EconomicAnalyzer()
        gas_info = analyzer._extract_gas_info({
            "gas_used": 200_000,
            "gas_price_wei": 100e9,
        })

        assert gas_info is not None
        assert gas_info["gas_used"] == 200_000
        assert gas_info["gas_price_gwei"] == 100.0

    def test_gas_info_missing(self) -> None:
        """Returns None when gas_used is absent."""
        analyzer = EconomicAnalyzer()
        assert analyzer._extract_gas_info({}) is None

    def test_estimate_gas_cost_no_info(self) -> None:
        """Returns 0 when no gas info is available."""
        analyzer = EconomicAnalyzer()
        assert analyzer._estimate_gas_cost(None, 3000.0) == 0.0


# ======================================================================
# TriageAgent
# ======================================================================


class TestTriageAgent:
    """Test TriageAgent finding triage."""

    def _make_agent(self, run_context: RunContext) -> TriageAgent:
        return TriageAgent(
            run_context=run_context,
            worker_model=DryRunModelClient(),
            advisor_model=DryRunModelClient(),
        )

    @pytest.mark.asyncio
    async def test_no_findings(self, run_context: RunContext) -> None:
        """Returns success with empty findings when nothing to triage."""
        agent = self._make_agent(run_context)
        result = await agent.run(exploit_data={}, static_data={})

        assert result.success is True
        assert result.data["findings"] == []
        assert result.data["triaged"] == 0

    @pytest.mark.asyncio
    async def test_kill_switch(self, run_context: RunContext) -> None:
        """Returns failure when kill-switch is active."""
        run_context.kill()
        agent = self._make_agent(run_context)
        result = await agent.run()

        assert result.success is False
        assert "kill" in result.message.lower()

    @pytest.mark.asyncio
    async def test_triages_findings(self, run_context: RunContext) -> None:
        """Triages dynamic and static findings."""
        agent = self._make_agent(run_context)
        findings = [
            {"id": "f1", "target": "example.com", "vuln_type": "xss", "severity": "high"},
            {"id": "f2", "target": "example.com", "vuln_type": "sqli", "severity": "critical"},
        ]
        result = await agent.run(
            exploit_data={"findings": findings, "attempts": []},
            static_data={"findings": []},
        )

        assert result.success is True
        assert len(result.data["findings"]) == 2

    def test_deduplicate(self, run_context: RunContext) -> None:
        """Deduplicates findings by target + vuln_type."""
        agent = self._make_agent(run_context)
        findings = [
            {"id": "f1", "target": "example.com", "vuln_type": "xss"},
            {"id": "f2", "target": "example.com", "vuln_type": "xss"},
            {"id": "f3", "target": "example.com", "vuln_type": "sqli"},
        ]
        unique = agent._deduplicate(findings)

        assert len(unique) == 2
        assert {f["vuln_type"] for f in unique} == {"xss", "sqli"}

    def test_cluster_findings(self, run_context: RunContext) -> None:
        """Clusters findings by vulnerability type."""
        agent = self._make_agent(run_context)
        findings = [
            {"id": "f1", "vuln_type": "xss"},
            {"id": "f2", "vuln_type": "xss"},
            {"id": "f3", "vuln_type": "sqli"},
        ]
        clusters = agent._cluster_findings(findings)

        assert len(clusters) == 2
        assert len(clusters["xss"]) == 2
        assert len(clusters["sqli"]) == 1

    def test_prioritize(self, run_context: RunContext) -> None:
        """Prioritizes findings by severity order."""
        agent = self._make_agent(run_context)
        findings = [
            {"id": "f1", "severity": "low"},
            {"id": "f2", "severity": "critical"},
            {"id": "f3", "severity": "high"},
            {"id": "f4", "severity": "critical", "status": "false_positive"},
        ]
        prioritized = agent._prioritize(findings)

        assert len(prioritized) == 3  # false_positive excluded
        assert prioritized[0]["severity"] == "critical"
        assert prioritized[1]["severity"] == "high"
        assert prioritized[2]["severity"] == "low"

    def test_group_by_severity(self, run_context: RunContext) -> None:
        """Groups finding counts by severity."""
        agent = self._make_agent(run_context)
        findings = [
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "low"},
        ]
        grouped = agent._group_by_severity(findings)

        assert grouped["high"] == 2
        assert grouped["low"] == 1

    def test_economic_decision_delegates(self, run_context: RunContext) -> None:
        """_economic_decision uses EconomicAnalyzer."""
        agent = self._make_agent(run_context)
        result = agent._economic_decision([])

        assert result["decision"] == "SKIP"

    def test_agent_metadata(self, run_context: RunContext) -> None:
        """Agent has correct name and phase."""
        agent = self._make_agent(run_context)
        assert agent.name == "triage"
        assert agent.phase == "triage"
