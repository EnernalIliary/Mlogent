"""Sync the authoritative blueprint copies out to tools/ and the two skill dirs."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

ROOT = Path("F:/OneDrive/桌面/AtomicStates")
BP = ROOT / "mindustry-blueprint"
TOOLS = ROOT / "tools"
SKILL_BP = ROOT / ".dsh/skills/mindustry-blueprint"
SKILL_AG = ROOT / ".dsh/skills/mlogagent"

PY = ["mlog.py", "mlogir.py", "mlogcheck.py", "mlogval.py", "mlogpack.py",
      "msch.py", "mschgen.py", "mlogagent.py"]
DATA = ["instr_semantics.json", "item_ids.json", "block_ids.json",
        "block_sizes.json", "cmd_index.json", "unit_attrs.json",
        "block_attrs.json"]
DOCS = ["SKILL.md", "BUILDS.md", "REFERENCE.md", "PATTERNS.md",
        "BLUEPRINT-ANALYSIS.md", "README.md"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def put(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


for name in PY + DATA:
    src = BP / "tools" / name
    if not src.exists():
        print("skip (missing)", name)
        continue
    put(src, TOOLS / name)
    put(src, SKILL_BP / "tools" / name)

for name in DOCS:
    src = BP / name
    if not src.exists():
        continue
    put(src, SKILL_BP / name)

print("=== hashes (blueprint / root / skill)")
for name in PY[:5]:
    a = BP / "tools" / name
    b = TOOLS / name
    c = SKILL_BP / "tools" / name
    print(f"  {name:<14} {sha(a)} {sha(b)} {sha(c)} {'OK' if sha(a)==sha(b)==sha(c) else 'MISMATCH'}")
print("  instr_semantics", sha(BP / "tools/instr_semantics.json"),
      sha(TOOLS / "instr_semantics.json"),
      sha(SKILL_BP / "tools/instr_semantics.json"))
