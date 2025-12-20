from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from secbrain.core.verification import VerificationResult


@dataclass
class ConsensusResult:
    verified: bool
    confidence: float
    evidence: Any | None = None


class ConsensusEngine:
    """Simple consensus aggregator for verifier results."""

    def decide(self, results: Iterable[VerificationResult]) -> ConsensusResult:
        results = list(results)
        if not results:
            return ConsensusResult(verified=False, confidence=0.0, evidence=None)

        verified = any(r.verified for r in results)
        avg_conf = sum((r.confidence_score or 0.0) for r in results) / len(results)

        # Pick the highest-confidence evidence if available
        evidence = None
        top = max(results, key=lambda r: r.confidence_score or 0.0)
        if top and top.evidence:
            evidence = top.evidence.to_dict() if hasattr(top.evidence, "to_dict") else top.evidence

        return ConsensusResult(verified=verified, confidence=avg_conf, evidence=evidence)
