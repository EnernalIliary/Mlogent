"""For every label value, which blocks/tokens actually characterise it?

`lift` = P(block | label) - P(block | no label), so a value that is really about
`cyclone` shows cyclone with a huge lift and everything else near zero.

Usage: python tools/label_lift.py [--top 8]
"""
from __future__ import annotations

import collections
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "mindustry-blueprint" / "tools"))
import msch  # noqa: E402
import mlogir  # noqa: E402

MARK = re.compile(r"\[([^\]]*)\]")
PUA = "".join(chr(c) for c in range(0xE000, 0xF900))


def split_label(label: str) -> tuple[str, str, str]:
    m = MARK.search(label)
    colour = m.group(1) if m else ""
    body = MARK.sub("", label)
    text = "".join(ch for ch in body if ch not in PUA).strip()
    return colour, text or label, label


def main() -> None:
    top_n = 8
    if "--top" in sys.argv:
        top_n = int(sys.argv[sys.argv.index("--top") + 1])

    corpus = pathlib.Path.home() / "AppData" / "Roaming" / "Mindustry" / "schematics"
    files = sorted(corpus.glob("*.msch"))

    per_file: list[tuple[set[str], collections.Counter[str], set[str]]] = []
    for p in files:
        try:
            sch = msch.parse_file(str(p))
        except Exception:
            continue
        texts = {split_label(l)[1] for l in (sch.labels or [])}
        blocks = collections.Counter(t.block for t in sch.tiles)
        # logic tokens: mnemonics + every string literal + @vars
        toks: set[str] = set()
        for t in sch.logic_tiles():
            for line in t.logic.code.split("\n"):
                body = mlogir.strip_comment(line).strip()
                if not body:
                    continue
                toks.add(body.split()[0].lower())
                toks.update(w.lower() for w in body.split()[1:] if w.startswith("@"))
                toks.update(s for s in re.findall(r'"([^"]*)"', body) if len(s) <= 20)
        per_file.append((texts, blocks, toks))

    n = len(per_file)
    # baseline frequencies
    base_b: collections.Counter[str] = collections.Counter()
    base_t: collections.Counter[str] = collections.Counter()
    for _, b, t in per_file:
        base_b.update(b.keys())
        base_t.update(t)

    values = sorted({v for texts, _, _ in per_file for v in texts})
    out = [f"# 标签 -> 内容 的判别特征(lift)\n", f"语料 {n} 份\n"]
    for v in values:
        sel = [(b, t) for texts, b, t in per_file if v in texts]
        if len(sel) < 3:
            continue
        cb: collections.Counter[str] = collections.Counter()
        ct: collections.Counter[str] = collections.Counter()
        for b, t in sel:
            cb.update(b.keys())
            ct.update(t)
        lift_b = {k: cb[k] / len(sel) - base_b[k] / n for k in cb}
        lift_t = {k: ct[k] / len(sel) - base_t[k] / n for k in ct}
        best_b = [f"{k}({lift_b[k]:+.2f}/{cb[k]}/{len(sel)})"
                  for k in sorted(lift_b, key=lift_b.get, reverse=True)[:top_n] if lift_b[k] > 0.15]
        best_t = [f"{k}({lift_t[k]:+.2f})"
                  for k in sorted(lift_t, key=lift_t.get, reverse=True)[:top_n] if lift_t[k] > 0.15]
        out.append(f"## {v}  ({len(sel)} 份)")
        out.append(f"- 方块: {'、'.join(best_b) or '(无显著)'}")
        out.append(f"- 逻辑: {'、'.join(best_t) or '(无显著)'}")
        out.append("")

    path = ROOT / "out" / "label_lift.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
