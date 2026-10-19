"""Sync the authoritative blueprint copies out to tools/ and the two skill dirs.

Authoritative copy = `mindustry-blueprint/tools/`. Everything else is a mirror.
The file list is **globbed** rather than hand-listed: a hand-written list silently
skips new modules (that is how `mlogcross.py` and `mlogsearch.py` fell out of sync
once already).
"""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "mindustry-blueprint"
TOOLS = ROOT / "tools"
SKILL_BP = ROOT / ".dsh" / "skills" / "mindustry-blueprint"

# private helpers (`_patch_*.py`, `_sweep_*.py`) stay in the repo; caches never ship
PY = sorted(p.name for p in (BP / "tools").glob("*.py") if not p.name.startswith("_"))
DATA = sorted(p.name for p in (BP / "tools").glob("*.json") if not p.name.startswith("."))
DOCS = ["SKILL.md", "BUILDS.md", "REFERENCE.md", "PATTERNS.md",
        "BLUEPRINT-ANALYSIS.md", "README.md"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def put(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


print(f"py   : {len(PY)} file(s) -> {', '.join(PY)}")
print(f"data : {len(DATA)} file(s)")
for name in PY + DATA:
    put(BP / "tools" / name, TOOLS / name)
    put(BP / "tools" / name, SKILL_BP / "tools" / name)

for name in DOCS:
    src = BP / name
    if not src.exists():
        print("skip (missing)", name)
        continue
    put(src, SKILL_BP / name)

print("=== hashes (blueprint / root / skill)")
bad = 0
for name in PY + DATA:
    a, b, c = BP / "tools" / name, TOOLS / name, SKILL_BP / "tools" / name
    ok = sha(a) == sha(b) == sha(c)
    bad += 0 if ok else 1
    print(f"  {name:<24} {sha(a)} {'OK' if ok else 'MISMATCH'}")
print("all in sync" if not bad else f"!! {bad} mismatch(es)")
