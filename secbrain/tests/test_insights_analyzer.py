"""Tests for InsightsAnalyzer."""

from __future__ import annotations

from pathlib import Path

from secbrain.insights.aggregator import WorkspaceData
from secbrain.insights.analyzer import (
    ActionableInsight,
    AnalysisResults,
    InsightsAnalyzer,
)

# ======================================================================
# ActionableInsight / AnalysisResults dataclasses
# ======================================================================


class TestActionableInsight:
    """Test ActionableInsight dataclass."""

    def test_basic_creation(self) -> None:
        insight = ActionableInsight(
            category="exploitation",
            priority="high",
            title="Test insight",
            description="A description",
            action="Do something",
        )
        assert insight.category == "exploitation"
        assert insight.priority == "high"
        assert insight.timestamp  # auto-populated


class TestAnalysisResults:
    """Test AnalysisResults dataclass."""

    def test_get_critical_insights(self) -> None:
        results = AnalysisResults(
            insights=[
                ActionableInsight("a", "critical", "t1", "d1", "a1"),
                ActionableInsight("b", "high", "t2", "d2", "a2"),
                ActionableInsight("c", "critical", "t3", "d3", "a3"),
            ]
        )
        critical = results.get_critical_insights()
        assert len(critical) == 2
        assert all(i.priority == "critical" for i in critical)

    def test_get_high_priority_insights(self) -> None:
        results = AnalysisResults(
            insights=[
                ActionableInsight("a", "critical", "t1", "d1", "a1"),
                ActionableInsight("b", "high", "t2", "d2", "a2"),
                ActionableInsight("c", "low", "t3", "d3", "a3"),
            ]
        )
        high = results.get_high_priority_insights()
        assert len(high) == 1
        assert high[0].title == "t2"

    def test_get_by_category(self) -> None:
        results = AnalysisResults(
            insights=[
                ActionableInsight("exploitation", "high", "t1", "d1", "a1"),
                ActionableInsight("recon", "medium", "t2", "d2", "a2"),
                ActionableInsight("exploitation", "low", "t3", "d3", "a3"),
            ]
        )
        exploit = results.get_by_category("exploitation")
        assert len(exploit) == 2


# ======================================================================
# InsightsAnalyzer
# ======================================================================


