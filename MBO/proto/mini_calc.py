# -*- coding: utf-8 -*-
"""
mini_calc.py — 生产计算器的**最小原型**（L2 生产层的第一层：配方 DAG 传递 + 整数化）。

用途：用 v160.7 真机 dump 的配方数据，回答"要 X 速率，需要几台机器、多少原料、多少电"。
这是 MBO 生产层的可行性证明，不是最终实现
（最终实现用 MILP 处理共享中间品的多路线分摊、副产物平衡、多目标权重）。

用法：
    python -X utf8 mini_calc.py silicon:3/s
    python -X utf8 mini_calc.py surge-alloy:0.8/s --json
数据：
    ../spikes/data/gamedata.json（由 spike 脚本从服务端 dump）
"""
import argparse
import json
import math
import sys
import io
from collections import Counter, defaultdict
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "spikes" / "data" / "gamedata.json"

# 同一物品有多条产出路线时，原型用"人工优先级"表达经验（数字越小越优先），
# 正式实现里这是 L2 的生产方案选择（可由 LP 在建筑数/电力/面积上优化后决定）。
PRODUCER_PRIORITY = {
    "silicon-smelter": 10, "graphite-press": 10, "kiln": 10, "ferric-crusher": 10,
    "pulverizer": 20, "cultivator": 10, "spore-press": 10, "pyratite-mixer": 10,
    "blast-mixer": 10, "surge-smelter": 10, "phase-weaver": 10, "cryofluid-mixer": 10,
    "melter": 30, "separator": 30, "disassembler": 30,
}


def load(path=DATA):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return d, {b["name"]: b for b in d["blocks"]}, {i["name"]: i for i in d["items"]}


def build_producers(blocks):
    """item -> [候选产出方块]，按 (人工优先级, 每单位电耗) 排序。"""
    producers = defaultdict(list)
    for name, b in blocks.items():
        r = b.get("recipe")
        if not r or not r.get("craftTime"):
            continue
        cps = r.get("cyclesPerSecond") or (60.0 / r["craftTime"])
        for o in r.get("outputItems") or []:
            producers[o["name"]].append({
                "block": name, "rate": o["amount"] * cps, "cps": cps, "recipe": r,
                "size": b["size"], "power": (b.get("power") or {}).get("usagePerSecond") or 0.0,
            })
    for lst in producers.values():
        lst.sort(key=lambda p: (PRODUCER_PRIORITY.get(p["block"], 100), p["power"] / max(p["rate"], 1e-9)))
    return producers


def solve(target_item, target_rate, blocks, producers, boundary_items=frozenset(), force=None):
    """按拓扑序做一次"连续需求传递 + 每层向上取整"。

    boundary_items: 视为边界输入（不再展开）的物品，例如采矿产物 coal/sand。
    force: {item: block} 强制某物品用指定方块生产（表达人工经验/场景约束）。
    返回 dict(buildings, boundary, power, warnings, order)。
    """
    demand = defaultdict(float)      # 物品 -> 累计需求速率（连续值）
    demand[target_item] += target_rate
    buildings = Counter()
    power = 0.0
    boundary = Counter()
    warnings = []
    order = []                       # 生产者在前、原料在后（pre-order 拓扑序）
    seen = set()

    def visit(item, stack):
        if item in stack:
            raise SystemExit("检测到循环依赖: %s" % " -> ".join(stack + [item]))
        if item in seen:
            return
        seen.add(item)
        order.append(item)
        if item in boundary_items:
            return
        p = producers.get(item)
        if p:
            for inp in p[0]["recipe"]["inputs"]:
                for it in inp.get("items", []):
                    visit(it["name"], stack + [item])

    visit(target_item, [])

    # 拓扑序处理：先处理生产者，再把需求推给上游
    for item in order:
        need = demand[item]
        if need <= 1e-12:
            continue
        if item in boundary_items:
            boundary[item] += need
            continue
        p = producers.get(item)
        if not p:
            boundary[item] += need
            continue
        prod = p[0]
        if force and item in force:
            cand = [x for x in p if x["block"] == force[item]]
            if not cand:
                raise SystemExit("强制生产方式无效: %s 不由 %s 产出" % (item, force[item]))
            prod = cand[0]
        n = math.ceil(need / prod["rate"] - 1e-9)
        if n <= 0:
            continue
        buildings[prod["block"]] += n
        power += n * prod["power"]
        if n * prod["rate"] > need * 1.5 + 1e-9:
            warnings.append("%s 取整后过量 %.2f/s（需求 %.2f，产能 %.2f）"
                            % (item, n * prod["rate"] - need, need, n * prod["rate"]))
        # 上游需求按"实际台数满负荷"计算（n * cps * 每批用量），
        # 这才是真实工厂的输入需求；按理论速率算会系统性低估取整带来的过量。
        for inp in prod["recipe"]["inputs"]:
            for it in inp.get("items", []):
                demand[it["name"]] += n * prod["cps"] * it["amount"]
    return {
        "buildings": dict(buildings),
        "boundary": dict(boundary),
        "power": power,
        "warnings": warnings,
        "order": order,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="形如 silicon:3/s")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--data", default=str(DATA))
    ap.add_argument("--boundary", default="", help="逗号分隔：视为边界输入（采矿/外部供给）的物品")
    ap.add_argument("--force", default="", help="逗号分隔 item=block：强制某物品用指定方块生产")
    a = ap.parse_args()
    item, _, rate = a.target.partition(":")
    rate = float(rate.replace("/s", "") or 1.0)
    boundary_items = frozenset(x.strip() for x in a.boundary.split(",") if x.strip())
    force = {}
    for kv in a.force.split(","):
        if "=" in kv:
            k, v = kv.split("=", 1)
            force[k.strip()] = v.strip()
    _, blocks, items = load(a.data)
    if item not in items:
        raise SystemExit("未知物品: %s（可用: %s）" % (item, ", ".join(sorted(items))))
    producers = build_producers(blocks)
    if item not in producers:
        raise SystemExit("%s 没有原版生产方式（可能是采矿产物，属于边界输入）" % item)
    r = solve(item, rate, blocks, producers, boundary_items, force)
    if a.json:
        print(json.dumps({
            "target": {"item": item, "rate_per_s": rate},
            "buildings": r["buildings"],
            "power_per_s": round(r["power"], 2),
            "raw_inputs_per_s": {k: round(v, 4) for k, v in r["boundary"].items()},
            "warnings": r["warnings"],
            "order": r["order"],
        }, ensure_ascii=False, indent=1))
        return
    print("目标: %s %.3g/s" % (item, rate))
    print("建筑清单:")
    for n, c in sorted(r["buildings"].items(), key=lambda kv: -kv[1]):
        b = blocks[n]
        pw = (b.get("power") or {}).get("usagePerSecond") or 0.0
        print("  %-22s x%-3d size=%d power=%.1f/s" % (n, c, b["size"], pw))
    total = sum(r["buildings"].values())
    area = sum(blocks[n]["size"] ** 2 * c for n, c in r["buildings"].items())
    print("建筑总数 %d（占 %d 格），总耗电 %.1f/s" % (total, area, r["power"]))
    print("边界输入: %s" % (", ".join("%s %.3g/s" % (k, v) for k, v in sorted(r["boundary"].items())) or "无"))
    for w in r["warnings"]:
        print("  [warn] " + w)


if __name__ == "__main__":
    main()
