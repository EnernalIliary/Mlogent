"""Fingerprint every distinct logic program found in the save folder.

Programs inside saves have no name (mlog has no name field; only blueprints do),
so purpose has to be inferred from three cheap signals:

  * which blocks it links to   (reactor1 / dome1 / sorters  -- the names carry meaning)
  * its instruction histogram  (draw = display, ubind = units, control config = logistics)
  * the few string literals it contains

Output: out/saves_programs.md (readable index) and out/saves_programs.json.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "mindustry-blueprint" / "tools"))
import map_logic  # noqa: E402

SAVES = Path.home() / "AppData/Roaming/Mindustry/saves"
STR = re.compile(r'"((?:[^"\\]|\\.)*)"')
CJK = re.compile(r"[\u4e00-\u9fff]")
TRAILING_DIGITS = re.compile(r"\d+$")

# families, checked in this order: the first match wins, so the most specific
# structural evidence has to come first.
FAMILIES = [
    # generated art: almost every statement is a draw command
    ("像素画(逐格 draw)",
     lambda f: f["stmts"] >= 50 and f["draw_n"] >= 0.5 * f["stmts"]),
    ("显示/UI", lambda f: f["draw_n"] >= 3 or (f["links"].get("display") and f["draw_n"])),
    ("单位", lambda f: f["ubind"] or f["ucontrol"] or f["radar"] or f["ulocate"]),
    ("规则/世界", lambda f: f["setrule"] or f["spawn"] or f["effect"] or f["cutscene"]),
    ("物流", lambda f: f["control"] or f["itemdrop"] or f["itemtake"]
     or any(k in f["links"] for k in ("sorter", "unloader", "conveyor", "junction", "router"))),
    ("通信", lambda f: f["message"] or f["messagewrite"] or f["messageread"]),
    ("计算/内存", lambda f: f["cell"] or f["bank"] or f["op"] >= 8),
]


def code_hash(code: str) -> str:
    norm = "\n".join(line.rstrip() for line in code.replace("\r\n", "\n").split("\n"))
    return hashlib.sha1(norm.strip("\n").encode("utf-8")).hexdigest()


def fingerprint(code: str, links: list[dict]) -> dict:
    lines = [ln.strip() for ln in code.splitlines() if ln.strip()]
    ops = Counter(ln.split()[0].lower() for ln in lines)
    kinds = Counter(TRAILING_DIGITS.sub("", l["name"].lower()) for l in links)
    strings = [s for ln in lines for s in STR.findall(ln)]
    text = ""
    for s in strings:
        if len(s) > len(text) and not s.startswith("#"):
            text = s
    cjk_lines = sum(1 for ln in lines if CJK.search(ln))
    return {
        "stmts": len(lines),
        "ops": ops,
        "links": kinds,
        "strings": strings,
        "text": text,
        "cjk_pct": round(100.0 * cjk_lines / max(1, len(lines)), 1),
        "draw": bool(ops.get("draw")),
        "draw_n": ops.get("draw", 0),
        "getblock": bool(ops.get("getblock") or ops.get("setblock")),
        "ubind": bool(ops.get("ubind")),
        "ucontrol": bool(ops.get("ucontrol")),
        "radar": bool(ops.get("radar") or ops.get("uradar")),
        "ulocate": bool(ops.get("ulocate")),
        "setrule": bool(ops.get("setrule") or ops.get("setrules")),
        "spawn": bool(ops.get("spawn") or ops.get("bullet")),
        "effect": bool(ops.get("effect") or ops.get("explosion")),
        "cutscene": bool(ops.get("cutscene")),
        "control": bool(ops.get("control")),
        "itemdrop": bool(ops.get("itemdrop") or ops.get("itemtake")),
        "message": "message" in kinds or bool(ops.get("printflush")),
        "messagewrite": bool(ops.get("writemessage")),
        "messageread": bool(ops.get("readmessage") or ops.get("fetchmessage")),
        "cell": "cell" in kinds or "memory" in kinds,
        "bank": "bank" in kinds,
        "op": ops.get("op", 0),
    }


def family_of(f: dict) -> str:
    for name, test in FAMILIES:
        try:
            if test(f):
                return name
        except Exception:
            continue
    return "其他"


def short(counter: Counter, n: int = 5) -> str:
    return ", ".join(f"{k}×{v}" for k, v in counter.most_common(n))


def main() -> int:
    files = sorted(SAVES.glob("*.msav"))
    seen: dict[str, dict] = {}
    order: list[str] = []
    failed = 0
    for k, path in enumerate(files, 1):
        try:
            info = map_logic.read_save(path)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  !! {path.name}: {type(exc).__name__}: {exc}")
            continue
        for tile in info["logic"]:
            h = code_hash(tile["code"])
            if h in seen:
                seen[h]["copies"] += 1
                continue
            fp = fingerprint(tile["code"], tile["links"])
            seen[h] = {
                "hash": h,
                "save": path.name,
                "x": tile["x"],
                "y": tile["y"],
                "block": tile["block"],
                "copies": 1,
                "stmts": fp["stmts"],
                "cjk_pct": fp["cjk_pct"],
                "text": fp["text"],
                "links": short(fp["links"]),
                "ops": short(fp["ops"]),
                "family": family_of(fp),
                "op_count": fp["op"],
                "opens": next((ln.strip() for ln in tile["code"].splitlines() if ln.strip()), ""),
                "link_n": len(tile["links"]),
            }
            order.append(h)
        if k % 100 == 0:
            print(f"  {k}/{len(files)} saves, distinct={len(seen)}", flush=True)

    programs = [seen[h] for h in order]
    by_family: dict[str, list[dict]] = defaultdict(list)
    for p in programs:
        by_family[p["family"]].append(p)
    for group in by_family.values():
        group.sort(key=lambda p: -p["copies"])

    out = HERE / "out"
    out.mkdir(exist_ok=True)
    (out / "saves_programs.json").write_text(
        json.dumps({"saves": len(files), "failed": failed, "distinct": len(programs),
                    "families": {k: len(v) for k, v in by_family.items()},
                    "programs": programs}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    lines = []
    total_stmts = sum(p["stmts"] for p in programs)
    lines.append("# 存档里的逻辑程序：按「像什么」分桶\n")
    lines.append(f"{len(files)} 个存档（{failed} 个读不了），**{len(programs)} 份不同的程序**，"
                 f"合计 {total_stmts:,} 条语句。\n")
    lines.append("存档里的处理器**没有名字**（mlog 没有名字字段，只有蓝图有）。下面每一桶的用途是"
                 "从三个信号推的：链接的方块类型、指令直方图、代码里唯一的几段字符串。"
                 "**这是猜测，不是标签**——每行都把证据写在右边，方便你一眼否掉。\n")
    lines.append("| 桶 | 程序数 | 语句数 | 副本数 |\n| --- | ---: | ---: | ---: |")
    for fam, group in sorted(by_family.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"| {fam} | {len(group)} | {sum(p['stmts'] for p in group):,} "
                     f"| {sum(p['copies'] for p in group):,} |")
    lines.append("")
    for fam, group in sorted(by_family.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"\n## {fam} — {len(group)} 份\n")
        lines.append("| 副本 | 语句 | 位置 | 链接 | 主要指令 | 代码里的字 |\n| ---: | ---: | --- | --- | --- | --- |")
        for p in group[:20]:
            text = p["text"].replace("|", "\\|")[:28] or "—"
            lines.append(f"| {p['copies']:,} | {p['stmts']} | `{p['save']}` ({p['x']},{p['y']}) "
                         f"| {p['links'] or '—'} | {p['ops'] or '—'} | {text} |")
        if len(group) > 20:
            lines.append(f"\n（另有 {len(group) - 20} 份，见 JSON）")
    (out / "saves_programs.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\ndistinct programs: {len(programs)}  failed saves: {failed}")
    for fam, group in sorted(by_family.items(), key=lambda kv: -len(kv[1])):
        print(f"  {fam:<10} {len(group):>5} programs  {sum(p['copies'] for p in group):>7} copies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
