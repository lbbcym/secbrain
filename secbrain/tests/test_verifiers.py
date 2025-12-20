"""Unit tests for exploit verifiers."""

import asyncio
from unittest.mock import Mock

import pytest

from secbrain.agents.verifiers import NaiveVerifier, ReflectedXSSVerifier, SQLiErrorVerifier
from secbrain.core.verification import VerificationMethod


@pytest.fixture
def mock_response():
    """Factory for mock SecBrainHTTPClient HTTPResponse-like objects."""

    def _make_response(
        status_code: int = 200,
        body: str = "Hello World",
        headers: dict | None = None,
        url: str = "https://example.com/test",
        method: str = "GET",
    ):
        response = Mock()
        response.status_code = status_code
        response.body = body.encode("utf-8")
        response.text = body
        response.headers = headers or {
            "content-type": "text/html",
            "server": "Apache/2.4.1",
        }
        response.url = url
        response.method = method
        return response

    return _make_response


def test_reflected_xss_verifier_with_reflection(mock_response):
    baseline = mock_response(body="Welcome to our site")
    test = mock_response(body="Welcome<script>alert(1)</script>")

    verifier = ReflectedXSSVerifier()
    result = asyncio.run(
        verifier.verify(
            target_url="https://example.com/search",
            parameter_name="q",
            payload="<script>alert(1)</script>",
            baseline_response=baseline,
            test_response=test,
            trace_id="test-123",
        )
    )

    assert result.verified is True
    assert result.confidence_score == 0.85
    assert result.evidence is not None
    assert result.evidence.verification_method == VerificationMethod.REFLECTION


def test_reflected_xss_verifier_without_reflection(mock_response):
    baseline = mock_response(body="Welcome to our site")
    test = mock_response(body="Welcome to our site")

    verifier = ReflectedXSSVerifier()
    result = asyncio.run(
        verifier.verify(
            target_url="https://example.com/search",
            parameter_name="q",
            payload="<script>alert(1)</script>",
            baseline_response=baseline,
            test_response=test,
            trace_id="test-123",
        )
    )

    assert result.verified is False
    assert result.confidence_score == 0.0


def test_sqli_verifier_with_error(mock_response):
    baseline = mock_response(body="User: alice", status_code=200)
    test = mock_response(body="You have an error in your SQL syntax", status_code=200)

    verifier = SQLiErrorVerifier()
    result = asyncio.run(
        verifier.verify(
            target_url="https://example.com/api/user?id=1",
            parameter_name="id",
            payload="1' OR '1'='1",
            baseline_response=baseline,
            test_response=test,
            trace_id="test-456",
        )
    )

    assert result.verified is True
    assert result.confidence_score == 0.8
    assert result.evidence is not None


def test_sqli_verifier_with_500_error(mock_response):
    baseline = mock_response(body="User: alice", status_code=200)
    test = mock_response(body="Internal Server Error", status_code=500)

    verifier = SQLiErrorVerifier()
    result = asyncio.run(
        verifier.verify(
            target_url="https://example.com/api/user?id=1",
            parameter_name="id",
            payload="1' OR '1'='1",
            baseline_response=baseline,
            test_response=test,
            trace_id="test-456",
        )
    )

    assert result.verified is True
    assert result.confidence_score == 0.5


def test_naive_verifier(mock_response):
    baseline = mock_response()
    test = mock_response(body="Different response")

    verifier = NaiveVerifier()
    result = asyncio.run(
        verifier.verify(
            target_url="https://example.com",
            parameter_name="param",
            payload="test_payload",
            baseline_response=baseline,
            test_response=test,
            trace_id="test-789",
        )
    )

    assert result.verified is False
    assert result.confidence_score == 0.0
