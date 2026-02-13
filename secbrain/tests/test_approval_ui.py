"""Tests for secbrain.cli.approval_ui.interactive_approval_prompt.

Verifies that the interactive approval prompt correctly interprets operator
input (approve, deny, empty, case variations) and returns the expected
(approved, reason) tuple.  All I/O is mocked so no real stdin or terminal
output is required.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from secbrain.cli.approval_ui import interactive_approval_prompt
from secbrain.core.approval import ApprovalRequest


def _make_request(
    tool_name: str = "test_tool",
    risk_level: str = "high",
    operation: str = "GET https://example.com",
) -> ApprovalRequest:
    """Build a minimal ApprovalRequest for testing."""
    return ApprovalRequest(
        request_id="req-001",
        tool_name=tool_name,
        operation=operation,
        risk_level=risk_level,
        timestamp=datetime.now(UTC),
    )


class TestApprovalWithShorthand:
    """Tests for approval via the short-hand 'a' input."""

    async def test_approve_with_a(self):
        """Typing 'a' at the prompt should approve the request."""
        req = _make_request()
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="a")
            approved, reason = await interactive_approval_prompt(req)

        assert approved is True
        assert reason == "approved"

    async def test_approve_with_approve(self):
        """Typing 'approve' at the prompt should approve the request."""
        req = _make_request()
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="approve")
            approved, reason = await interactive_approval_prompt(req)

        assert approved is True
        assert reason == "approved"


class TestDenial:
    """Tests for denial via 'd', 'deny', or other non-approve inputs."""

    async def test_deny_with_d(self):
        """Typing 'd' at the prompt should deny the request."""
        req = _make_request()
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="d")
            approved, reason = await interactive_approval_prompt(req)

        assert approved is False
        assert reason == "denied"

    async def test_deny_with_deny(self):
        """Typing 'deny' at the prompt should deny the request."""
        req = _make_request()
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="deny")
            approved, reason = await interactive_approval_prompt(req)

        assert approved is False
        assert reason == "denied"

    async def test_deny_with_random_text(self):
        """Any unrecognised text should deny the request."""
        req = _make_request()
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="maybe")
            approved, reason = await interactive_approval_prompt(req)

        assert approved is False
        assert reason == "denied"


class TestEmptyInput:
    """Tests for empty or whitespace-only input."""

    async def test_empty_string_denies(self):
        """An empty string should be treated as a denial."""
        req = _make_request()
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="")
            approved, reason = await interactive_approval_prompt(req)

        assert approved is False
        assert reason == "denied"

    async def test_whitespace_only_denies(self):
        """Whitespace-only input should be treated as a denial."""
        req = _make_request()
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="   ")
            approved, reason = await interactive_approval_prompt(req)

        assert approved is False
        assert reason == "denied"

    async def test_none_coerced_to_empty_denies(self):
        """If to_thread somehow returns None it should be treated as denial."""
        req = _make_request()
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value=None)
            approved, reason = await interactive_approval_prompt(req)

        assert approved is False
        assert reason == "denied"


class TestCaseInsensitivity:
    """Tests to verify that input matching is case-insensitive."""

    async def test_uppercase_A(self):
        """'A' should approve."""
        req = _make_request()
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="A")
            approved, reason = await interactive_approval_prompt(req)

        assert approved is True
        assert reason == "approved"

    async def test_uppercase_APPROVE(self):
        """'APPROVE' should approve."""
        req = _make_request()
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="APPROVE")
            approved, reason = await interactive_approval_prompt(req)

        assert approved is True
        assert reason == "approved"

    async def test_mixed_case_Approve(self):
        """'Approve' (mixed case) should approve."""
        req = _make_request()
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="Approve")
            approved, reason = await interactive_approval_prompt(req)

        assert approved is True
        assert reason == "approved"

    async def test_uppercase_D_denies(self):
        """'D' should deny."""
        req = _make_request()
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="D")
            approved, reason = await interactive_approval_prompt(req)

        assert approved is False
        assert reason == "denied"

    async def test_uppercase_DENY(self):
        """'DENY' should deny."""
        req = _make_request()
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="DENY")
            approved, reason = await interactive_approval_prompt(req)

        assert approved is False
        assert reason == "denied"


class TestConsoleOutput:
    """Tests that verify the prompt prints expected information."""

    async def test_console_prints_tool_name(self):
        """The prompt should print the tool name from the request."""
        req = _make_request(tool_name="http_client")
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="d")
            await interactive_approval_prompt(req)

        # At least one print call should contain the tool name
        printed_texts = [
            str(call) for call in mock_console.print.call_args_list
        ]
        assert any("http_client" in text for text in printed_texts)

    async def test_console_prints_risk_level(self):
        """The prompt should print the risk level from the request."""
        req = _make_request(risk_level="critical")
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="d")
            await interactive_approval_prompt(req)

        printed_texts = [
            str(call) for call in mock_console.print.call_args_list
        ]
        assert any("critical" in text for text in printed_texts)

    async def test_console_prints_operation(self):
        """The prompt should print the operation description from the request."""
        req = _make_request(operation="DELETE /api/users/1")
        with patch("secbrain.cli.approval_ui.asyncio") as mock_asyncio, \
             patch("secbrain.cli.approval_ui._console") as mock_console:
            mock_asyncio.to_thread = AsyncMock(return_value="d")
            await interactive_approval_prompt(req)

        printed_texts = [
            str(call) for call in mock_console.print.call_args_list
        ]
        assert any("DELETE /api/users/1" in text for text in printed_texts)
