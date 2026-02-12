"""Tests for payload adaptation and mutation."""

from __future__ import annotations

from unittest.mock import Mock

from secbrain.core.payload_adaptation import PayloadMutator


class TestPayloadMutatorAdapt:
    """Test PayloadMutator.adapt() method."""

    def test_waf_keywords_trigger_bypass(self) -> None:
        """WAF keywords in response text produce bypass variants."""
        response = Mock(text="Request blocked by firewall", status_code=403)
        result = PayloadMutator.adapt("<script>alert(1)</script>", response)

        assert len(result) > 0
        # Should contain hex-encoded variants
        assert any("\\x3c" in v for v in result)

    def test_encoding_hints_trigger_bypass(self) -> None:
        """HTML-entity encoding hints produce encoding variants."""
        response = Mock(text="value is &lt;script&gt;", status_code=200)
        result = PayloadMutator.adapt("<script>", response)

        assert len(result) > 0
        assert any("&lt;" in v for v in result)

    def test_status_500_trigger_variants(self) -> None:
        """Server error (5xx) produces delimiter variants."""
        response = Mock(text="Internal Server Error", status_code=500)
        result = PayloadMutator.adapt("test", response)

        assert len(result) > 0
        assert any(v.endswith(";") for v in result)

    def test_status_504_trigger_timing(self) -> None:
        """Gateway timeout (504) produces timing-based variants."""
        response = Mock(text="Gateway Timeout", status_code=504)
        result = PayloadMutator.adapt("test", response)

        assert len(result) > 0
        assert any("SLEEP" in v for v in result)
        assert any("WAITFOR" in v for v in result)

    def test_no_match_returns_original(self) -> None:
        """When no signals match, the original payload is returned."""
        response = Mock(text="OK", status_code=200)
        result = PayloadMutator.adapt("benign", response)

        assert result == ["benign"]

    def test_deduplication(self) -> None:
        """Duplicate variants are removed while preserving order."""
        response = Mock(text="blocked by firewall", status_code=500)
        result = PayloadMutator.adapt("x", response)

        assert len(result) == len(set(result))

    def test_none_text_attribute(self) -> None:
        """Handles response with None text gracefully."""
        response = Mock(text=None, status_code=200)
        result = PayloadMutator.adapt("test", response)

        assert result == ["test"]

    def test_missing_text_attribute(self) -> None:
        """Handles response without text attribute gracefully."""
        response = Mock(spec=[])
        result = PayloadMutator.adapt("test", response)

        assert result == ["test"]


class TestPayloadMutatorWafBypass:
    """Test PayloadMutator._waf_bypass() static method."""

    def test_produces_multiple_variants(self) -> None:
        """WAF bypass produces several evasion variants."""
        result = PayloadMutator._waf_bypass("<script>alert(1)</script>")

        assert len(result) == 6

    def test_hex_encoding_variant(self) -> None:
        """Includes hex-encoded angle brackets."""
        result = PayloadMutator._waf_bypass("<b>")
        assert any("\\x3c" in v for v in result)

    def test_case_variation(self) -> None:
        """Includes mixed-case 'script' variants."""
        result = PayloadMutator._waf_bypass("<script>")
        assert any("scRipt" in v for v in result)
        assert any("Script" in v for v in result)

    def test_whitespace_replacement(self) -> None:
        """Includes comment-based and tab space replacement."""
        result = PayloadMutator._waf_bypass("a b")
        assert any("/**/" in v for v in result)


class TestPayloadMutatorEncodingBypass:
    """Test PayloadMutator._encoding_bypass() static method."""

    def test_produces_multiple_variants(self) -> None:
        """Encoding bypass produces several variants."""
        result = PayloadMutator._encoding_bypass("'test\"")

        assert len(result) == 8

    def test_entity_encoding(self) -> None:
        """Includes HTML entity encoded variants."""
        result = PayloadMutator._encoding_bypass("'")
        assert any("&#39;" in v for v in result)

    def test_url_encoding(self) -> None:
        """Includes URL-encoded space variants."""
        result = PayloadMutator._encoding_bypass("a b")
        assert any("%20" in v for v in result)
        assert any("%09" in v for v in result)
