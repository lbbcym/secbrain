"""Tests for secbrain.agents.reporting_agent.ReportingAgent.

Covers the public interface of the reporting agent including:
- run() with no findings, with findings, and under the kill switch
- _format_title() with URL targets and plain-text targets
- _generate_summary() counting logic
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from secbrain.agents.reporting_agent import ReportingAgent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_run_context(
    tmp_path: Path,
    *,
    killed: bool = False,
    dry_run: bool = True,
    run_id: str = "test-run-001",
) -> Mock:
    """Build a lightweight Mock that satisfies BaseAgent.__init__."""
    ctx = Mock()
    ctx.run_id = run_id
    ctx.workspace_path = tmp_path
    ctx.dry_run = dry_run
    ctx.is_killed = Mock(return_value=killed)
    ctx.should_run_phase = Mock(return_value=True)
    ctx.worker_model = None
    ctx.advisor_model = None
    # LLM / research caching stubs
    ctx.get_cached_llm = Mock(return_value=None)
    ctx.cache_llm = Mock()
    ctx.get_cached_research = Mock(return_value=None)
    ctx.cache_research = Mock()
    return ctx


def _make_worker_model(response: str = "## Report Content\nGenerated report.") -> Mock:
    """Build a mock worker model that returns a canned response."""
    model = Mock()

    async def _generate(prompt: str, system: str | None = None, **kwargs: Any) -> Mock:
        resp = Mock()
        resp.content = response
        return resp

    model.generate = _generate
    return model


def _make_advisor_model() -> Mock:
    """Build a mock advisor model (not actively used in reporting, but required)."""
    model = Mock()

    async def _generate(prompt: str, system: str | None = None, **kwargs: Any) -> Mock:
        resp = Mock()
        resp.content = "{}"
        return resp

    model.generate = _generate
    return model


def _make_agent(
    tmp_path: Path,
    *,
    killed: bool = False,
    worker_response: str = "## Report\nGenerated.",
) -> ReportingAgent:
    """Instantiate a ReportingAgent with fully mocked dependencies."""
    ctx = _make_run_context(tmp_path, killed=killed)
    worker = _make_worker_model(response=worker_response)
    advisor = _make_advisor_model()
    return ReportingAgent(
        run_context=ctx,
        worker_model=worker,
        advisor_model=advisor,
    )


# ---------------------------------------------------------------------------
# Test classes
# ---------------------------------------------------------------------------


class TestRunNoFindings:
    """Tests for ReportingAgent.run() when there are no findings."""

    async def test_returns_success(self, tmp_path: Path):
        """run() with empty findings should return a successful result."""
        agent = _make_agent(tmp_path)
        result = await agent.run(triage_data={"findings": []})

        assert result.success is True

    async def test_reports_list_is_empty(self, tmp_path: Path):
        """run() with empty findings should produce an empty reports list."""
        agent = _make_agent(tmp_path)
        result = await agent.run(triage_data={"findings": []})

        assert result.data["reports"] == []

    async def test_message_indicates_nothing_to_report(self, tmp_path: Path):
        """run() message should indicate there were no findings to report."""
        agent = _make_agent(tmp_path)
        result = await agent.run(triage_data={"findings": []})

        assert "No findings" in result.message

    async def test_missing_triage_data_treated_as_empty(self, tmp_path: Path):
        """run() with no triage_data kwarg should behave like empty findings."""
        agent = _make_agent(tmp_path)
        result = await agent.run()

        assert result.success is True
        assert result.data["reports"] == []


class TestRunWithFindings:
    """Tests for ReportingAgent.run() when reportable findings exist."""

    @pytest.fixture
    def findings(self) -> list[dict[str, Any]]:
        """A small set of reportable findings."""
        return [
            {
                "id": "vuln-001",
                "vuln_type": "XSS",
                "target": "https://example.com/search",
                "severity": "high",
                "status": "confirmed",
                "description": "Reflected XSS in search parameter",
                "evidence": [{"type": "request", "data": "<script>alert(1)</script>"}],
            },
            {
                "id": "vuln-002",
                "vuln_type": "SQLI",
                "target": "https://example.com/api/users",
                "severity": "critical",
                "status": "confirmed",
                "description": "SQL injection in users endpoint",
                "evidence": [{"type": "request", "data": "' OR 1=1 --"}],
            },
        ]

    async def test_generates_reports_for_each_finding(
        self, tmp_path: Path, findings: list[dict[str, Any]]
    ):
        """run() should generate one report per reportable finding."""
        agent = _make_agent(tmp_path)
        result = await agent.run(triage_data={"findings": findings})

        assert result.success is True
        assert len(result.data["reports"]) == 2

    async def test_report_ids_match_findings(
        self, tmp_path: Path, findings: list[dict[str, Any]]
    ):
        """Each report id should correspond to its source finding id."""
        agent = _make_agent(tmp_path)
        result = await agent.run(triage_data={"findings": findings})

        report_ids = {r["id"] for r in result.data["reports"]}
        assert report_ids == {"vuln-001", "vuln-002"}

    async def test_summary_is_populated(
        self, tmp_path: Path, findings: list[dict[str, Any]]
    ):
        """run() should include a summary with total_reports."""
        agent = _make_agent(tmp_path)
        result = await agent.run(triage_data={"findings": findings})

        summary = result.data["summary"]
        assert summary["total_reports"] == 2

    async def test_reports_saved_to_workspace(
        self, tmp_path: Path, findings: list[dict[str, Any]]
    ):
        """run() should write markdown report files into the workspace."""
        agent = _make_agent(tmp_path)
        await agent.run(triage_data={"findings": findings})

        reports_dir = tmp_path / "reports"
        assert reports_dir.exists()
        saved_files = list(reports_dir.glob("*.md"))
        assert len(saved_files) == 2

    async def test_filters_out_false_positives(self, tmp_path: Path):
        """run() should exclude findings marked as false_positive."""
        findings = [
            {
                "id": "vuln-fp",
                "vuln_type": "XSS",
                "target": "https://example.com",
                "severity": "high",
                "status": "false_positive",
                "description": "Not a real finding",
                "evidence": [],
            },
        ]
        agent = _make_agent(tmp_path)
        result = await agent.run(triage_data={"findings": findings})

        assert result.success is True
        assert result.data["reports"] == []

    async def test_filters_out_low_severity(self, tmp_path: Path):
        """run() should exclude findings with severity below medium."""
        findings = [
            {
                "id": "vuln-low",
                "vuln_type": "Info Disclosure",
                "target": "https://example.com",
                "severity": "low",
                "status": "confirmed",
                "description": "Low severity issue",
                "evidence": [],
            },
        ]
        agent = _make_agent(tmp_path)
        result = await agent.run(triage_data={"findings": findings})

        assert result.success is True
        assert result.data["reports"] == []

    async def test_filters_out_duplicates(self, tmp_path: Path):
        """run() should exclude findings with status 'duplicate'."""
        findings = [
            {
                "id": "vuln-dup",
                "vuln_type": "SQLI",
                "target": "https://example.com",
                "severity": "critical",
                "status": "duplicate",
                "description": "Duplicate finding",
                "evidence": [],
            },
        ]
        agent = _make_agent(tmp_path)
        result = await agent.run(triage_data={"findings": findings})

        assert result.success is True
        assert result.data["reports"] == []

    async def test_message_contains_report_count(
        self, tmp_path: Path, findings: list[dict[str, Any]]
    ):
        """run() message should state how many reports were generated."""
        agent = _make_agent(tmp_path)
        result = await agent.run(triage_data={"findings": findings})

        assert "2" in result.message


class TestRunKillSwitch:
    """Tests for ReportingAgent.run() when the kill switch is active."""

    async def test_returns_failure(self, tmp_path: Path):
        """run() should return a failure result when the kill switch fires."""
        agent = _make_agent(tmp_path, killed=True)
        result = await agent.run(triage_data={"findings": []})

        assert result.success is False

    async def test_message_mentions_kill_switch(self, tmp_path: Path):
        """run() failure message should reference the kill switch."""
        agent = _make_agent(tmp_path, killed=True)
        result = await agent.run(triage_data={"findings": []})

        assert "Kill" in result.message or "kill" in result.message.lower()


class TestFormatTitle:
    """Tests for ReportingAgent._format_title()."""

    def _agent(self, tmp_path: Path) -> ReportingAgent:
        """Create a ReportingAgent for title-formatting tests."""
        return _make_agent(tmp_path)

    def test_url_target_extracts_domain(self, tmp_path: Path):
        """_format_title should extract the domain from an HTTP URL target."""
        agent = self._agent(tmp_path)
        finding = {"vuln_type": "XSS", "target": "https://app.example.com/search?q=1"}
        title = agent._format_title(finding)

        assert "app.example.com" in title

    def test_url_target_excludes_path(self, tmp_path: Path):
        """_format_title should not include the URL path in the title."""
        agent = self._agent(tmp_path)
        finding = {"vuln_type": "XSS", "target": "https://example.com/search?q=1"}
        title = agent._format_title(finding)

        assert "/search" not in title

    def test_non_url_target_used_as_is(self, tmp_path: Path):
        """_format_title should use a non-URL target string directly."""
        agent = self._agent(tmp_path)
        finding = {"vuln_type": "SQLI", "target": "internal-api-server"}
        title = agent._format_title(finding)

        assert "internal-api-server" in title

    def test_vuln_type_uppercased(self, tmp_path: Path):
        """_format_title should upper-case the vulnerability type."""
        agent = self._agent(tmp_path)
        finding = {"vuln_type": "xss", "target": "example.com"}
        title = agent._format_title(finding)

        assert "XSS" in title

    def test_missing_vuln_type_defaults(self, tmp_path: Path):
        """_format_title should use 'Vulnerability' when vuln_type is absent."""
        agent = self._agent(tmp_path)
        finding = {"target": "example.com"}
        title = agent._format_title(finding)

        assert "VULNERABILITY" in title

    def test_missing_target_produces_empty_domain(self, tmp_path: Path):
        """_format_title should handle a missing target gracefully."""
        agent = self._agent(tmp_path)
        finding = {"vuln_type": "XSS"}
        title = agent._format_title(finding)

        # Should still produce a string without raising
        assert "XSS" in title


class TestGenerateSummary:
    """Tests for ReportingAgent._generate_summary()."""

    def _agent(self, tmp_path: Path) -> ReportingAgent:
        """Create a ReportingAgent for summary tests."""
        return _make_agent(tmp_path)

    def test_empty_reports_returns_zero_total(self, tmp_path: Path):
        """_generate_summary with no reports should report total_reports=0."""
        agent = self._agent(tmp_path)
        summary = agent._generate_summary([])

        assert summary["total_reports"] == 0
        assert summary["by_severity"] == {}
        assert summary["by_type"] == {}

    def test_counts_by_severity(self, tmp_path: Path):
        """_generate_summary should correctly count reports per severity."""
        agent = self._agent(tmp_path)
        reports = [
            {"severity": "high", "vuln_type": "XSS"},
            {"severity": "high", "vuln_type": "SQLI"},
            {"severity": "critical", "vuln_type": "RCE"},
        ]
        summary = agent._generate_summary(reports)

        assert summary["total_reports"] == 3
        assert summary["by_severity"]["high"] == 2
        assert summary["by_severity"]["critical"] == 1

    def test_counts_by_type(self, tmp_path: Path):
        """_generate_summary should correctly count reports per vuln_type."""
        agent = self._agent(tmp_path)
        reports = [
            {"severity": "high", "vuln_type": "XSS"},
            {"severity": "medium", "vuln_type": "XSS"},
            {"severity": "critical", "vuln_type": "RCE"},
        ]
        summary = agent._generate_summary(reports)

        assert summary["by_type"]["XSS"] == 2
        assert summary["by_type"]["RCE"] == 1

    def test_generated_at_present(self, tmp_path: Path):
        """_generate_summary should include a generated_at timestamp."""
        agent = self._agent(tmp_path)
        summary = agent._generate_summary([])

        assert "generated_at" in summary

    def test_unknown_severity_counted(self, tmp_path: Path):
        """Reports missing a severity key should be counted as 'unknown'."""
        agent = self._agent(tmp_path)
        reports = [
            {"vuln_type": "XSS"},
            {"severity": "high", "vuln_type": "SQLI"},
        ]
        summary = agent._generate_summary(reports)

        assert summary["by_severity"]["unknown"] == 1
        assert summary["by_severity"]["high"] == 1

    def test_unknown_type_counted(self, tmp_path: Path):
        """Reports missing a vuln_type key should be counted as 'unknown'."""
        agent = self._agent(tmp_path)
        reports = [
            {"severity": "high"},
        ]
        summary = agent._generate_summary(reports)

        assert summary["by_type"]["unknown"] == 1
