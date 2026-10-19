"""Hand-typo hunt over a schematic folder.

The A-layer answers "is this name undefined"; this answers "did you mean
something you already defined". A one-character misspelling of a real variable
is invisible to an undefined-name check (it is undefined too) but obvious here.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mindustry-blueprint" / "tools"))

import mlogcheck as C
import msch

SKIP = re.compile(r"^(@|_|null$|true$|false$|-?\d|\"|%)")
EMULATOR = ("mlogv32", "linux", "riscv", "risc-v", "vm")


def dist(a: str, b: str) -> int:
    if abs(len(a) - len(b)) > 2:
        return 99
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def blocks(path: Path):
    try:
        sch = msch.parse_file(path)
    except Exception:
        return
    for t in sch.logic_tiles():
        yield t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--out", type=Path, default=Path("out/mine_typos.md"))
    args = ap.parse_args()

    typo: list[tuple] = []
    full: list[tuple] = []
    files = 0
    for p in sorted(args.folder.rglob("*.msch")):
        if any(h in p.name.lower() for h in EMULATOR):
            continue
        files += 1
        for t in blocks(p):
            lines = t.logic.code.split("\n")
            stmts = [(i, c) for i, c in enumerate(lines) if c.strip()]
            defined, used = set(), Counter()
            for _i, c in stmts:
                defined |= set(C.defs_of(c))
                for v in C.uses_of(c):
                    if not SKIP.match(v):
                        used[v] += 1
            undefined = {v for v in used if v not in defined}
            for v in sorted(undefined):
                for w in defined:
                    if w == v:
                        continue
                    d = dist(v, w)
                    if d == 1 or (d == 2 and len(v) >= 6):
                        typo.append((p.name, t.block, t.x, t.y, v, w, used[v], d))
                        break
            for _i, c in stmts:
                for name in list(C.defs_of(c)) + C.uses_of(c):
                    if C._FULLWIDTH.search(name) if hasattr(C, "_FULLWIDTH") else False:
                        full.append((p.name, t.block, t.x, t.y, name))
    out = ["# 手误候选（我自己的蓝图库）", ""]
    out.append(f"扫描 {files} 份，命中 {len(typo)} 条疑似拼错、{len(full)} 条全角标点名。")
    out.append("")
    out.append("## 疑似拼错（用了一个不存在的名字，而它离某个已定义的名字只差一两个字符）")
    out.append("")
    out.append("| 文件 | 方块 | 用了 | 像 | 距离 | 出现 |")
    out.append("|---|---|---|---|---:|---:|")
    for f, b, x, y, v, w, n, d in sorted(typo, key=lambda r: (r[0], r[4])):
        out.append(f"| {f} | {b} @({x},{y}) | `{v}` | `{w}` | {d} | {n} |")
    if full:
        out.append("")
        out.append("## 全角标点当变量名")
        out.append("")
        for f, b, x, y, v in full[:40]:
            out.append(f"- {f} {b} @({x},{y}) `{v}`")
    args.out.write_text("\n".join(out) + "\n", "utf-8")
    print(f"files {files} typo {len(typo)} fullwidth {len(full)} -> {args.out}")
    for f, b, x, y, v, w, n, d in sorted(typo, key=lambda r: -r[6])[:20]:
        print(f"  {v!r} ~ {w!r}  x{n}  {f} {b}@({x},{y})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
