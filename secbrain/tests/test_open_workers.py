"""Tests for OpenWorkerClient and OllamaClient."""

from __future__ import annotations

import warnings
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from secbrain.models.base import ModelResponse
from secbrain.models.open_workers import OllamaClient, OpenWorkerClient

# ======================================================================
# OpenWorkerClient
# ======================================================================


class TestOpenWorkerClient:
    """Test OpenWorkerClient for OpenAI-compatible APIs."""

    def test_init_with_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Initializes with explicit API key."""
        monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = OpenWorkerClient(api_key="test-key")

        assert client.api_key == "test-key"

    def test_init_default_model(self) -> None:
        """Uses default model name."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = OpenWorkerClient(api_key="key")

        assert "Llama" in client.model or "llama" in client.model

    def test_init_custom_base_url(self) -> None:
        """Supports custom base URL."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = OpenWorkerClient(
                api_key="key",
                base_url="https://custom-api.com/v1",
            )

        assert client.base_url == "https://custom-api.com/v1"

    def test_init_warns_no_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Warns when no API key is found."""
        monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        with pytest.warns(UserWarning, match="No API key"):
            client = OpenWorkerClient()
        assert client.api_key == ""

    def test_init_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Picks up TOGETHER_API_KEY from env."""
        monkeypatch.setenv("TOGETHER_API_KEY", "env-together-key")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = OpenWorkerClient()

        assert client.api_key == "env-together-key"

    @pytest.mark.asyncio
    async def test_generate_success(self) -> None:
        """Returns ModelResponse on successful API call."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = OpenWorkerClient(api_key="fake")

        mock_response = httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
                "model": "test-model",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            },
            request=httpx.Request("POST", "http://test/chat/completions"),
        )

        client.client = MagicMock()
        client.client.post = AsyncMock(return_value=mock_response)

        result = await client.generate("Hi")

        assert isinstance(result, ModelResponse)
        assert result.content == "Hello!"
        assert result.finish_reason == "stop"
        assert result.prompt_tokens == 10

    @pytest.mark.asyncio
    async def test_generate_http_error(self) -> None:
        """Returns error response on HTTP failure."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = OpenWorkerClient(api_key="fake")

        client.client = MagicMock()
        client.client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "rate limit",
                request=httpx.Request("POST", "http://test"),
                response=httpx.Response(429),
            )
        )

        result = await client.generate("Hi")

        assert result.finish_reason == "error"
        assert result.content == ""

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self) -> None:
        """Includes system message when provided."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = OpenWorkerClient(api_key="fake")

        captured_payload: dict[str, Any] = {}

        async def mock_post(url: str, json: dict[str, Any]) -> httpx.Response:
            captured_payload.update(json)
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                    "model": "test",
                    "usage": {},
                },
                request=httpx.Request("POST", "http://test/chat/completions"),
            )

        client.client = MagicMock()
        client.client.post = mock_post

        await client.generate("user msg", system="system msg")

        assert len(captured_payload["messages"]) == 2
        assert captured_payload["messages"][0]["role"] == "system"

    @pytest.mark.asyncio
    async def test_generate_structured_parses_json(self) -> None:
        """Parses valid JSON from response."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = OpenWorkerClient(api_key="fake")

        async def mock_generate(prompt, system=None, **kwargs):
            return ModelResponse(
                content='{"status": "ok"}', model="test", finish_reason="stop"
            )

        client.generate = mock_generate  # type: ignore[assignment]

        result = await client.generate_structured("test", {"type": "object"})
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_generate_structured_strips_markdown(self) -> None:
        """Handles markdown-wrapped JSON."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = OpenWorkerClient(api_key="fake")

        async def mock_generate(prompt, system=None, **kwargs):
            return ModelResponse(
                content='```json\n{"value": 42}\n```', model="test", finish_reason="stop"
            )

        client.generate = mock_generate  # type: ignore[assignment]

        result = await client.generate_structured("test", {"type": "object"})
        assert result["value"] == 42

    @pytest.mark.asyncio
    async def test_generate_structured_invalid_json(self) -> None:
        """Returns empty dict for invalid JSON."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = OpenWorkerClient(api_key="fake")

        async def mock_generate(prompt, system=None, **kwargs):
            return ModelResponse(content="nope!", model="test", finish_reason="stop")

        client.generate = mock_generate  # type: ignore[assignment]

        result = await client.generate_structured("test", {"type": "object"})
        assert result == {}

    @pytest.mark.asyncio
    async def test_generate_structured_failed_generation(self) -> None:
        """Returns empty dict when generation itself fails."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = OpenWorkerClient(api_key="fake")

        async def mock_generate(prompt, system=None, **kwargs):
            return ModelResponse(content="", model="test", finish_reason="error")

        client.generate = mock_generate  # type: ignore[assignment]

        result = await client.generate_structured("test", {"type": "object"})
        assert result == {}

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Closes the HTTP client."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = OpenWorkerClient(api_key="fake")

        client.client = MagicMock()
        client.client.aclose = AsyncMock()

        await client.close()
        client.client.aclose.assert_called_once()


