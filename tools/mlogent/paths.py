"""Locations shared by repo checkouts and relocated standalone skills.

Resolve from this installed package, never from the process working directory.
"""
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = TOOLS_ROOT.parent