class TestInsightsAnalyzer:
    """Test InsightsAnalyzer analysis logic."""

    def _empty_data(self, tmp_path: Path) -> WorkspaceData:
        return WorkspaceData(workspace_path=tmp_path)

    # ------------------------------------------------------------------
    # Full analyze
    # ------------------------------------------------------------------

    def test_analyze_empty_data(self, tmp_path: Path) -> None:
        """Analyze returns results for empty workspace."""
        analyzer = InsightsAnalyzer()
        data = self._empty_data(tmp_path)
        results = analyzer.analyze(data)

        assert isinstance(results, AnalysisResults)
        assert results.metrics["total_runs"] == 0

    def test_analyze_with_data(self, tmp_path: Path) -> None:
        """Analyze generates insights from populated data."""
        analyzer = InsightsAnalyzer()
        data = WorkspaceData(
            workspace_path=tmp_path,
            run_summaries=[{"success": True}],
            meta_metrics=[{"hypotheses_count": 10, "attempts_count": 5}],
            phases={
                "recon": {"data": {"assets": [1, 2], "compiled_count": 2, "failed_count": 0}},
                "hypothesis": {"data": {"hypotheses": [{"id": "h1"}]}},
            },
            exploit_attempts=[{"profit_eth": 0.5, "success": True}],
        )
        results = analyzer.analyze(data)

        assert results.metrics["total_runs"] == 1
        assert results.metrics["success_rate"] == 100.0
        # Should have a profitable exploit insight
        assert any("profitable" in i.title.lower() for i in results.insights)

    # ------------------------------------------------------------------
    # _analyze_recon
    # ------------------------------------------------------------------

    def test_analyze_recon_no_issues(self, tmp_path: Path) -> None:
        """No insights when recon is fine."""
        analyzer = InsightsAnalyzer()
        data = WorkspaceData(
            workspace_path=tmp_path,
            phases={"recon": {"data": {"assets": [1], "compiled_count": 1, "failed_count": 0}}},
        )
        insights = analyzer._analyze_recon(data)
        assert len(insights) == 0

    def test_analyze_recon_compilation_failures(self, tmp_path: Path) -> None:
        """Reports compilation failures."""
        analyzer = InsightsAnalyzer()
        data = WorkspaceData(
            workspace_path=tmp_path,
            phases={"recon": {"data": {"assets": [1, 2, 3], "compiled_count": 1, "failed_count": 2}}},
        )
        insights = analyzer._analyze_recon(data)
        assert len(insights) == 1
        assert insights[0].priority == "high"
        assert "failed compilation" in insights[0].title.lower()

    def test_analyze_recon_zero_compiled(self, tmp_path: Path) -> None:
        """Critical insight when nothing compiled."""
        analyzer = InsightsAnalyzer()
        data = WorkspaceData(
            workspace_path=tmp_path,
            phases={"recon": {"data": {"assets": [1], "compiled_count": 0, "failed_count": 1}}},
        )
        insights = analyzer._analyze_recon(data)
        assert any(i.priority == "critical" for i in insights)

    # ------------------------------------------------------------------
    # _analyze_hypotheses
    # ------------------------------------------------------------------

    def test_analyze_hypotheses_none_generated(self, tmp_path: Path) -> None:
        """Critical insight when no hypotheses generated."""
        analyzer = InsightsAnalyzer()
        data = WorkspaceData(
            workspace_path=tmp_path,
            phases={"hypothesis": {"data": {"hypotheses": []}}},
        )
        insights = analyzer._analyze_hypotheses(data)
        assert len(insights) == 1
        assert insights[0].priority == "critical"

    def test_analyze_hypotheses_missing_targets(self, tmp_path: Path) -> None:
        """Medium insight when hypotheses lack targets."""
        analyzer = InsightsAnalyzer()
        data = WorkspaceData(
            workspace_path=tmp_path,
            phases={
                "hypothesis": {
                    "data": {
                        "hypotheses": [{"id": "h1"}],
                        "missing_targets": {
                            "total_hypotheses": 10,
                            "missing_contract_or_function": 5,
                        },
                    }
                }
            },
        )
        insights = analyzer._analyze_hypotheses(data)
        assert any(i.priority == "medium" for i in insights)

    # ------------------------------------------------------------------
    # _analyze_exploitation
    # ------------------------------------------------------------------

    def test_analyze_exploitation_no_attempts(self, tmp_path: Path) -> None:
        """High priority when hypotheses exist but no attempts."""
        analyzer = InsightsAnalyzer()
        data = WorkspaceData(
            workspace_path=tmp_path,
            meta_metrics=[{"hypotheses_count": 10, "attempts_count": 0}],
        )
        insights = analyzer._analyze_exploitation(data)
        assert any(i.priority == "high" for i in insights)

    def test_analyze_exploitation_profitable(self, tmp_path: Path) -> None:
        """Critical insight for profitable exploits."""
        analyzer = InsightsAnalyzer()
        data = WorkspaceData(
            workspace_path=tmp_path,
            exploit_attempts=[
                {"profit_eth": 1.5, "success": True},
                {"profit_eth": 0, "success": False},
            ],
        )
        insights = analyzer._analyze_exploitation(data)
        assert any(i.priority == "critical" and "profitable" in i.title.lower() for i in insights)

    def test_analyze_exploitation_high_failure_rate(self, tmp_path: Path) -> None:
        """Medium insight for high failure rate."""
        analyzer = InsightsAnalyzer()
        attempts = [{"success": False} for _ in range(9)] + [{"success": True}]
        data = WorkspaceData(workspace_path=tmp_path, exploit_attempts=attempts)
        insights = analyzer._analyze_exploitation(data)
        assert any("failure rate" in i.title.lower() for i in insights)

    # ------------------------------------------------------------------
    # _analyze_performance
    # ------------------------------------------------------------------

    def test_analyze_performance_long_duration(self, tmp_path: Path) -> None:
        """Flags long run duration."""
        analyzer = InsightsAnalyzer()
        data = WorkspaceData(
            workspace_path=tmp_path,
            meta_metrics=[{"total_duration_seconds": 600}],
        )
        insights = analyzer._analyze_performance(data)
        assert len(insights) == 1
        assert "run time" in insights[0].title.lower()

    def test_analyze_performance_ok(self, tmp_path: Path) -> None:
        """No insight for short duration."""
        analyzer = InsightsAnalyzer()
        data = WorkspaceData(
            workspace_path=tmp_path,
            meta_metrics=[{"total_duration_seconds": 60}],
        )
        insights = analyzer._analyze_performance(data)
        assert len(insights) == 0

    # ------------------------------------------------------------------
    # _analyze_learnings
    # ------------------------------------------------------------------

    def test_analyze_learnings_with_recs(self, tmp_path: Path) -> None:
        """Converts learnings recommendations to insights."""
        analyzer = InsightsAnalyzer()
        data = WorkspaceData(
            workspace_path=tmp_path,
            learnings=[{"recommendations": ["Do A", "Do B"]}],
        )
        insights = analyzer._analyze_learnings(data)
        assert len(insights) == 2

    def test_analyze_learnings_empty(self, tmp_path: Path) -> None:
        """No insights when no learnings."""
        analyzer = InsightsAnalyzer()
        data = self._empty_data(tmp_path)
        insights = analyzer._analyze_learnings(data)
        assert len(insights) == 0

    # ------------------------------------------------------------------
    # _generate_summary and _generate_recommendations
    # ------------------------------------------------------------------

    def test_generate_summary_healthy(self, tmp_path: Path) -> None:
        """Status is healthy when no critical/high insights."""
        analyzer = InsightsAnalyzer()
        data = self._empty_data(tmp_path)
        results = AnalysisResults()
        summary = analyzer._generate_summary(data, results)
        assert summary["status"] == "healthy"

    def test_generate_summary_requires_attention(self, tmp_path: Path) -> None:
        """Status is requires_attention with critical insights."""
        analyzer = InsightsAnalyzer()
        data = self._empty_data(tmp_path)
        results = AnalysisResults(
            insights=[ActionableInsight("a", "critical", "t", "d", "act")]
        )
        summary = analyzer._generate_summary(data, results)
        assert summary["status"] == "requires_attention"

    def test_generate_recommendations(self) -> None:
        """Recommendations are ordered by priority."""
        analyzer = InsightsAnalyzer()
        results = AnalysisResults(
            insights=[
                ActionableInsight("a", "high", "High issue", "d", "Fix high"),
                ActionableInsight("b", "critical", "Critical issue", "d", "Fix critical"),
            ]
        )
        recs = analyzer._generate_recommendations(results)
        assert recs[0].startswith("[CRITICAL]")
        assert recs[1].startswith("[HIGH]")
