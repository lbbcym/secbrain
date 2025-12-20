from collections import deque
from pathlib import Path

import httpx
import pytest

from secbrain.core.context import ProgramConfig, RunContext, ScopeConfig
from secbrain.tools.http_client import SecBrainHTTPClient


def _client_with_transport(run_context: RunContext, responses: deque[httpx.Response]) -> SecBrainHTTPClient:
    async def handler(request: httpx.Request) -> httpx.Response:
        if not responses:
            raise RuntimeError("No more mock responses")
        return responses.popleft()

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    return SecBrainHTTPClient(run_context, max_retries=2, backoff_factor=0.01, client=client)


@pytest.mark.asyncio
async def test_http_client_retries_then_succeeds(tmp_path: Path) -> None:
    run_context = RunContext(
        workspace_path=tmp_path,
        dry_run=False,
        scope=ScopeConfig(domains=["example.com"]),
        program=ProgramConfig(name="Test"),
    )

    responses = deque(
        [
            httpx.Response(500, request=httpx.Request("GET", "https://example.com")),
            httpx.Response(200, request=httpx.Request("GET", "https://example.com"), json={"ok": True}),
        ]
    )
    client = _client_with_transport(run_context, responses)

    resp = await client.get("https://example.com")
    await client.close()

    assert resp.status_code == 200
    assert resp.metadata.get("retries") == 1
    assert resp.success is True


@pytest.mark.asyncio
async def test_http_client_retries_then_gives_up(tmp_path: Path) -> None:
    run_context = RunContext(
        workspace_path=tmp_path,
        dry_run=False,
        scope=ScopeConfig(domains=["example.com"]),
        program=ProgramConfig(name="Test"),
    )

    responses = deque(
        [
            httpx.Response(503, request=httpx.Request("GET", "https://example.com")),
            httpx.Response(503, request=httpx.Request("GET", "https://example.com")),
            httpx.Response(503, request=httpx.Request("GET", "https://example.com")),
        ]
    )
    client = _client_with_transport(run_context, responses)

    resp = await client.get("https://example.com")
    await client.close()

    assert resp.status_code == 503
    assert resp.metadata.get("retries") == 2
    assert resp.success is False
