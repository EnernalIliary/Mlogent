"""Reverse-engineer the schematic label taxonomy.

Labels look like `[color]<private-use glyph>text`. The glyph is the category
icon, the colour is the category colour, the text is the category name. Some
blueprints carry several labels, which is how a single blueprint ends up in
more than one bucket.

Usage:  python tools/label_map.py [--samples N]
"""
from __future__ import annotations

import collections
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "mindustry-blueprint" / "tools"))
import msch  # noqa: E402

import re

MARK = re.compile(r"\[([^\]]*)\]")
PUA = "".join(chr(c) for c in range(0xE000, 0xF900))


def split_label(label: str) -> tuple[str, str, str]:
    """-> (colour, icon, text)."""
    m = MARK.search(label)
    colour = m.group(1) if m else ""
    body = MARK.sub("", label)
    icon = "".join(ch for ch in body if ch in PUA)
    text = "".join(ch for ch in body if ch not in PUA).strip()
    return colour, icon, text


def main() -> None:
    n_samples = 2
    if "--samples" in sys.argv:
        n_samples = int(sys.argv[sys.argv.index("--samples") + 1])

    corpus = pathlib.Path.home() / "AppData" / "Roaming" / "Mindustry" / "schematics"
    files = sorted(corpus.glob("*.msch"))
    if not files:
        raise SystemExit(f"no schematics under {corpus}")

    count: collections.Counter[str] = collections.Counter()
    icon_of: dict[str, str] = {}
    colour_of: dict[str, str] = {}
    samples: dict[str, list[str]] = collections.defaultdict(list)
    per_file: dict[str, list[str]] = {}
    n_label = collections.Counter()
    bad = 0

    for p in files:
        try:
            sch = msch.parse_file(str(p))
        except Exception:
            bad += 1
            continue
        labs = [l for l in (sch.labels or []) if l.strip()]
        per_file[p.name] = labs
        n_label[len(labs)] += 1
        for l in labs:
            colour, icon, text = split_label(l)
            count[text or l] += 1
            icon_of.setdefault(text or l, icon)
            colour_of.setdefault(text or l, colour)
            if len(samples[text or l]) < n_samples:
                samples[text or l].append(p.name)

    print(f"# 标签体系\n")
    print(f"文件 {len(files)-bad} 份(解析失败 {bad})，"
          f"不同标签 {len(count)} 个，无标签 {n_label[0]} 份\n")
    print("## 每份蓝图的标签数量\n")
    for k in sorted(n_label):
        print(f"- {k} 个标签: {n_label[k]} 份")
    print()

    # group by icon glyph -- the icon is the dimension
    by_icon: dict[str, list[str]] = collections.defaultdict(list)
    for text in count:
        by_icon[icon_of[text]].append(text)

    print("## 按图标(维度)分组\n")
    print("| 图标 | 色 | 维度内标签(次数) |")
    print("|---|---|---|")
    for icon, texts in sorted(by_icon.items(), key=lambda kv: -sum(count[t] for t in kv[1])):
        glyph = " ".join(f"U+{ord(c):04X}" for c in icon) or "(无)"
        colours = {colour_of[t] for t in texts}
        cells = "、".join(f"{t}({count[t]})" for t in sorted(texts, key=lambda t: -count[t]))
        print(f"| {glyph} | {'/'.join(sorted(colours))} | {cells} |")
    print()

    print("## 全部标签\n")
    print("| 次数 | 色 | 图标 | 标签 | 例子 |")
    print("|---|---|---|---|---|")
    for text, n in count.most_common():
        icon = " ".join(f"U+{ord(c):04X}" for c in icon_of[text]) or "-"
        ex = "、".join(samples[text][:n_samples])
        print(f"| {n} | {colour_of[text] or '-'} | {icon} | {text} | {ex} |")
    print()

    print("## 组合(前 20)\n")
    combos: collections.Counter[tuple[str, ...]] = collections.Counter()
    for name, labs in per_file.items():
        key = tuple(sorted(split_label(l)[2] or l for l in labs))
        combos[key] += 1
    print("| 份数 | 标签组合 |")
    print("|---|---|")
    for combo, n in combos.most_common(20):
        print(f"| {n} | {' + '.join(combo) if combo else '(无)'} |")


if __name__ == "__main__":
    main()
