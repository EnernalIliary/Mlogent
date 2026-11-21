"""Locate optional sibling projects used by the source checkout."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def project_dir(name: str) -> Path:
    """Prefer an in-checkout dependency, then the documented sibling path."""
    for candidate in (ROOT / name, ROOT.parent / name):
        if candidate.is_dir():
            return candidate
    return ROOT / name
