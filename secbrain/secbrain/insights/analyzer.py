"""Insights analyzer - extracts actionable recommendations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from secbrain.insights.aggregator import WorkspaceData


@dataclass
class ActionableInsight:
    """A single actionable insight."""

    category: str
    priority: str  # "critical", "high", "medium", "low"
    title: str
    description: str
    action: str  # What to do next
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class AnalysisResults:
    """Analysis results with actionable insights."""

    insights: list[ActionableInsight] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    def get_critical_insights(self) -> list[ActionableInsight]:
        """Get critical priority insights."""
        return [i for i in self.insights if i.priority == "critical"]

    def get_high_priority_insights(self) -> list[ActionableInsight]:
        """Get high priority insights."""
        return [i for i in self.insights if i.priority == "high"]

    def get_by_category(self, category: str) -> list[ActionableInsight]:
        """Get insights by category."""
        return [i for i in self.insights if i.category == category]


class InsightsAnalyzer:
    """Analyzes workspace data to extract actionable insights."""

    def __init__(self):
        """Initialize analyzer."""
        self.categories = [
            "reconnaissance",
            "hypothesis_generation",
            "exploitation",
            "code_quality",
            "performance",
            "security",
        ]

    def analyze(self, data: WorkspaceData) -> AnalysisResults:
        """
        Analyze workspace data and generate insights.

        Args:
            data: Aggregated workspace data

        Returns:
            AnalysisResults with actionable insights
        """
        results = AnalysisResults()

        # Generate metrics summary
        results.metrics = self._generate_metrics(data)

        # Analyze each category
        results.insights.extend(self._analyze_recon(data))
        results.insights.extend(self._analyze_hypotheses(data))
        results.insights.extend(self._analyze_exploitation(data))
        results.insights.extend(self._analyze_performance(data))
        results.insights.extend(self._analyze_learnings(data))

        # Generate high-level summary
        results.summary = self._generate_summary(data, results)

        # Generate recommendations
        results.recommendations = self._generate_recommendations(results)

        return results

    def _generate_metrics(self, data: WorkspaceData) -> dict[str, Any]:
        """Generate key metrics."""
        return {
            "total_runs": data.total_runs,
            "successful_runs": data.successful_runs,
            "success_rate": data.successful_runs / max(data.total_runs, 1) * 100,
            "total_hypotheses": data.total_hypotheses,
            "total_attempts": data.total_attempts,
            "avg_hypotheses_per_run": data.total_hypotheses / max(data.total_runs, 1),
            "avg_attempts_per_run": data.total_attempts / max(data.total_runs, 1),
        }

    def _analyze_recon(self, data: WorkspaceData) -> list[ActionableInsight]:
        """Analyze reconnaissance phase."""
        insights = []

        recon_data = data.phases.get("recon", {}).get("data", {})
        assets = recon_data.get("assets", [])
        failed_count = recon_data.get("failed_count", 0)
        compiled_count = recon_data.get("compiled_count", 0)

        if failed_count > 0:
            insights.append(
                ActionableInsight(
                    category="reconnaissance",
                    priority="high",
                    title=f"{failed_count} contracts failed compilation",
                    description=f"Out of {len(assets)} contracts, {failed_count} failed to compile. This blocks vulnerability analysis.",
                    action="Fix the Foundry project setup. Check that dependencies are installed and foundry.toml is configured correctly. Review compilation errors in recon.json.",
                    context={
                        "failed_count": failed_count,
                        "total_count": len(assets),
                        "compiled_count": compiled_count,
                    },
                )
            )

        if compiled_count == 0 and len(assets) > 0:
            insights.append(
                ActionableInsight(
                    category="reconnaissance",
                    priority="critical",
                    title="No contracts compiled successfully",
                    description="Cannot proceed with security analysis without compiled contracts.",
                    action="Ensure Foundry is installed and the project compiles. Run 'forge build' in the instascope directory.",
                    context={"asset_count": len(assets)},
                )
            )

        return insights

    def _analyze_hypotheses(self, data: WorkspaceData) -> list[ActionableInsight]:
        """Analyze hypothesis generation."""
        insights = []

        hyp_data = data.phases.get("hypothesis", {}).get("data", {})
        hypotheses = hyp_data.get("hypotheses", [])
        missing_targets = hyp_data.get("missing_targets", {})

        if len(hypotheses) == 0:
            insights.append(
                ActionableInsight(
                    category="hypothesis_generation",
                    priority="critical",
                    title="No hypotheses generated",
                    description="The system did not generate any vulnerability hypotheses. This prevents exploit testing.",
                    action="Check that recon phase completed successfully and contracts were compiled. Review plan.json to ensure hypothesis phase is enabled.",
                    context={},
                )
            )

        if missing_targets.get("missing_contract_or_function", 0) > 0:
            total = missing_targets.get("total_hypotheses", 0)
            missing = missing_targets.get("missing_contract_or_function", 0)
            insights.append(
                ActionableInsight(
                    category="hypothesis_generation",
                    priority="medium",
                    title=f"{missing} hypotheses missing concrete targets",
                    description=f"{missing} out of {total} hypotheses lack specific contract/function targets.",
                    action="Improve hypothesis quality by providing more specific target information during generation.",
                    context={"missing": missing, "total": total},
                )
            )

        return insights

    def _analyze_exploitation(self, data: WorkspaceData) -> list[ActionableInsight]:
        """Analyze exploitation attempts."""
        insights = []

        if len(data.exploit_attempts) == 0 and data.total_hypotheses > 0:
            insights.append(
                ActionableInsight(
                    category="exploitation",
                    priority="high",
                    title="No exploitation attempts were made",
                    description="Hypotheses were generated but no exploits were attempted.",
                    action="Check exploit phase configuration. Ensure RPC URL is set and hypotheses have concrete targets.",
                    context={"hypotheses": data.total_hypotheses},
                )
            )

        # Check for profitable attempts
        profitable = [a for a in data.exploit_attempts if (a.get("profit_eth") or 0) > 0]
        if profitable:
            insights.append(
                ActionableInsight(
                    category="exploitation",
                    priority="critical",
                    title=f"🎯 {len(profitable)} profitable exploit(s) found!",
                    description=f"Found {len(profitable)} exploit attempts with positive profit. These are potential vulnerabilities.",
                    action="Review the exploit code in the attempt directories. Validate the findings and prepare reports for submission.",
                    context={
                        "profitable_count": len(profitable),
                        "attempts": profitable,
                    },
                )
            )

        # Analyze failure patterns
        failed = [a for a in data.exploit_attempts if not a.get("success", False)]
        if len(failed) > 0.8 * len(data.exploit_attempts) and len(data.exploit_attempts) > 5:
            insights.append(
                ActionableInsight(
                    category="exploitation",
                    priority="medium",
                    title="High exploit failure rate",
                    description=f"{len(failed)} out of {len(data.exploit_attempts)} attempts failed ({len(failed) / len(data.exploit_attempts) * 100:.1f}%).",
                    action="Review failure logs to identify common issues. Consider improving exploit templates or hypothesis quality.",
                    context={
                        "failed_count": len(failed),
                        "total_count": len(data.exploit_attempts),
                    },
                )
            )

        return insights

    def _analyze_performance(self, data: WorkspaceData) -> list[ActionableInsight]:
        """Analyze performance metrics."""
        insights = []

        if data.meta_metrics:
            durations = [m.get("total_duration_seconds", 0) for m in data.meta_metrics]
            avg_duration = sum(durations) / len(durations) if durations else 0

            if avg_duration > 300:  # 5 minutes
                insights.append(
                    ActionableInsight(
                        category="performance",
                        priority="medium",
                        title=f"Long average run time: {avg_duration / 60:.1f} minutes",
                        description="Workflow runs are taking longer than expected.",
                        action="Consider optimizing compilation, reducing hypothesis count, or parallelizing exploit attempts.",
                        context={"avg_duration": avg_duration},
                    )
                )

        return insights

    def _analyze_learnings(self, data: WorkspaceData) -> list[ActionableInsight]:
        """Analyze learnings data."""
        insights = []

        if data.learnings:
            # Get most recent learning
            latest = data.learnings[-1]
            recs = latest.get("recommendations", [])

            if recs:
                for rec in recs[:3]:  # Top 3 recommendations
                    insights.append(
                        ActionableInsight(
                            category="security",
                            priority="low",
                            title="Learning recommendation",
                            description=rec,
                            action="Review and consider implementing this recommendation.",
                            context={},
                        )
                    )

        return insights

    def _generate_summary(self, data: WorkspaceData, results: AnalysisResults) -> dict[str, Any]:
        """Generate high-level summary."""
        critical = results.get_critical_insights()
        high = results.get_high_priority_insights()

        return {
            "workspace": str(data.workspace_path),
            "total_insights": len(results.insights),
            "critical_count": len(critical),
            "high_count": len(high),
            "status": "requires_attention" if critical else ("review_recommended" if high else "healthy"),
            "next_action": critical[0].action if critical else (high[0].action if high else "Continue security research"),
        }

    def _generate_recommendations(self, results: AnalysisResults) -> list[str]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Add critical items first
        for insight in results.get_critical_insights():
            recommendations.append(f"[CRITICAL] {insight.title} - {insight.action}")

        # Add high priority items
        for insight in results.get_high_priority_insights():
            recommendations.append(f"[HIGH] {insight.title} - {insight.action}")

        return recommendations[:10]  # Top 10
