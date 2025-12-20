"""Contract fixture utilities used in tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_fixtures_from_file(path: str | Path) -> list[dict[str, Any]]:
    """Load contract fixtures from a JSON file path. Returns empty list on error."""
    try:
        data = json.loads(Path(path).read_text())
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict)]
    except Exception:
        return []
    return []
