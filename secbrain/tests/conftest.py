from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root (the directory containing the `secbrain/` package) is on sys.path.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
