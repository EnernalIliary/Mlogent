#!/usr/bin/env python3
"""gen_turret_shots.py — 生成 00-data/turret_shots.json（源码派生：每触发发数与射击模式）。

为什么需要这张表：jar 反射（00-data/turrets.json）拿不到 ShootPattern.shots
（它是 ShootPattern 的 public 字段，但 Turret 实例上只有一个匿名子类实例，
反射表只收录了 Turret 自身的标量字段）。DPS 公式里的"发数"因此缺一个输入，
之前的文章只能靠手抄，口径反复出错。

本表由**源码**派生（不是 jar 反射），每条记录带 Blocks.java 行号与校验片段：
脚本会重新打开 Blocks.java，逐条断言 (1) 该行确实是 new <Cls>("<id>")，
(2) 证据行确实含有所声明 token（如 shots = 4），断言失败直接退出码 1。

用法：
    python knowledge/tools/gen_turret_shots.py            # 生成 00-data/turret_shots.json
    python knowledge/tools/gen_turret_shots.py --check    # 只校验不写盘
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
KB = HERE.parent
REPO = KB.parent
BLOCKS = REPO / "Mindustry-Source/core/src/mindustry/content/Blocks.java"
OUT = KB / "00-data/turret_shots.json"

# id, 定义类, 定义行, shots, pattern, barrels, shotDelay, firstShotDelay, 证据(行号, 必须出现的 token)
RECORDS = [
    ("duo",        "ItemTurret",   3258, 1,  "ShootAlternate(3.5f)", 2, None, None, [(3300, ["ShootAlternate"])]),
    ("scatter",    "ItemTurret",   3333, 2,  "ShootPattern + shotDelay", 1, 5, None, [(3402, ["shotDelay"]), (3403, ["shots", "2"])]),
    ("scorch",     "ItemTurret",   3419, 1,  "ShootPattern(默认)", 1, None, None, []),
    ("hail",       "ItemTurret",   3463, 1,  "ShootPattern(默认)", 1, None, None, []),
    ("wave",       "LiquidTurret", 3529, 1,  "ShootPattern(默认)", 1, None, None, []),
    ("lancer",     "PowerTurret",  3561, 1,  "ShootPattern + firstShotDelay", 1, None, 40, [(3565, ["firstShotDelay", "40"])]),
    ("arc",        "PowerTurret",  3602, 1,  "ShootPattern(默认)", 1, None, None, []),
    ("parallax",   "TractorBeamTurret", 3641, 1, "无射击循环（持续牵引）", 1, None, None, []),
    ("swarmer",    "ItemTurret",   3656, 4,  "ShootBarrel(barrels=8)", 8, 5, None, [(3706, ["ShootBarrel"]), (3712, ["shots", "4"]), (3713, ["shotDelay"])]),
    ("salvo",      "ItemTurret",   3731, 4,  "ShootPattern + shotDelay", 1, 3, None, [(3824, ["shots", "4"]), (3825, ["shotDelay", "3"])]),
    ("segment",    "PointDefenseTurret", 3836, 1, "点防（每触发拦截 1 枚弹体）", 1, None, None, []),
    ("tsunami",    "LiquidTurret", 3850, 2,  "ShootAlternate(4f)", 2, None, None, [(3902, ["ShootAlternate"]), (3903, ["shots", "2"])]),
    ("fuse",       "ItemTurret",   3915, 3,  "ShootSpread(3, 20f)", 1, None, None, [(3923, ["ShootSpread", "3"])]),
    ("ripple",     "ItemTurret",   3955, 4,  "ShootPattern", 1, None, None, [(4065, ["shots", "4"])]),
    ("cyclone",    "ItemTurret",   4085, 1,  "ShootBarrel", 2, None, None, [(4166, ["ShootBarrel"]), (4167, ["barrels"])]),
    ("foreshadow", "ItemTurret",   4203, 1,  "ShootPattern(默认)", 1, None, None, []),
    ("spectre",    "ItemTurret",   4248, 1,  "ShootAlternate(8f)", 2, None, None, [(4302, ["ShootAlternate"])]),
    ("meltdown",   "LaserTurret",  4315, 1,  "连续激光（shootDuration 230）", 1, None, None, []),
    ("breach",     "ItemTurret",   4351, 1,  "ShootPattern(默认)", 1, None, None, []),
    ("diffuse",    "ItemTurret",   4463, 15, "ShootSpread(15, 4f)", 1, None, None, [(4515, ["ShootSpread", "15"])]),
    ("sublimate",  "ContinuousLiquidTurret", 4553, 1, "连续火焰", 1, None, None, []),
    ("titan",      "ItemTurret",   4639, 1,  "ShootPattern(默认)", 1, None, None, []),
    ("disperse",   "ItemTurret",   4840, 4,  "ShootAlternate(4f) + shots/barrels", 4, None, None, [(5001, ["ShootAlternate"]), (5003, ["shots", "4"]), (5004, ["barrels", "4"])]),
    ("afflict",    "PowerTurret",  5024, 1,  "ShootPattern(默认)", 1, None, None, []),
    ("lustre",     "ContinuousTurret", 5147, 1, "连续光束", 1, None, None, []),
    ("scathe",     "ItemTurret",   5212, 1,  "发射 MissileUnitType 导弹单位", 1, None, None, [(5224, ["MissileUnitType"])]),
    ("smite",      "ItemTurret",   5656, 5,  "ShootMulti(ShootAlternate(5f) 派生) + shots=barrels=5", 5, None, None, [(5721, ["ShootAlternate"]), (5723, ["shots", "barrels", "5"])]),
    ("malign",     "PowerTurret",  5926, 1,  "ShootSummon", 1, None, None, [(6246, ["ShootSummon"])]),
]

def main(argv=None):
    ap = argparse.ArgumentParser(description="生成 00-data/turret_shots.json（源码派生）")
    ap.add_argument("--check", action="store_true", help="只校验，不写盘")
    ap.add_argument("--blocks", default=str(BLOCKS), help="Blocks.java 路径")
    a = ap.parse_args(argv)

    bp = Path(a.blocks)
    if not bp.is_file():
        print("找不到 Blocks.java: " + str(bp), file=sys.stderr)
        return 2
    lines = bp.read_text(encoding="utf-8", errors="replace").split("\n")

    recs, bad = [], 0
    for (tid, cls, line, shots, pattern, barrels, shotDelay, firstShotDelay, ev) in RECORDS:
        def at(ln):
            return lines[ln - 1] if 1 <= ln <= len(lines) else ""

        defn = at(line)
        ok = ('new %s("%s")' % (cls, tid)) in defn
        if not ok:
            print("[FAIL] %s 第 %d 行不是 new %s(\"%s\")：%s" % (tid, line, cls, tid, defn.strip()[:80]), file=sys.stderr)
            bad += 1
        for (eln, toks) in ev:
            body = at(eln)
            miss = [t for t in toks if t not in body]
            if miss:
                print("[FAIL] %s 证据行 %d 缺 token %s：%s" % (tid, eln, miss, body.strip()[:80]), file=sys.stderr)
                bad += 1
        rec = {
            "id": tid,
            "name": tid,
            "src": "src:Mindustry-Source/core/src/mindustry/content/Blocks.java:%d" % line,
            "ver": "v159.3",
            "class": cls,
            "shots": shots,
            "pattern": pattern,
            "barrels": barrels,
            "evidence": [{"line": eln, "contains": toks} for (eln, toks) in ev],
        }
        if shotDelay is not None:
            rec["shotDelay"] = shotDelay
        if firstShotDelay is not None:
            rec["firstShotDelay"] = firstShotDelay
        recs.append(rec)

    if bad:
        print("校验失败 %d 处，未写盘" % bad, file=sys.stderr)
        return 1

    obj = {
        "table": "turret_shots",
        "note": "源码派生表（非 jar 反射）：每触发发数 shots 与射击模式。shots 缺省为 1，见 ShootPattern.shots 默认值",
        "src": "Mindustry-Source/core/src/mindustry/content/Blocks.java",
        "shootpattern_src": "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9",
        "ver": "v159.3",
        "generator": "knowledge/tools/gen_turret_shots.py",
        "count": len(recs),
        "records": recs,
    }
    if a.check:
        print("校验通过 %d 条（未写盘）" % len(recs))
        return 0
    OUT.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("写出 %s（%d 条）" % (OUT, len(recs)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
