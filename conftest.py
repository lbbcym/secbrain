import sys
from pathlib import Path

# Ensure the secbrain package is importable when running pytest from repo root.
ROOT = Path(__file__).resolve().parent
SEC_BRAIN = ROOT / "secbrain"
if SEC_BRAIN.exists():
    sys.path.insert(0, str(SEC_BRAIN))
