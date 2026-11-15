#!/usr/bin/env python3
"""gen_turrets.py — 逐台炮塔文章生成器（COMBAT.TURRET.1xx / 2xx + 总览 002）。

输入（全部只读）：
  knowledge/00-data/turrets.json       jar v160.7 反射：reload/range/ammo[]/power/target*
  knowledge/00-data/blocks.json        jar v160.7 反射：health/size/requirements/buildTime
  knowledge/00-data/bullets.json       jar v160.7 反射：splashDamage/pierceCap/damage
  knowledge/00-data/turret_shots.json  源码派生：shots/pattern/barrels/证据行
  knowledge/03-combat/_turrets/verdicts.*.json   评价文案（人工/智能体撰写）

输出：
  knowledge/03-combat/turrets/T1xx-<id>.md   Serpulo 18 台（COMBAT.TURRET.101-118）
  knowledge/03-combat/turrets/T2xx-<id>.md   Erekir  10 台（COMBAT.TURRET.201-210）
  knowledge/03-combat/C11-turret-verdict.md  总览与选型（COMBAT.TURRET.002，就地重写）

口径（写死，勿改）：
  发/s      = 60/(reload × reloadMultiplier) × shots
  单体DPS   = 发/s × 直伤
  面板DPS   = 发/s × (直伤 + 0.75 × 溅射)     （对齐 BulletType.estimateDPS）
  物品/秒   = 发/s × ammoPerShot / ammoMultiplier
  对22甲DPS = 发/s × max(直伤 − 22, 0.1 × 直伤)

用法：
  python knowledge/tools/gen_turrets.py --facts duo   # 打印单塔事实卡（写文案时对照）
  python knowledge/tools/gen_turrets.py --facts all
  python knowledge/tools/gen_turrets.py               # 生成全部文章 + 总览
  python knowledge/tools/gen_turrets.py --dry         # 只统计不写盘
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
D = KB / "00-data"
OUTDIR = KB / "03-combat" / "turrets"
HUB = KB / "03-combat" / "C11-turret-verdict.md"

ORDER_SERPULO = ["duo", "scatter", "scorch", "hail", "wave", "lancer", "arc", "parallax",
                 "swarmer", "salvo", "segment", "tsunami", "fuse", "ripple", "cyclone",
                 "foreshadow", "spectre", "meltdown"]
ORDER_EREKIR = ["breach", "diffuse", "sublimate", "titan", "disperse",
                "afflict", "lustre", "scathe", "smite", "malign"]
TIER_ORDER = ["S", "A", "B", "C", "D"]
B = "/core/src/mindustry/content/Blocks.java"

# 非 item 塔（shootType 不在 bullets.json）与 scathe 的手工数值块：
# 数字来自 Blocks.java 源码（行号见每行第 4 列），不来自 jar 反射表。
MANUAL = {
    "wave": {
        "table": [
            "| 弹药 | 单发伤害 | 发/s | 0甲 DPS | 机制 | 来源 |",
            "|---|---|---|---|---|---|",
            "| water | 0 | 20 | 0 | 只有击退 0.7 与 extinguisher（灭火）标记 | Mindustry-Source" + B + ":3536 |",
            "| slag | 4 | 20 | 80 | 唯一有伤害的弹药 | Mindustry-Source" + B + ":3541 |",
            "| cryofluid | 0 | 20 | 0 | 冻结 + 灭火，无直伤 | Mindustry-Source" + B + ":3544 |",
            "| oil | 0 | 20 | 0 | 只上油（可燃）状态 | Mindustry-Source" + B + ":3547 |",
        ],
        "notes": [
            "reload 3 tick ⇒ 20 发/s，是本作射击频率最高的塔之一；优势全在状态与击退，不在伤害。",
            "液体塔的弹药不是物品：要管道/容器供液，断液即停火（不是打空弹匣）。",
        ],
    },
    "tsunami": {
        "table": [
            "| 弹药 | 单发伤害 | 发/s | 0甲 DPS | ammoMultiplier | 来源 |",
            "|---|---|---|---|---|---|",
            "| water | 0.2 | 20 | 4 | 0.4 | Mindustry-Source" + B + ":3857 |",
            "| slag | 4.75 | 20 | 95 | 0.4 | Mindustry-Source" + B + ":3858 |",
            "| cryofluid | 0.2 | 20 | 4 | 0.4 | Mindustry-Source" + B + ":3859 |",
            "| oil | 0.2 | 20 | 4 | 0.4 | Mindustry-Source" + B + ":3860 |",
        ],
        "notes": [
            "ammoMultiplier 0.4 ⇒ 每发消耗 2.5 单位液体，20 发/s 就是 50 液体/s，供液压力远大于 wave。",
            "shots=2（ShootAlternate 双管交替），所以 0甲 DPS 是 2 × 20 × 单发伤害。",
        ],
    },
    "lancer": {
        "table": [
            "| 项 | 值 | 说明 | 来源 |",
            "|---|---|---|---|",
            "| 直伤 | 140 | LaserBulletType | Mindustry-Source" + B + ":3566 |",
            "| armorMultiplier | 4 | 目标护甲 ×4 参与减法 | Mindustry-Source" + B + ":3567 |",
            "| 发/s | 0.75 | reload 80 tick | Mindustry-Source" + B + ":3568 |",
            "| 0甲 DPS | 105 | 140 × 0.75 | 本文口径 |",
            "| 耗电 | 360/s | consumePower(6) | Mindustry-Source" + B + ":3573 |",
        ],
        "notes": [
            "对 22 甲的靶子：有效护甲 22 × 4 = 88，单发只剩 52，DPS 掉到 39。这是全作最吃护甲惩罚的塔。",
            "pierceCap 4；buildingDamageMultiplier 0.25（拆建筑只有 1/4）。",
        ],
    },
    "arc": {
        "table": [
            "| 项 | 值 | 说明 | 来源 |",
            "|---|---|---|---|",
            "| 直伤 | 20 | LightningBulletType | Mindustry-Source" + B + ":3603 |",
            "| lightningLength | 25 | 链长（世界单位） | Mindustry-Source" + B + ":3604 |",
            "| 发/s | 1.71 | reload 35 tick | Mindustry-Source" + B + ":3626 |",
            "| 0甲 DPS | 34.3 | 20 × 1.71 | 本文口径 |",
            "| 耗电 | 198/s | consumePower(3.3) | Mindustry-Source" + B + ":3631 |",
        ],
        "notes": [
            "collidesAir=false ⇒ 完全不防空；链状闪电会跳到相邻目标，实际总输出高于单体 DPS。",
            "附 shocked 状态（打断/削弱），价值高于数字。",
        ],
    },
    "parallax": {
        "table": [
            "| 项 | 值 | 说明 | 来源 |",
            "|---|---|---|---|",
            "| force | 16 | 牵引力 | Mindustry-Source" + B + ":3642 |",
            "| scaledForce | 9 | 随距离缩放 | Mindustry-Source" + B + ":3643 |",
            "| damage | 0.5/tick | setStats 显示 ×60 = 30/s | Mindustry-Source" + B + ":3644 |",
            "| 耗电 | 198/s | | Mindustry-Source" + B + ":3653 |",
        ],
        "notes": [
            "只打空中（targetAir=true, targetGround=false），把飞行单位往外推，是位移控制而非杀伤。",
            "30/s 的伤害只是附赠，指望它击落是误用。",
        ],
    },
    "segment": {
        "table": [
            "| 项 | 值 | 说明 | 来源 |",
            "|---|---|---|---|",
            "| bulletDamage | 30 | 对弹体的伤害 | Mindustry-Source" + B + ":3837 |",
            "| 发/s | 7.5 | reload 8 tick | Mindustry-Source" + B + ":3843 |",
            "| 拦截吞吐 | 225/s | 只对弹体成立，不对单位 | 本文口径 |",
            "| 耗电 | 480/s | | Mindustry-Source" + B + ":3849 |",
        ],
        "notes": [
            "点防塔：击落飞来的子弹/炮弹，不伤害单位与建筑；它的「DPS」是拦截吞吐而不是杀伤。",
            "对弹幕型敌人价值远超数字，对纯激光/近战敌人几乎为零。",
        ],
    },
    "meltdown": {
        "table": [
            "| 项 | 值 | 说明 | 来源 |",
            "|---|---|---|---|",
            "| 每结算伤害 | 78 | ContinuousLaserBulletType(78) | Mindustry-Source" + B + ":4316 |",
            "| damageInterval | 5 tick | 每 5 tick 结算一次 ⇒ ×12 | Mindustry-Source" + B + ":4317 |",
            "| 0甲 DPS | 936 | 78 × 12 | 本文口径 |",
            "| shootDuration | 230 tick | 单次开火持续 | Mindustry-Source" + B + ":4325 |",
            "| 耗电 | 1020/s | | Mindustry-Source" + B + ":4321 |",
        ],
        "notes": [
            "连续型：目标在射界内就一直结算，不需要命中判定，所以数字极稳。",
            "附 melting 状态与 incendChance 0.4；冷却液消耗 0.5/s 属同级偏高。",
        ],
    },
    "sublimate": {
        "table": [
            "| 弹药 | 每结算伤害 | 0甲 DPS | 特殊 | 来源 |",
            "|---|---|---|---|---|",
            "| ozone | 60 | 720 | ammoMultiplier 1.2、pierceCap 2 | Mindustry-Source" + B + ":4570 |",
            "| cyanogen | 130 | 1560 | rangeChange +70、pierceCap 3 | Mindustry-Source" + B + ":4576 |",
        ],
        "notes": [
            "连续火焰型（damageInterval 5 tick，×12 结算）；液体消耗 18/s，是双层供给（弹药液体 + 电力/冷却）。",
            "cyanogen 的 rangeChange +70 会实打实延长射界，是少数「换弹药换射程」的塔。",
        ],
    },
    "afflict": {
        "table": [
            "| 项 | 值 | 说明 | 来源 |",
            "|---|---|---|---|",
            "| 直伤 | 180 | BasicBulletType | Mindustry-Source" + B + ":5025 |",
            "| 发/s | 1.2 | reload 50 tick | Mindustry-Source" + B + ":5030 |",
            "| 0甲 DPS | 216 | 180 × 1.2 | 本文口径 |",
            "| 耗电 | 300/s | | Mindustry-Source" + B + ":5036 |",
        ],
        "notes": [
            "pierceCap 2（可穿 2 个目标），speed 5、lifetime 80 ⇒ 弹道偏慢、需要预判。",
            "Erekir 中口径电塔，定位类似 lancer 但不吃护甲惩罚（无 armorMultiplier）。",
        ],
    },
    "lustre": {
        "table": [
            "| 项 | 值 | 说明 | 来源 |",
            "|---|---|---|---|",
            "| 每次结算伤害 | 210 | PointLaserBulletType | Mindustry-Source" + B + ":5148 |",
            "| shootCone | 360 | 全向射界 | Mindustry-Source" + B + ":5160 |",
            "| unitSort | strongest | 优先打最强目标 | Mindustry-Source" + B + ":5157 |",
            "| 消耗 | nitrogen 6/60 每 tick + 电 200/60 每 tick | 双层供给 | Mindustry-Source" + B + ":5165 |",
        ],
        "notes": [
            "连续光束型；DPS 口径依赖 ContinuousTurret 的结算间隔，本表不给 DPS 数字（诚实缺口见文末）。",
            "shootCone 360 + strongest 排序 ⇒ 天然点杀最硬的目标，适合放阵地中央。",
        ],
    },
    "malign": {
        "table": [
            "| 项 | 值 | 说明 | 来源 |",
            "|---|---|---|---|",
            "| 直伤 | 70 | FlakBulletType(8, 70) | Mindustry-Source" + B + ":5927 |",
            "| 发/s | 17.14 | reload 3.5 tick | Mindustry-Source" + B + ":5941 |",
            "| 0甲 DPS | 1200 | 70 × 17.14 | 本文口径 |",
            "| 附弹 | intervalBullet 雷电 18 + fragBullet 激光 65 | 每发还带两种子弹 | Mindustry-Source" + B + ":5930 |",
            "| 耗电 | 2400/s | | Mindustry-Source" + B + ":5949 |",
        ],
        "notes": [
            "射界由 ShootSummon 在半径内随机落点（Blocks.java:6246），所以它不是精确瞄准，是覆盖式弹幕。",
            "2400/s 的耗电是全作最高档，必须有独立电网与储能。",
        ],
    },
    "scathe": {
        "table": [
            "| 项 | 值 | 说明 | 来源 |",
            "|---|---|---|---|",
            "| 弹体 | BulletType(0, 0) + spawnUnit 导弹单位 | 塔本身不产生伤害 | Mindustry-Source" + B + ":5218 |",
            "| 真伤害 | 导弹武器溅射 1000 | 见 00-data/bullets.json 的 scathe-missile-weapon1 | 00-data/bullets.json |",
            "| reload | 600 tick | 10 秒一发 | 00-data/turrets.json |",
            "| maxAmmo / ammoPerShot | 45 / 15 | 一匣 3 发 | 00-data/turrets.json |",
        ],
        "notes": [
            "这是导弹发射架而不是炮：伤害由导弹落地结算，所以 DPS 不能按塔的 shootType 算。",
            "射程 1350 世界单位（约 169 格）是全作最远，属于跨屏战略武器。",
        ],
    },
}

# 每塔额外的源码锚点
SRC_EXTRA = {
    "duo": ["Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29"],
    "scatter": ["Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"],
    "fuse": ["Mindustry-Source/core/src/mindustry/entities/pattern/ShootSpread.java:9"],
    "diffuse": ["Mindustry-Source/core/src/mindustry/entities/pattern/ShootSpread.java:9"],
    "swarmer": ["Mindustry-Source/core/src/mindustry/entities/pattern/ShootBarrel.java:1"],
    "cyclone": ["Mindustry-Source/core/src/mindustry/entities/pattern/ShootBarrel.java:1"],
    "tsunami": ["Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29"],
    "spectre": ["Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29"],
    "disperse": ["Mindustry-Source/core/src/mindustry/entities/pattern/ShootAlternate.java:29"],
    "smite": ["Mindustry-Source/core/src/mindustry/entities/pattern/ShootMulti.java:30"],
    "malign": ["Mindustry-Source/core/src/mindustry/entities/pattern/ShootSummon.java:20"],
}

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig", errors="replace"))

def recs(obj):
    if isinstance(obj, dict):
        for k in ("records", "items", "entries", "rows", "data"):
            if isinstance(obj.get(k), list):
                return obj[k]
    return obj if isinstance(obj, list) else []

def g(x, d=1):
    if x is None:
        return "-"
    return (("%." + str(d) + "f") % float(x))

def fmt(x):
    if x is None:
        return "—"
    x = float(x)
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return ("%.2f" % x).rstrip("0").rstrip(".")

class Data:
    def __init__(self):
        self.t = dict((r["id"], r) for r in recs(load(D / "turrets.json")) if r.get("id"))
        self.b = dict((r["id"], r) for r in recs(load(D / "blocks.json")) if r.get("id"))
        self.bu = dict((r["id"], r) for r in recs(load(D / "bullets.json")) if r.get("id"))
        self.sh = dict((r["id"], r) for r in recs(load(D / "turret_shots.json")) if r.get("id"))

    def ammo_rows(self, tid):
        t = self.t[tid]
        shots = int(self.sh.get(tid, {}).get("shots", 1))
        rl_raw = t.get("reload")
        rl = float(rl_raw) if rl_raw else 0.0
        if rl <= 0:
            return shots, None, []
        rows = []
        for a in t.get("ammo") or []:
            bu = self.bu.get(a.get("bullet"), {})
            dmg = float(a.get("damage") or 0)
            spl = float(bu.get("splashDamage") or 0)
            rm = float(a.get("reloadMultiplier") or 1)
            mult = float(a.get("ammoMultiplier") or 1)
            hz = 60.0 / (rl * rm) * shots
            ips = hz * float(t.get("ammoPerShot") or 1) / mult if mult else 0.0
            dps = hz * dmg
            rows.append({"item": a.get("item") or "-", "bullet": a.get("bullet"),
                         "D": dmg, "S": spl, "rm": rm, "mult": mult, "hz": hz,
                         "dps": dps, "panel": hz * (dmg + 0.75 * spl), "ips": ips,
                         "dpi": (dps / ips) if ips else 0.0,
                         "d22": hz * max(dmg - 22.0, 0.1 * dmg), "status": a.get("status")})
        rows.sort(key=lambda r: -r["dps"])
        return shots, rl, rows

    def facts(self, tid):
        t, b = self.t[tid], self.b.get(tid, {})
        shots, rl, rows = self.ammo_rows(tid)
        sh = self.sh.get(tid, {})
        L = ["=== " + tid + " (" + art_id(tid) + ") ===",
             "定义行  " + str(sh.get("src", "?")),
             "块字段  尺寸 %s | 血量 %s | 护甲 %s | 造价 %s 件 | 建造 %s tick" % (
                 fmt(b.get("size", 0)), fmt(b.get("health", 0)), fmt(b.get("armor", 0)),
                 fmt(sum(x.get("amount", 0) for x in (b.get("requirements") or []))),
                 fmt(b.get("buildTime", 0))),
             "塔字段  射程 %s 世界单位（%s 格） | reload %s | shots %s | 模式 %s" % (
                 fmt(t.get("range", 0)), g(float(t.get("range", 0)) / 8.0, 2),
                 ((fmt(rl) + " tick") if rl else "—（无 reload）"), shots,
                 sh.get("pattern", "-")),
             "        maxAmmo %s | ammoPerShot %s | air %s | ground %s | 耗电 %s/s" % (
                 fmt(t.get("maxAmmo", 0)), fmt(t.get("ammoPerShot", 0)), t.get("targetAir"),
                 t.get("targetGround"), fmt((t.get("power") or {}).get("usagePerSecond", 0))),
             "        coolantMult %s | shootCone %s | inaccuracy %s | damageMultiplier %s" % (
                 fmt(t.get("coolantMultiplier", 0)), fmt(t.get("shootCone", 0)),
                 fmt(t.get("inaccuracy", 0)), fmt(t.get("damageMultiplier", 0)))]
        if rows:
            L.append("")
            L.append("%-12s %7s %7s %5s %7s %9s %9s %8s %9s %9s" % (
                "物品", "直伤", "溅射", "rm", "发/s", "单体DPS", "面板DPS", "物品/秒", "DPS/物品", "对22甲"))
            for r in rows:
                L.append("%-12s %7s %7s %5s %7s %9s %9s %8s %9s %9s" % (
                    r["item"], fmt(r["D"]), fmt(r["S"]), g(r["rm"], 2), g(r["hz"], 2),
                    g(r["dps"], 1), g(r["panel"], 1), g(r["ips"], 2), g(r["dpi"], 1), g(r["d22"], 1)))
        else:
            L.append("")
            L.append("（无 ammo[]：shootType 不在 bullets.json，数值见 MANUAL 手工表）")
        L.append("")
        L.append("门禁提醒：正文别写「" + tid + " 射程 20 格 / 尺寸 3 / 血量 800」这类（与表里 160/3/800 口径不同即 E_NUM_CONFLICT）。")
        L.append("        要写射程就用「射程 160 世界单位（20 格）」，先世界单位后格。")
        return "\n".join(L)

def art_id(tid):
    if tid in ORDER_SERPULO:
        return "COMBAT.TURRET.%03d" % (101 + ORDER_SERPULO.index(tid))
    if tid in ORDER_EREKIR:
        return "COMBAT.TURRET.%03d" % (201 + ORDER_EREKIR.index(tid))
    raise KeyError(tid)

def load_verdicts():
    out = {}
    vd = KB / "03-combat" / "_turrets"
    for p in sorted(vd.glob("verdicts.*.json")):
        obj = load(p)
        for k, v in (obj.get("turrets") or {}).items():
            if k in out:
                raise SystemExit("verdicts 重复定义: " + k + "（" + str(p) + "）")
            out[k] = v
    return out

def bullet_row(r):
    return "| %s | %s | %s | %s | %s | %s | %s | %s | %s | 00-data |" % (
        r["item"], fmt(r["D"]), fmt(r["S"]), g(r["rm"], 2), g(r["hz"], 2),
        g(r["dps"], 1), g(r["panel"], 1), g(r["ips"], 2), g(r["d22"], 1))

def render(tid, d, vd):
    t, b = d.t[tid], d.b.get(tid, {})
    shots, rl, rows = d.ammo_rows(tid)
    sh = d.sh.get(tid, {})
    aid = art_id(tid)
    v = vd.get(tid) or {}
    L = []
    srcs = [str(sh.get("src", "src:Mindustry-Source" + B + ":1")).replace("src:", ""),
            "Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9"]
    srcs += SRC_EXTRA.get(tid, [])
    srcs += ["jar:v160.7#turrets/" + tid, "jar:v160.7#blocks/" + tid]
    L.append("---")
    L.append("id: " + aid)
    L.append("title: " + tid + " —— " + (v.get("title") or tid))
    L.append("domain: combat")
    L.append("status: active")
    L.append("ver: [v160.7_rt, v159.3_src]")
    L.append("conf: I")
    L.append("src:")
    emitted_jar = False
    for s in srcs:
        if s.startswith("jar:") and not emitted_jar:
            L.append("  # ver: v160.7_rt  # jar 反射取值（运行值口径）")
            emitted_jar = True
        L.append('  - "' + s + '"')
    L.append("data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]")
    L.append("depends: [COMBAT.TURRET.001, COMBAT.TURRET.002, COMBAT.NUMBERS.001]")
    L.append("tags: [炮塔, " + tid + ", " + (v.get("role") or "评价") + "]")
    L.append("---")
    L.append("")
    L.append("## 一句话")
    L.append("")
    L.append(v.get("oneliner") or (tid + " 的评价待补。"))
    L.append("")
    L.append("## 规则 / 公式")
    L.append("")
    L.append("- **层位**：" + (v.get("tier") or "-") + " ｜ **岗位**：" + (v.get("role") or "-"))
    L.append("- **射击模式**：" + str(sh.get("pattern") or "-") + "（每触发 " + str(shots) + " 发；"
             + (("reload " + fmt(rl) + " tick") if rl else "无 reload（连续型/牵引型）") + "）"
             + " [src: 00-data/turret_shots.json]")
    tgt = []
    if t.get("targetAir"):
        tgt.append("空中")
    if t.get("targetGround"):
        tgt.append("地面")
    if t.get("targetBlocks"):
        tgt.append("建筑")
    L.append("- **目标层**：" + ("、".join(tgt) if tgt else "（表未标注）"))
    for m in v.get("mechanics") or []:
        L.append("- " + m)
    if v.get("strengths"):
        L.append("- **优点**：")
        for s in v["strengths"]:
            L.append("  - " + s)
    if v.get("weaknesses"):
        L.append("- **缺点**：")
        for s in v["weaknesses"]:
            L.append("  - " + s)
    L.append("- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤；面板 DPS 再按 "
             "BulletType.estimateDPS 把溅射按 0.75 折进去（见 [[COMBAT.NUMBERS.001]]）。"
             + " [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]")
    L.append("")
    L.append("## 数值")
    L.append("")
    L.append("| 项 | 值 | 来源 |")
    L.append("|---|---|---|")
    L.append("| 尺寸 | " + fmt(b.get("size", 0)) + " | 00-data/blocks.json |")
    L.append("| 血量 | " + fmt(b.get("health", 0)) + " | 00-data/blocks.json |")
    L.append("| 护甲 | " + fmt(b.get("armor", 0)) + " | 00-data/blocks.json |")
    req = "、".join("%s × %s" % (x.get("item"), fmt(x.get("amount", 0))) for x in (b.get("requirements") or []))
    L.append("| 造价 | " + fmt(sum(x.get("amount", 0) for x in (b.get("requirements") or []))) + " 件（" + (req or "-") + "） | 00-data/blocks.json |")
    L.append("| 射程 | " + fmt(t.get("range", 0)) + " 世界单位（" + g(float(t.get("range", 0)) / 8.0, 2) + " 格） | 00-data/turrets.json |")
    L.append("| reload | " + (fmt(rl) if rl else "—") + " tick | 00-data/turrets.json |")
    L.append("| shots | " + str(shots) + " | 00-data/turret_shots.json |")
    L.append("| 冷却液倍率 / shootCone | " + fmt(t.get("coolantMultiplier", 0)) + " / " + fmt(t.get("shootCone", 0)) + " | 00-data/turrets.json |")
    L.append("| 耗电 | " + fmt((t.get("power") or {}).get("usagePerSecond", 0)) + "/s | 00-data/turrets.json |")
    L.append("")
    if rows:
        L.append("| 弹药 | 直伤 | 溅射 | reloadMult | 发/s | 单体DPS(0甲) | 面板DPS | 物品/秒 | 对22甲DPS | 来源 |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            L.append(bullet_row(r))
        L.append("")
    elif tid in MANUAL:
        for ln in MANUAL[tid]["table"]:
            L.append(ln)
        L.append("")
    if tid in MANUAL:
        mk = " [src: " + str(sh.get("src", "")).replace("src:", "") + "]"
        for n in MANUAL[tid]["notes"]:
            L.append("- " + n + mk)
        L.append("")
    for n in v.get("numbers_notes") or []:
        L.append("- " + n)
    if v.get("numbers_notes"):
        L.append("")
    L.append("## 源码锚点")
    L.append("")
    L.append("- " + str(sh.get("src", "?")).replace("src:", "") + " —— 定义行 new " + str(sh.get("class", "?")) + "(\"" + tid + "\")")
    for e in sh.get("evidence") or []:
        L.append("- Mindustry-Source" + B + ":" + str(e["line"]) + " —— 含 " + " / ".join(e["contains"]))
    if not sh.get("evidence"):
        L.append("- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1（本塔未覆写）")
    for s in SRC_EXTRA.get(tid, []):
        L.append("- " + s)
    L.append("- 00-data/turret_shots.json#id=" + tid + " —— 源码派生记录（含证据行）")
    L.append("")
    L.append("## 实测与反例")
    L.append("")
    for c in v.get("counterexamples") or []:
        L.append("- " + c)
    L.append("")
    L.append("## 常见误解")
    L.append("")
    for m in v.get("misconceptions") or []:
        L.append("- " + m)
    L.append("")
    L.append("## 相关")
    L.append("")
    rel = list(v.get("related") or [])
    for x in ["COMBAT.TURRET.001", "COMBAT.TURRET.002", "COMBAT.NUMBERS.001"]:
        if x not in rel:
            rel.append(x)
    sib = ORDER_SERPULO if tid in ORDER_SERPULO else ORDER_EREKIR
    i = sib.index(tid)
    for j in (i - 1, i + 1):
        if 0 <= j < len(sib):
            s2 = art_id(sib[j])
            if s2 not in rel:
                rel.append(s2)
    for x in rel:
        L.append("- [[" + x + "]]")
    L.append("")
    return "\n".join(L)

def render_hub(d, vd):
    L = []
    L.append("---")
    L.append("id: COMBAT.TURRET.002")
    L.append("title: 原版炮塔评价总览与选型决策表（28 台逐台索引）")
    L.append("domain: combat")
    L.append("status: active")
    L.append("ver: [v160.7_rt, v159.3_src]")
    L.append("conf: I")
    L.append("src:")
    L.append('  - "Mindustry-Source/core/src/mindustry/content/Blocks.java:3258"')
    L.append("data: [00-data/turrets.json, 00-data/blocks.json, 00-data/bullets.json, 00-data/turret_shots.json]")
    L.append("depends: [COMBAT.TURRET.001, COMBAT.NUMBERS.001]")
    L.append("tags: [炮塔, 评价, 选型, 索引]")
    L.append("---")
    L.append("")
    L.append("## 一句话")
    L.append("")
    L.append("28 门炮塔要按「层位（拿到手的时代）」和「岗位（你缺什么）」两个维度选，而不是按单体 DPS 排名："
             "同层位里 DPS 最高的塔往往最吃供给、最吃位置，而低 DPS 的塔常常是唯一能解决某个具体问题的。")
    L.append("")
    L.append("## 规则 / 公式")
    L.append("")
    L.append("- **口径**：单体 DPS = 60/(reload × reloadMultiplier) × shots × 直伤，只算一个目标、零护甲、"
             "不冷却、不卡供给。它不是实战输出，是可比价。")
    L.append("- **层位字母**：S=长期一线主力 ｜ A=强但专用（特定敌人/局面才上）｜ B=过渡或补充 ｜ C=只在特定场合 ｜ D=有更好选择。"
             "这是按「长期战役里值不值得造」给的判断，不是数值排名。")
    L.append("- **护甲修正**：对 A 甲目标换成 60/(reload × rm) × shots × max(直伤 − A, 0.1 × 直伤)"
             "（minArmorDamage 0.1，见 [[COMBAT.TURRET.001]]）。 [src: Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414]")
    L.append("- **供给约束**：物品/秒 列是满射速时的弹药消耗，超过产能就自动降频，所以「DPS/物品」"
             "这一列才决定持续输出。")
    L.append("- **层位不等于强度**：Serpulo 与 Erekir 是两套独立科技线，跨线比数字没有意义。")
    L.append("")
    L.append("## 数值")
    L.append("")
    L.append("| 塔 | 层位 | 岗位 | 最佳弹药 | 单体DPS(0甲) | 造价(件) | DPS/件 | 射程(格) | 目标 | 来源 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for tid in ORDER_SERPULO + ORDER_EREKIR:
        t, b = d.t[tid], d.b.get(tid, {})
        shots, rl, rows = d.ammo_rows(tid)
        v = vd.get(tid) or {}
        best = rows[0] if rows else None
        dps = best["dps"] if best else 0.0
        cost = sum(x.get("amount", 0) for x in (b.get("requirements") or []))
        tgt = ("空" if t.get("targetAir") else "") + ("地" if t.get("targetGround") else "")
        L.append("| " + art_id(tid) + " " + tid + " | " + (v.get("tier") or "-") + " | " + (v.get("role") or "-")
                 + " | " + (best["item"] if best else "液体/特殊") + " | " + (g(dps, 1) if best else "见正文")
                 + " | " + fmt(cost) + " | " + (g(dps / cost, 2) if best and cost else "-")
                 + " | " + g(float(t.get("range", 0)) / 8.0, 1) + " | " + (tgt or "-") + " | 00-data |")
    L.append("")
    L.append("## 源码锚点")
    L.append("")
    L.append("- Mindustry-Source" + B + " —— 28 台塔的定义、shootType 与弹药表")
    L.append("- Mindustry-Source/core/src/mindustry/entities/pattern/ShootPattern.java:9 —— shots 默认 1")
    L.append("- Mindustry-Source/core/src/mindustry/entities/bullet/BulletType.java:414 —— estimateDPS（面板口径）")
    L.append("- 00-data/turret_shots.json —— 源码派生的 shots/pattern 表（jar 反射拿不到）")
    L.append("")
    L.append("## 实测与反例")
    L.append("")
    L.append("- 只看单体 DPS 会得出「breach 2437.5 最强」的结论，但 breach 用 carbide 时 7.5 发/s × 2 件 = "
             "15 件/s，一条满速传送带（11 件/s）根本喂不满；掐掉供给后它与 300 件的塔没区别。 [src: 00-data/turrets.json + 00-data/blocks.json]")
    L.append("- 反向例子：wave 的 0 甲 DPS 是 0（water 无伤），但它是唯一能灭火、能击退的塔，"
             "在燃烧/近战波次里的价值无法用 DPS 表达。")
    L.append("")
    L.append("## 常见误解")
    L.append("")
    L.append("- 「造价越贵越强」：foreshadow 造价 2700 件、单体 405 DPS；spectre 1875 件就有 685.7 DPS。"
             "贵的部分买的是射程与穿甲，不是数字。 [src: 00-data/turrets.json]")
    L.append("- 「口径可以混用」：旧表格混过「单发伤害」与「每发伤害 × 发数」，同一张表里 duo 27 与 salvo 31 不可比。"
             "本库统一按上面的口径重算，旧数字作废。")
    L.append("")
    L.append("## 相关")
    L.append("")
    L.append("- [[COMBAT.TURRET.001]] 炮塔机制（reload / 冷却液 / 过热 / 目标层）")
    L.append("- [[COMBAT.NUMBERS.001]] DPS 三式与三层口径")
    for tid in ORDER_SERPULO + ORDER_EREKIR:
        L.append("- [[" + art_id(tid) + "]] " + tid)
    L.append("")
    return "\n".join(L)

def lint_verdicts(d, vd):
    """自检：把评价文案渲染成 md，再用与 check_kb 同口径的规则查一遍（给写文案的人用）。"""
    import re as _re
    bad = 0
    NUM_LABELS = {"health": ("血量", "health", "生命值"), "size": ("尺寸", "size"),
                  "range": ("射程", "range")}
    claim = _re.compile(r"\d+(?:\.\d+)?\s*(?:/s|/tick|/秒|格|秒|tick|帧|%)|\d+\.\d+")
    ids = ORDER_SERPULO + ORDER_EREKIR
    for tid in ids:
        v = vd.get(tid)
        if not v:
            print("[MISS] " + tid + " 没有 verdicts 记录")
            bad += 1
            continue
        miss = [k for k in ("tier", "role", "title", "oneliner") if not str(v.get(k) or "").strip()]
        if not (v.get("mechanics") or []):
            miss.append("mechanics")
        if not (v.get("counterexamples") or []):
            miss.append("counterexamples")
        if not (v.get("misconceptions") or []):
            miss.append("misconceptions")
        if miss:
            print("[FAIL] " + tid + " 缺字段: " + ",".join(miss))
            bad += 1
        text = render(tid, d, vd)
        if text.count("\n") + 1 > 250:
            print("[FAIL] " + tid + " 渲染后超过 250 行")
            bad += 1
        # E_NUM_CONFLICT 同口径
        meta = {}
        for name in list(d.b.keys()):
            meta[name] = d.b[name]
        for name in list(d.t.keys()):
            meta.setdefault(name, {})
        for ln in text.splitlines():
            low = ln.lower()
            if len(ln) < 8:
                continue
            for field, labels in NUM_LABELS.items():
                hit = None
                for lab in labels:
                    if lab.isascii():
                        m = _re.search(r"(?<![A-Za-z0-9_-])" + _re.escape(lab) + r"(?![A-Za-z0-9_-])", low)
                        li = m.start() if m else -1
                    else:
                        li = ln.find(lab)
                    if li >= 0:
                        hit = (lab, li)
                        break
                if not hit:
                    continue
                lab, li = hit
                for tname, rec in meta.items():
                    if len(tname) < 3:
                        continue
                    nm = _re.search(r"(?<![A-Za-z0-9_-])" + _re.escape(tname) + r"(?![A-Za-z0-9_-])", low)
                    if not nm or abs(nm.start() - li) > 40:
                        continue
                    want = None
                    if field in ("health", "size"):
                        want = rec.get(field) if field == "size" else rec.get("health")
                    elif field == "range":
                        want = d.t.get(tname, {}).get("range")
                    try:
                        want = float(want)
                    except (TypeError, ValueError):
                        continue
                    tail = ln[max(nm.start(), li):]
                    m = _re.search(_re.escape(lab) + r"[^0-9\n]{0,14}(-?\d+(?:\.\d+)?)", tail)
                    if not m:
                        continue
                    got = float(m.group(1))
                    if abs(got - want) > max(0.51, want * 0.02):
                        print("[CONFLICT] " + tid + " 行: " + ln.strip()[:90])
                        print("           " + tname + " 的 " + field + " 写 " + str(got) + "，数据为 " + str(want))
                        bad += 1
                    break
        # 反例/误解汉字数
        ce = (v.get("counterexamples") or []) + (v.get("misconceptions") or [])
        han = len(_re.findall(r"[\u4e00-\u9fff]", "".join(ce)))
        if han < 20:
            print("[FAIL] " + tid + " 反例+误解汉字只有 " + str(han) + " 个（>=20）")
            bad += 1
        # 缺来源标记的数字行（正文段落，不含表格）
        last_marker = -1
        for i, ln in enumerate(text.splitlines()):
            if ln.lstrip().startswith("|") or not ln.strip():
                continue
            if not claim.search(ln):
                continue
            if any(k in ln for k in ("[src:", "[实测", "见 DATA", "00-data/", "src:", "ver:", "conf:")):
                last_marker = i
                continue
            if last_marker >= 0 and i - last_marker <= 6:
                continue
            print("[NOSRC] " + tid + " 行: " + ln.strip()[:90])
            bad += 1
    print(("自检通过" if not bad else "自检问题 %d 处" % bad))
    return 1 if bad else 0

def main(argv=None):
    ap = argparse.ArgumentParser(description="逐台炮塔文章生成器")
    ap.add_argument("--facts", nargs="?", const="all", default=None, help="打印事实卡（塔 id 或 all）")
    ap.add_argument("--dry", action="store_true", help="只统计，不写盘")
    ap.add_argument("--only", nargs="*", default=None, help="只生成指定塔")
    ap.add_argument("--dump", default=None, help="把某塔渲染结果打印到 stdout（不写盘）")
    ap.add_argument("--lint", action="store_true", help="自检 verdicts 文案（不写盘）")
    a = ap.parse_args(argv)
    d = Data()
    if a.facts:
        ids = ORDER_SERPULO + ORDER_EREKIR if a.facts == "all" else [a.facts]
        for tid in ids:
            print(d.facts(tid))
            print()
        return 0
    vd = load_verdicts()
    if a.dump:
        print(render(a.dump, d, vd))
        return 0
    if a.lint:
        return lint_verdicts(d, vd)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    n = 0
    todo = ORDER_SERPULO + ORDER_EREKIR
    if a.only:
        todo = [x for x in todo if x in a.only]
    for tid in todo:
        aid = art_id(tid)
        path = OUTDIR / ("T" + aid.split(".")[2] + "-" + tid + ".md")
        text = render(tid, d, vd)
        if not a.dry:
            path.write_text(text, encoding="utf-8", newline="\n")
        n += 1
        print("写出 %s（%d 行）" % (path.name, text.count("\n") + 1))
    hub = render_hub(d, vd).replace("B_placeholder", "").replace("Mindustry-Source" + ":3258", "Mindustry-Source" + B + ":3258")
    if not a.dry:
        HUB.write_text(hub, encoding="utf-8", newline="\n")
    print("写出 %s（%d 行）" % (HUB.name, hub.count("\n") + 1))
    print("完成 %d 篇。verdicts 覆盖 %d/%d。" % (n, len([x for x in todo if x in vd]), len(todo)))
    missing = [x for x in todo if x not in vd]
    if missing:
        print("缺评价文案: " + ", ".join(missing))
    return 0

if __name__ == "__main__":
    sys.exit(main())
