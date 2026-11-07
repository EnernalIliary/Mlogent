# -*- coding: utf-8 -*-
"""extract_src.py -- 从 v159.3 Java 源码树抽取"公式锚点 + 关键常量"（知识库 00-data/src_anchors.json）。

用法:
    python -u kb-stage/tools/extract_src.py
    python -u kb-stage/tools/extract_src.py --src "F:/OneDrive/桌面/AtomicStates/Mindustry-Source/core/src" --out <json>

设计取舍: **不解析 Java AST**。每个锚点声明为
    (id, 相对路径, 起始正则, 取数方式, 说明)
取数方式:
    num    -> 从命中行里抓第一个数字字面量（支持 1.6f / 8 / 0.046f）
    line   -> 只记录行号与该行原文（公式行, 供人读）
    block  -> 记录从命中行开始、括号配平的方法体（上限 N 行）
只做"正则定位 + 括号配平", 因此换行/空白变化不会误伤, 而 Java 语法改动会显式报 warn。

产物: {"generated","src_root","ver","counts","items":[...],"warnings":[...]}
每条 item: {id, path, line, code, value?, note, ver}
"""
import argparse
import datetime
import json
import os
import re

DEFAULT_SRC = r"F:\OneDrive\桌面\AtomicStates\Mindustry-Source\core\src"
VER = "v159.3"

def _num(s):
    m = re.search(r"-?\d+(?:\.\d+)?[fFdD]?", s)
    if not m:
        return None
    t = m.group(0).rstrip("fFdD")
    try:
        return float(t) if ("." in t) else int(t)
    except ValueError:
        return None

def _block(lines, start, max_lines=24):
    """从 start 行起做括号配平，返回方法体文本（够读公式即可）。"""
    buf, depth, seen = [], 0, False
    for i in range(start, min(len(lines), start + max_lines)):
        ln = lines[i]
        buf.append(ln.rstrip())
        depth += ln.count("{") - ln.count("}")
        if "{" in ln:
            seen = True
        if seen and depth <= 0:
            break
    return "\n".join(buf)

