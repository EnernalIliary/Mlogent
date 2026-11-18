#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_game_aliases.py — 用官方的中文 bundle 覆盖 data/game/aliases.json。

`data/game/*.json` 是从 v160.7 执行器导出的英文内容表；`aliases.json` 是给人看的中文名。
它一度是手写的，于是出现了「flare = 耀斑」「toxopid = 毒蛛」这类与游戏内不一致的译名。
母本只有一个：`assets/bundles/bundle_zh_CN.properties`（与 `gen_name_docs.py` 同源）。

规则:
    第一个别名恒等于官方中文名（`<kind>.<id>.name`，去掉 `[color]` 标记）；
    排在后面的旧别名只在「不与任何 id 的官方名撞车」时保留——它们只是搜索用的口语写法
    （`铜矿`、`硅厂`），显示时永远用第一个。

用法:
    python knowledge/tools/gen_game_aliases.py           # 重写 data/game/aliases.json
    python knowledge/tools/gen_game_aliases.py --check   # 只报告覆盖率与冲突，不写文件
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KB = HERE.parent
REPO = KB.parent

OUT = REPO / "data" / "game" / "aliases.json"
DATA = KB / "00-data"

KINDS = [
    ("items", "item", "items.json"),
    ("liquids", "liquid", "liquids.json"),
    ("units", "unit", "units.json"),
    ("blocks", "block", "blocks.json"),
]

KV_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*=\s*(.*)$")
TAG_RE = re.compile(r"\[[a-zA-Z#][a-zA-Z0-9#_]{0,15}\]")


def _asset_root() -> Path:
    """素材目录（游戏素材已拆出仓库，与 gen_name_docs.py 的查找顺序一致）。"""
    cands = [os.environ.get("MLOG_ASSETS"),
             REPO / "assetsraw",
             REPO.parent / "TextureMDT",
             REPO.parent / "Mindustry_assetsraw",
             REPO.parent / "assetsraw"]
    for c in cands:
        if c and (Path(c) / "assets" / "bundles").is_dir():
            return Path(c)
    return REPO / "assetsraw"


def clean(text: str) -> str:
    return TAG_RE.sub("", text).strip()


def load_bundle(path: Path) -> dict:
    out = {}
    if not path.is_file():
        return out
    for raw in path.open(encoding="utf-8-sig", errors="replace"):
        m = KV_RE.match(raw.rstrip("\r\n"))
        if m:
            out[m.group(1)] = clean(m.group(2))
    return out


def ids_of(name: str) -> list[str]:
    obj = json.loads((DATA / name).read_text(encoding="utf-8-sig"))
    if isinstance(obj, dict):
        for k in ("records", "items", "entries", "rows", "data"):
            if isinstance(obj.get(k), list):
                obj = obj[k]
                break
        else:
            obj = [v for v in obj.values() if isinstance(v, dict)]
    out = []
    for rec in obj:
        if not isinstance(rec, dict):
            continue
        ident = rec.get("id") or rec.get("name")
        if ident and ident not in out:
            out.append(ident)
    return out


def main(argv: list[str]) -> int:
    check = "--check" in argv
    zh = load_bundle(_asset_root() / "assets/bundles/bundle_zh_CN.properties")
    if not zh:
        sys.exit("missing bundle_zh_CN.properties; set MLOG_ASSETS or put the assets next to the repo")

    old = {}
    if OUT.is_file():
        old = json.loads(OUT.read_text(encoding="utf-8-sig"))

    # 每个官方中文名归谁所有：用来挡住「把别人的官方名当自己的口语别名」
    owner = {}
    for kind, pref, fn in KINDS:
        for ident in ids_of(fn):
            name = zh.get("%s.%s.name" % (pref, ident))
            if name:
                owner.setdefault(name, set()).add("%s:%s" % (kind, ident))

    result = {}
    stats = {"official": 0, "no_official": 0, "extras_kept": 0, "extras_dropped": 0}
    for kind, pref, fn in KINDS:
        table = {}
        for ident in ids_of(fn):
            official = zh.get("%s.%s.name" % (pref, ident))
            mine = old.get(kind, {}).get(ident, [])
            if official:
                stats["official"] += 1
                names = [official]
            else:
                stats["no_official"] += 1
                names = []
            for alias in mine:
                if alias in names:
                    continue
                if alias in owner and ("%s:%s" % (kind, ident)) not in owner[alias]:
                    stats["extras_dropped"] += 1
                    continue
                names.append(alias)
                stats["extras_kept"] += 1
            if names:
                table[ident] = names
        if table:
            result[kind] = table

    report = ", ".join("%s %d" % (k, len(v)) for k, v in result.items())
    print("official %(official)d, no official name %(no_official)d, "
          "extras kept %(extras_kept)d, extras dropped %(extras_dropped)d" % stats)
    print("kinds: " + report)
    if check:
        return 0

    lines = ["{"]
    kinds = list(result)
    for ki, kind in enumerate(kinds):
        lines.append('  "%s": {' % kind)
        items = list(result[kind].items())
        for ii, (ident, names) in enumerate(items):
            arr = ", ".join(json.dumps(n, ensure_ascii=False) for n in names)
            comma = "," if ii < len(items) - 1 else ""
            lines.append('    %s: [%s]%s' % (json.dumps(ident, ensure_ascii=False), arr, comma))
        lines.append("  }" + ("," if ki < len(kinds) - 1 else ""))
    lines.append("}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("wrote %s (%d ids)" % (OUT.relative_to(REPO).as_posix(),
                                 sum(len(v) for v in result.values())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
