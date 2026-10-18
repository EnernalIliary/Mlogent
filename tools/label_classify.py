"""Classify the schematic library along the label facets, and check a few
labels against what the logic actually does.

The label system is faceted: the colour names the dimension, the private-use
glyph names the value, the trailing text is the value spelled out.
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

# colour -> dimension name (read off the label colours above)
DIM = {
    "sky": "数量",
    "#6335f8": "系列",
    "purple": "用途",
    "gray": "功能/地形",
    "olive": "超频规模",
    "slate": "阶段",
    "gold": "大类",
    "green": "发电方式",
    "blue": "单位/武器",
    "orange": "工厂产出",
    "red": "厂等",
    "highlight": "特殊类型",
    "lightgray": "品质",
    "yellow": "品质",
    "black": "内容",
}


def split_label(label: str) -> tuple[str, str]:
    m = MARK.search(label)
    colour = m.group(1) if m else ""
    body = MARK.sub("", label)
    text = "".join(ch for ch in body if ch not in PUA).strip()
    return colour, text or label


def main() -> None:
    corpus = pathlib.Path.home() / "AppData" / "Roaming" / "Mindustry" / "schematics"
    files = sorted(corpus.glob("*.msch"))

    per_file: dict[str, dict[str, list[str]]] = {}
    facet_count: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    opcodes_by_label: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    strings_by_label: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    content_by_label: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)

    for p in files:
        try:
            sch = msch.parse_file(str(p))
        except Exception:
            continue
        facets: dict[str, list[str]] = collections.defaultdict(list)
        for l in sch.labels or []:
            colour, text = split_label(l)
            dim = DIM.get(colour, colour or "?")
            facets[dim].append(text)
            facet_count[dim][text] += 1
        per_file[p.name] = facets

        ops: collections.Counter[str] = collections.Counter()
        strs: collections.Counter[str] = collections.Counter()
        for t in sch.logic_tiles():
            for line in t.logic.code.split("\n"):
                body = mlogir.strip_comment(line).strip()
                if not body:
                    continue
                ops[body.split()[0].lower()] += 1
                for s in re.findall(r'"([^"]*)"', body):
                    if len(s) <= 24:
                        strs[s] += 1
        blocks = collections.Counter(t.block for t in sch.tiles)
        for text in [v for vals in facets.values() for v in vals]:
            opcodes_by_label[text].update(ops)
            strings_by_label[text].update(strs)
            content_by_label[text].update(blocks)

    out: list[str] = []
    out.append("# 蓝图标签体系与归类\n")

    out.append("## 维度(色=维度)\n")
    out.append("| 维度 | 标签数 | 覆盖文件 | 值(次数) |")
    out.append("|---|---|---|---|")
    seen: set[str] = set()
    for dim in DIM.values():
        if dim in seen:
            continue
        seen.add(dim)
        c = facet_count.get(dim)
        if not c:
            continue
        files_n = sum(1 for f in per_file.values() if dim in f)
        vals = "、".join(f"{k}({v})" for k, v in c.most_common())
        out.append(f"| {dim} | {len(c)} | {files_n} | {vals} |")
    out.append("")

    # files with the most facets
    out.append("## 每份文件的维度数(前 10)\n")
    ranked = sorted(per_file.items(), key=lambda kv: -len(kv[1]))
    for name, f in ranked[:10]:
        desc = "; ".join(f"{d}={'/'.join(v)}" for d, v in f.items())
        out.append(f"- `{name}` —— {len(f)} 维:{desc}")
    out.append("")

    # co-occurrence between dimensions
    out.append("## 维度共现(同时带上这两个标签的文件数,前 12 对)\n")
    pairs: collections.Counter[tuple[str, str]] = collections.Counter()
    for f in per_file.values():
        dims = [d for d in f if d not in ("系列", "数量", "品质")]
        for i in range(len(dims)):
            for j in range(i + 1, len(dims)):
                a, b = sorted((dims[i], dims[j]))
                pairs[(a, b)] += 1
    out.append("| 文件数 | 维度对 |")
    out.append("|---|---|")
    for (a, b), n in pairs.most_common(12):
        out.append(f"| {n} | {a} + {b} |")
    out.append("")

    # label vs content spot-checks
    out.append("## 标签与内容的一致性抽检\n")
    checks = ["显示", "无线", "钍反", "质驱", "冲反", "温差", "t5厂", "自冷", "抽水"]
    out.append("| 标签 | 文件数 | 最常见方块 | 最常见 opcode | 看起来对不对 |")
    out.append("|---|---|---|---|---|")
    verdict = {
        "显示": "应该大量 `draw` ⇒ 核对 draw 占比",
        "无线": "应该 `ulocate`+`ucontrol`+`itemDrop`(无线超)",
        "钍反": "应该 `@heat` / thorium-reactor",
        "质驱": "应该 `mass-driver` + `control shoot`",
        "冲反": "应该 `ucontrol` / `radar`(反打)",
        "温差": "应该 `differential-generator` / `@heat`",
        "t5厂": "应该 `tetrative-reconstructor`",
        "自冷": "应该液体传感器 / `@liquid`",
        "抽水": "应该 `@liquid` / 抽水机",
    }
    for label in checks:
        blocks = content_by_label.get(label)
        ops = opcodes_by_label.get(label)
        if not blocks:
            continue
        n = sum(1 for f in per_file.values()
                for vals in f.values() if label in vals)
        top_blocks = "、".join(f"{k}({v})" for k, v in blocks.most_common(3))
        top_ops = "、".join(f"{k}({v})" for k, v in ops.most_common(4))
        out.append(f"| {label} | {n} | {top_blocks} | {top_ops} | {verdict.get(label, '')} |")
    out.append("")

    # gaps
    out.append("## 缺口\n")
    unlabelled = [n for n, f in per_file.items() if not f]
    out.append(f"- 无任何标签:{len(unlabelled)} 份")
    for n in unlabelled[:12]:
        out.append(f"  - `{n}`")
    weak = [n for n, f in per_file.items() if any(v == ["未分类或低效"] for v in f.values())]
    out.append(f"- 标了「未分类或低效」:{len(weak)} 份")
    only_series = [n for n, f in per_file.items() if set(f) <= {"系列"}]
    out.append(f"- 只有系列标(ILI)没有任何分类:{len(only_series)} 份")
    numbers = [n for n, f in per_file.items() if "数量" in f]
    out.append(f"- 带数量标:{len(numbers)} 份(占 {len(numbers)*100//max(1,len(per_file))}%)")

    path = ROOT / "out" / "label_report.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {path} ({len(out)} lines)")


if __name__ == "__main__":
    main()