# (id, 相对路径, 正则, 模式, 说明)
TARGETS = [
    # ---- 基础口径
    ("vars.tilesize", "mindustry/Vars.java", r"\btilesize\s*=\s*8", "num", "一个 tile 的像素/世界单位数"),
    ("vars.minArmorDamage", "mindustry/Vars.java", r"\bminArmorDamage\s*=\s*0\.1f", "num", "护甲后伤害下限比例"),
    ("vars.tilePayload", "mindustry/Vars.java", r"\btilePayload\s*=", "num", "单格载荷上限"),
    # ---- 伤害管线
    ("damage.calculateDamage", "mindustry/entities/Damage.java", r"static float calculateDamage\(", "block", "溅射衰减（单位）"),
    ("damage.falloff", "mindustry/entities/Damage.java", r"float falloff\s*=", "num", "溅射衰减权重 falloff"),
    ("damage.applyArmor", "mindustry/entities/Damage.java", r"static float applyArmor\(", "block", "护甲减伤"),
    ("damage.tileDamage", "mindustry/entities/Damage.java", r"static void tileDamage\(", "line", "建筑溅射入口"),
    ("damage.edgeScale", "mindustry/entities/Damage.java", r"float edgeScale\s*=", "num", "建筑溅射边缘权重"),
    ("damage.scaledHitSize", "mindustry/entities/Damage.java", r"dst\(x, y\) - unit\.type\.hitSize", "line", "scaled 溅射按外缘距离"),
    # ---- 单位受伤
    ("shield.damage", "mindustry/entities/comp/ShieldComp.java", r"public void damage\(float amount\)", "block", "单位受伤主路径"),
    ("shield.damagePierce", "mindustry/entities/comp/ShieldComp.java", r"public void damagePierce\(", "block", "无视护甲"),
    ("shield.rawDamage", "mindustry/entities/comp/ShieldComp.java", r"protected void rawDamage\(", "block", "护盾先扣"),
    # ---- 弹道
    ("bullet.calculateRange", "mindustry/entities/bullet/BulletType.java", r"protected float calculateRange\(", "block", "射程=lifetime*speed(含 drag)"),
    ("bullet.handlePierce", "mindustry/entities/bullet/BulletType.java", r"void handlePierce\(", "block", "穿透掉伤"),
    ("bullet.damageMultiplier", "mindustry/entities/bullet/BulletType.java", r"public float damageMultiplier\(", "block", "伤害倍率来源"),
    ("bullet.hitSplash", "mindustry/entities/bullet/BulletType.java", r"splashDamage \* b\.damageMultiplier\(\)", "line", "命中时溅射调用"),
    ("bullet.pierceDamageFactor", "mindustry/entities/bullet/BulletType.java", r"pierceDamageFactor\s*=", "num", "穿透每层掉伤比例"),
    ("bullet.splashDamage", "mindustry/entities/bullet/BulletType.java", r"public float splashDamage\s*=", "num", "默认溅射伤害"),
    # ---- 状态
    ("status.fieldDefaults", "mindustry/type/StatusEffect.java", r"public float damageMultiplier\s*=", "line", "状态倍率字段默认 1"),
    ("status.applyTransition", "mindustry/type/StatusEffect.java", r"boolean applyTransition\(", "block", "反应伤害入口"),
    ("statuscomp.reset", "mindustry/entities/comp/StatusComp.java", r"applied\.clear\(\)", "line", "每 tick 重置倍率"),
    ("statuscomp.multiply", "mindustry/entities/comp/StatusComp.java", r"speedMultiplier \*=", "block", "倍率逐项相乘"),
    ("statuscomp.armorOverride", "mindustry/entities/comp/StatusComp.java", r"armorOverride\s*=\s*entry\.armorOverride", "line", "护甲覆盖而非相乘"),
    # ---- 刷怪
    ("spawngroup.getSpawned", "mindustry/game/SpawnGroup.java", r"public int getSpawned\(", "block", "每波数量"),
    ("spawngroup.getShield", "mindustry/game/SpawnGroup.java", r"public float getShield\(", "block", "每波护盾"),
    ("spawngroup.max", "mindustry/game/SpawnGroup.java", r"public int max\s*=", "num", "数量上限"),
    ("spawngroup.unitAmount", "mindustry/game/SpawnGroup.java", r"public int unitAmount\s*=", "num", "基础数量"),
    ("spawngroup.unitScaling", "mindustry/game/SpawnGroup.java", r"public float unitScaling\s*=", "line", "数量缩放分母(默认 never)"),
    ("difficulty.enum", "mindustry/game/Difficulty.java", r"enum Difficulty", "block", "五档难度三元组"),
    ("waves.version", "mindustry/game/Waves.java", r"waveVersion\s*=", "num", "波次表版本号"),
    ("waves.spawnGroupCount", "mindustry/game/Waves.java", r"new SpawnGroup\(", "count", "内置刷怪组条数"),
    ("wavespawner.consts", "mindustry/ai/WaveSpawner.java", r"private static final float margin", "line", "margin/coreMargin/maxSteps"),
    ("wavespawner.spawnEnemies", "mindustry/ai/WaveSpawner.java", r"public void spawnEnemies\(", "block", "刷怪主流程"),
    ("wavespawner.spawnEffect", "mindustry/ai/WaveSpawner.java", r"public void spawnEffect\(Unit unit\)", "block", "出生 unmoving/invincible"),
    # ---- 波次计时 / 胜负
    ("logic.play", "mindustry/core/Logic.java", r"public void play\(", "block", "首波 grace = 2x waveSpacing"),
    ("logic.runWave", "mindustry/core/Logic.java", r"void runWave\(", "block", "推进波次与 wavetime"),
    ("logic.checkGameState", "mindustry/core/Logic.java", r"void checkGameState\(", "block", "胜负判定"),
    ("logic.waitEnemies", "mindustry/core/Logic.java", r"state\.rules\.waitEnemies \|\|", "line", "暂停倒计时条件"),
    # ---- 规则默认值
    ("rules.waveSpacing", "mindustry/game/Rules.java", r"public float waveSpacing\s*=", "line", "默认波次间隔"),
    ("rules.initialWaveSpacing", "mindustry/game/Rules.java", r"public float initialWaveSpacing\s*=", "num", "首波间隔"),
    ("rules.winWave", "mindustry/game/Rules.java", r"public int winWave\s*=", "num", "胜利波次 0=不限"),
    ("rules.dropZoneRadius", "mindustry/game/Rules.java", r"public float dropZoneRadius\s*=", "num", "降落区半径"),
    ("rules.enemyCoreBuildRadius", "mindustry/game/Rules.java", r"public float enemyCoreBuildRadius\s*=", "num", "敌核禁建半径"),
    ("rules.unitHealthFn", "mindustry/game/Rules.java", r"public float unitHealth\(", "block", "单位血量倍率合成"),
    ("rules.unitDamageFn", "mindustry/game/Rules.java", r"public float unitDamage\(", "block", "单位伤害倍率合成"),
    # ---- 电力
    ("power.chargeBatteries", "mindustry/world/blocks/power/PowerGraph.java", r"public float chargeBatteries\(", "block", "电池充电"),
    ("power.distributePower", "mindustry/world/blocks/power/PowerGraph.java", r"void distributePower\(", "block", "覆盖度=min(1,produced/needed)"),
    ("power.consumePower", "mindustry/world/consumers/ConsumePower.java", r"public float requestedPower\(", "block", "每 tick 请求功率"),
    # ---- 热
    ("heat.producer", "mindustry/world/blocks/heat/HeatProducer.java", r"public class HeatProducer", "block", "heatOutput/warmupRate"),
    ("heat.heatOutput", "mindustry/world/blocks/heat/HeatProducer.java", r"public float heatOutput\s*=", "num", "默认产热"),
    ("heat.warmupRate", "mindustry/world/blocks/heat/HeatProducer.java", r"public float warmupRate\s*=", "num", "升温速率"),
    ("heat.conductor", "mindustry/world/blocks/heat/HeatConductor.java", r"public float visualMaxHeat\s*=", "num", "导热体上限"),
    ("heat.calculateHeat", "mindustry/entities/comp/BuildingComp.java", r"public float calculateHeat\(", "block", "接触点传热"),
    # ---- 生产
    ("drill.getDrillTime", "mindustry/world/blocks/production/Drill.java", r"public float getDrillTime\(", "block", "钻速分母=drillTime+50*硬度"),
    ("drill.drillTime", "mindustry/world/blocks/production/Drill.java", r"public float drillTime\s*=", "num", "基础钻孔时间"),
    ("drill.hardnessMul", "mindustry/world/blocks/production/Drill.java", r"hardnessDrillMultiplier\s*=", "num", "硬度惩罚系数"),
    ("drill.liquidBoost", "mindustry/world/blocks/production/Drill.java", r"liquidBoostIntensity\s*=", "num", "液体加速上限"),
    ("drill.warmup", "mindustry/world/blocks/production/Drill.java", r"warmupSpeed\s*=", "num", "预热速率"),
    # ---- 传送带
    ("conveyor.itemSpace", "mindustry/world/blocks/distribution/Conveyor.java", r"private static final float itemSpace", "num", "物品间距(格)"),
    ("conveyor.capacity", "mindustry/world/blocks/distribution/Conveyor.java", r"private static final int capacity", "num", "同时容纳件数"),
    ("conveyor.moved", "mindustry/world/blocks/distribution/Conveyor.java", r"float moved = speed \* edelta\(\)", "line", "位置推进"),
    ("conveyor.block.speed", "mindustry/content/Blocks.java", r"conveyor = new Conveyor\(\"conveyor\"\)", "line", "基础带实例参数起始行"),
    ("conveyor.conveyor.speed", "mindustry/content/Blocks.java", r"\bspeed = 0\.046f", "num", "基础带 0.046 格/tick"),
    ("conveyor.conveyor.displayed", "mindustry/content/Blocks.java", r"\bdisplayedSpeed = 6\.5f", "num", "基础带展示吞吐"),
    ("conveyor.titanium.speed", "mindustry/content/Blocks.java", r"\bspeed = 0\.0801f", "num", "钛带 0.0801 格/tick"),
    ("conveyor.titanium.displayed", "mindustry/content/Blocks.java", r"\bdisplayedSpeed = 10f", "num", "钛带展示吞吐"),
    ("conveyor.armored.speed", "mindustry/content/Blocks.java", r"\bspeed = 0\.08f", "num", "装甲带 0.08 格/tick"),
    ("conveyor.armored.displayed", "mindustry/content/Blocks.java", r"\bdisplayedSpeed = 11f", "num", "装甲带展示吞吐"),
    # ---- 方块血量/尺寸
    ("block.scaledHealth", "mindustry/world/Block.java", r"public float scaledHealth\s*=", "num", "每格血量占位 -1"),
    ("block.size", "mindustry/world/Block.java", r"public int size\s*=", "num", "默认 1x1"),
    ("block.healthCalc", "mindustry/world/Block.java", r"if\(health == -1\)", "block", "health=size*size*scaledHealth"),
    # ---- 指令预算
    ("logicblock.budget", "mindustry/world/blocks/logic/LogicBlock.java", r"maxInstructionScale\s*=", "line", "预算常量"),
    ("logicblock.loop", "mindustry/world/blocks/logic/LogicBlock.java", r"if\(accumulator > maxInstructionScale \* ipt\)", "block", "每 tick 执行循环"),
    # ---- 建筑受伤
    ("building.damageBlockHealth", "mindustry/entities/comp/BuildingComp.java", r"float dm = state\.rules\.blockHealth\(team\)", "line", "建筑伤害/血量倍率"),
    ("building.armorHit", "mindustry/entities/comp/BuildingComp.java", r"block\.armor \* t\.armorMultiplier", "line", "建筑护甲减免"),
]

