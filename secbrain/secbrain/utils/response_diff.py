"""Reusable response diff primitives for authz/logic verification."""

from __future__ import annotations

import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any


def diff_status(baseline: int, test: int) -> dict[str, Any]:
    return {"changed": baseline != test, "baseline": baseline, "test": test}


def _normalize_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {k.lower(): v for k, v in headers.items()}


def diff_headers(baseline: Mapping[str, str], test: Mapping[str, str]) -> dict[str, Any]:
    b = _normalize_headers(baseline)
    t = _normalize_headers(test)
    added = {k: v for k, v in t.items() if k not in b}
    removed = {k: v for k, v in b.items() if k not in t}
    changed = {k: {"baseline": b[k], "test": t[k]} for k in b.keys() & t.keys() if b[k] != t[k]}
    return {"added": added, "removed": removed, "changed": changed, "has_diff": bool(added or removed or changed)}


def _entropy(data: str) -> float:
    if not data:
        return 0.0
    freq = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in freq.values())


def diff_body_size_entropy(baseline: str, test: str) -> dict[str, Any]:
    return {
        "size": {"baseline": len(baseline), "test": len(test), "delta": len(test) - len(baseline)},
        "entropy": {"baseline": _entropy(baseline), "test": _entropy(test)},
    }


def diff_keywords(baseline: str, test: str, keywords: Sequence[str]) -> dict[str, Any]:
    result = {}
    for kw in keywords:
        b_has = kw in baseline
        t_has = kw in test
        if b_has != t_has:
            result[kw] = {"baseline": b_has, "test": t_has}
    return {"changed": bool(result), "keywords": result}


def diff_json_semantic(baseline_body: str, test_body: str) -> dict[str, Any]:
    try:
        b_json = json.loads(baseline_body) if baseline_body else {}
        t_json = json.loads(test_body) if test_body else {}
    except json.JSONDecodeError:
        return {"changed": False, "error": "non-json"}

    return {
        "changed": b_json != t_json,
        "added_keys": sorted(set(t_json.keys()) - set(b_json.keys())) if isinstance(t_json, dict) else [],
        "removed_keys": sorted(set(b_json.keys()) - set(t_json.keys())) if isinstance(b_json, dict) else [],
    }
