"""Second pass: show context for typo candidates that are NOT link-shaped names."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mindustry-blueprint" / "tools"))

import mlogcheck as C
import msch
from typo_hunt import dist

LINKISH = re.compile(r"^[a-z][a-z-]*\d+$")          # message1, conveyor2, unloader24
SKIP = re.compile(r"^(@|_|null$|true$|false$|-?\d|\"|%)")


def main() -> int:
    root = Path(sys.argv[1])
    rows = []
    for p in sorted(root.rglob("*.msch")):
        if any(h in p.name.lower() for h in ("mlogv32", "linux", "riscv", "risc-v")):
            continue
        try:
            sch = msch.parse_file(p)
        except Exception:
            continue
        for t in sch.logic_tiles():
            lines = t.logic.code.split("\n")
            # `#` starts a comment (LParser.java:98-99); the raw line must be
            # cleaned the same way the checker cleans it, or the words inside a
            # comment get counted as variable reads.
            stmts = []
            for i, raw in enumerate(lines):
                c = C.strip_comment(raw).strip()
                if c:
                    stmts.append((i, c))
            defined: dict[str, int] = {}
            used: dict[str, list[int]] = {}
            for i, c in stmts:
                for v in C.defs_of(c):
                    defined.setdefault(v, i + 1)
                for v in C.uses_of(c):
                    if not SKIP.match(v):
                        used.setdefault(v, []).append(i + 1)
            for v, at in used.items():
                if v in defined or LINKISH.match(v):
                    continue
                best = None
                for w in defined:
                    if w == v or LINKISH.match(w):
                        continue
                    d = dist(v, w)
                    if d == 1 or (d == 2 and len(v) >= 6):
                        if best is None or d < best[1]:
                            best = (w, d)
                if best:
                    rows.append((len(at), p.name, t.block, t.x, t.y, v, best[0], best[1],
                                 at[:3], lines[at[0] - 1].strip()[:70],
                                 lines[defined[best[0]] - 1].strip()[:70]))
    rows.sort(reverse=True)
    print(f"non-link typo candidates: {len(rows)}")
    for n, f, b, x, y, v, w, d, at, code, wcode in rows[:28]:
        print(f"\n{n:>3}x `{v}` ~ `{w}` (d={d})  {f} {b}@({x},{y}) L{at}")
        print(f"     seen: {code}")
        print(f"     def : {wcode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