def extract(src_root, out_path):
    items, warnings = [], []
    counts = {}
    for tid, rel, pat, mode, note in TARGETS:
        p = os.path.join(src_root, rel)
        if not os.path.exists(p):
            warnings.append({"id": tid, "warn": "file missing", "path": rel})
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
        rx = re.compile(pat)
        hit = None
        for i, ln in enumerate(lines):
            if rx.search(ln):
                hit = i
                break
        if hit is None:
            warnings.append({"id": tid, "warn": "pattern not found", "path": rel, "pattern": pat})
            continue
        rec = {"id": tid, "path": "Mindustry-Source/core/src/" + rel, "line": hit + 1, "note": note, "ver": VER}
        if mode == "num":
            rec["value"] = _num(lines[hit])
        elif mode == "line":
            rec["code"] = lines[hit].strip()
            mnum = re.search(r"=\s*(-?\d+(?:\.\d+)?)[fFdD]?\s*;", lines[hit])
            if mnum:
                rec["value"] = _num(mnum.group(1))
        elif mode == "count":
            rec["value"] = sum(1 for ln in lines if rx.search(ln))
        else:
            rec["code"] = _block(lines, hit)
            for j in range(hit, min(len(lines), hit + 6)):
                n = _num(lines[j]) if re.search(r"0x|=\s*-?\d", lines[j]) else None
        items.append(rec)
        counts[tid] = rec.get("value", rec.get("line"))
    doc = {
        "generated": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "src_root": src_root,
        "ver": VER,
        "counts": counts,
        "items": items,
        "warnings": warnings,
        "note": "公式锚点表: 只做正则定位 + 括号配平, 不解析 Java AST; 重跑即可核对行号漂移。",
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    return doc

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "00-data", "src_anchors.json"))
    a = ap.parse_args()
    doc = extract(a.src, a.out)
    print("wrote", a.out)
    print("items=%d warnings=%d" % (len(doc["items"]), len(doc["warnings"])))
    for w in doc["warnings"]:
        print("  WARN", w["id"], w["warn"], w.get("pattern", ""))
    nv = [(k, v) for k, v in doc["counts"].items() if isinstance(v, (int, float))]
    print("numeric anchors:", ", ".join("%s=%s" % (k, v) for k, v in nv))

if __name__ == "__main__":
    main()
