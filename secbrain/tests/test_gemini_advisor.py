"""Tests for GeminiAdvisorClient."""

from __future__ import annotations

import json
import warnings
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from secbrain.models.base import ModelResponse
from secbrain.models.gemini_advisor import GeminiAdvisorClient


class TestGeminiAdvisorClient:
    """Test GeminiAdvisorClient initialization and methods."""

    def test_init_with_api_key(self) -> None:
        """Initializes correctly with explicit API key."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = GeminiAdvisorClient(api_key="test-key-123")

        assert client.api_key == "test-key-123"
        assert client.model == "gemini-2.0-flash-exp"

    def test_init_custom_model(self) -> None:
        """Initializes with custom model name."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = GeminiAdvisorClient(model="gemini-pro", api_key="key")

        assert client.model == "gemini-pro"

    def test_init_warns_no_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Warns when no API key is provided."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        with pytest.warns(UserWarning, match="No API key"):
            client = GeminiAdvisorClient()
        assert client.api_key == ""

    def test_init_uses_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Uses GOOGLE_API_KEY environment variable."""
        monkeypatch.setenv("GOOGLE_API_KEY", "env-key-456")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = GeminiAdvisorClient()

        assert client.api_key == "env-key-456"

    @pytest.mark.asyncio
    async def test_generate_returns_error_on_failure(self) -> None:
        """Returns error ModelResponse when generation fails."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = GeminiAdvisorClient(api_key="fake")

        # Mock _get_client to raise
        client._get_client = MagicMock(side_effect=Exception("API error"))

        result = await client.generate("test prompt")

        assert isinstance(result, ModelResponse)
        assert result.finish_reason == "error"
        assert result.content == ""
        assert "error" in result.raw_response

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self) -> None:
        """System prompt is prepended to user prompt."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = GeminiAdvisorClient(api_key="fake")

        # Create mock response
        mock_part = MagicMock()
        mock_part.text = "Generated response"
        mock_candidate = MagicMock()
        mock_candidate.content.parts = [mock_part]
        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_response.prompt_token_count = 10
        mock_response.candidates_token_count = 20

        mock_client = MagicMock()
        mock_client.generate_content = MagicMock(return_value=mock_response)
        client._client = mock_client

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_response)
            result = await client.generate("user prompt", system="system instructions")

        assert result.content == "Generated response"
        assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_structured_returns_empty_on_failure(self) -> None:
        """Returns empty dict when generation fails."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = GeminiAdvisorClient(api_key="fake")

        client._get_client = MagicMock(side_effect=Exception("fail"))

        result = await client.generate_structured("test", {"type": "object"})
        assert result == {}

    @pytest.mark.asyncio
    async def test_generate_structured_parses_json(self) -> None:
        """Parses JSON from model response."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = GeminiAdvisorClient(api_key="fake")

        json_content = json.dumps({"approved": True, "risk_level": "low"})

        async def mock_generate(prompt, system=None, **kwargs):
            return ModelResponse(
                content=json_content,
                model="gemini-test",
                finish_reason="stop",
            )

        client.generate = mock_generate  # type: ignore[assignment]

        result = await client.generate_structured("test", {"type": "object"})
        assert result["approved"] is True

    @pytest.mark.asyncio
    async def test_generate_structured_handles_markdown_blocks(self) -> None:
        """Strips markdown code blocks from response."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = GeminiAdvisorClient(api_key="fake")

        json_content = '```json\n{"result": "ok"}\n```'

        async def mock_generate(prompt, system=None, **kwargs):
            return ModelResponse(content=json_content, model="test", finish_reason="stop")

        client.generate = mock_generate  # type: ignore[assignment]

        result = await client.generate_structured("test", {"type": "object"})
        assert result["result"] == "ok"

    @pytest.mark.asyncio
    async def test_generate_structured_invalid_json(self) -> None:
        """Returns empty dict for invalid JSON."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = GeminiAdvisorClient(api_key="fake")

        async def mock_generate(prompt, system=None, **kwargs):
            return ModelResponse(content="not json!", model="test", finish_reason="stop")

        client.generate = mock_generate  # type: ignore[assignment]

        result = await client.generate_structured("test", {"type": "object"})
        assert result == {}

    @pytest.mark.asyncio
    async def test_review_plan(self) -> None:
        """review_plan delegates to generate_structured."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = GeminiAdvisorClient(api_key="fake")

        async def mock_gen_struct(prompt, schema, system=None, **kwargs):
            return {"approved": True, "concerns": [], "suggestions": [], "risk_level": "low"}

        client.generate_structured = mock_gen_struct  # type: ignore[assignment]

        result = await client.review_plan(
            plan={"steps": ["scan"]},
            context="test program",
        )

        assert result["approved"] is True
        assert result["risk_level"] == "low"

    @pytest.mark.asyncio
    async def test_validate_finding(self) -> None:
        """validate_finding delegates to generate_structured."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = GeminiAdvisorClient(api_key="fake")

        async def mock_gen_struct(prompt, schema, system=None, **kwargs):
            return {"valid": True, "confidence": 0.9, "severity_assessment": "high"}

        client.generate_structured = mock_gen_struct  # type: ignore[assignment]

        result = await client.validate_finding(
            finding={"vuln_type": "xss"},
            evidence=[{"type": "screenshot"}],
        )

        assert result["valid"] is True
        assert result["confidence"] == 0.9