# ======================================================================
# OllamaClient
# ======================================================================


class TestOllamaClient:
    """Test OllamaClient for local Ollama models."""

    def test_init_defaults(self) -> None:
        """Initializes with default values."""
        client = OllamaClient()
        assert client.model == "llama3.1"
        assert client.base_url == "http://localhost:11434"

    def test_init_custom(self) -> None:
        """Initializes with custom values."""
        client = OllamaClient(model="mistral", base_url="http://gpu:11434")
        assert client.model == "mistral"
        assert client.base_url == "http://gpu:11434"

    @pytest.mark.asyncio
    async def test_generate_success(self) -> None:
        """Returns ModelResponse on success."""
        client = OllamaClient()

        mock_response = httpx.Response(
            200,
            json={
                "response": "Generated text",
                "model": "llama3.1",
                "done": True,
                "prompt_eval_count": 20,
                "eval_count": 15,
            },
            request=httpx.Request("POST", "http://localhost:11434/api/generate"),
        )

        client.client = MagicMock()
        client.client.post = AsyncMock(return_value=mock_response)

        result = await client.generate("Test prompt")

        assert result.content == "Generated text"
        assert result.finish_reason == "stop"
        assert result.prompt_tokens == 20
        assert result.completion_tokens == 15

    @pytest.mark.asyncio
    async def test_generate_not_done(self) -> None:
        """Sets finish_reason to length when not done."""
        client = OllamaClient()

        mock_response = httpx.Response(
            200,
            json={"response": "Partial", "model": "llama3.1", "done": False},
            request=httpx.Request("POST", "http://localhost:11434/api/generate"),
        )

        client.client = MagicMock()
        client.client.post = AsyncMock(return_value=mock_response)

        result = await client.generate("Test")
        assert result.finish_reason == "length"

    @pytest.mark.asyncio
    async def test_generate_http_error(self) -> None:
        """Returns error response on connection failure."""
        client = OllamaClient()

        client.client = MagicMock()
        client.client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

        result = await client.generate("Test")
        assert result.finish_reason == "error"

    @pytest.mark.asyncio
    async def test_generate_structured(self) -> None:
        """Parses structured JSON from Ollama."""
        client = OllamaClient()

        async def mock_generate(prompt, system=None, **kwargs):
            return ModelResponse(
                content='{"answer": "yes"}', model="test", finish_reason="stop"
            )

        client.generate = mock_generate  # type: ignore[assignment]

        result = await client.generate_structured("test", {"type": "object"})
        assert result["answer"] == "yes"

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Closes the HTTP client."""
        client = OllamaClient()
        client.client = MagicMock()
        client.client.aclose = AsyncMock()

        await client.close()
        client.client.aclose.assert_called_once()
