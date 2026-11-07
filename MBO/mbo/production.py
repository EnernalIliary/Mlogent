"""L2 生产层：目标产量 → 建筑清单（MVP 版）。

规则（与 docs/02 §E1 一致）：

1. 目标速率取“单机速率的整数倍可达值”：`n = ceil(rate / per_machine)`；
2. 输入递归展开，遇到 `boundary` 里的物品就停（**边界是必填项**，不写会一路展开到矿，
   那是地图相关的，不属于 v1）；
3. 三类供给必须分清：**配方产出 / 采矿产出（本版不展开）/ 外部输入（边界）**；
4. ceil 会让上游富余（多产一点），本版只记录 `surplus`，不做回收——回收是 MILP 的事。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Plan:
    target: str
    requested_rate: float
    achieved_rate: float = 0.0
    machines: dict = field(default_factory=dict)      # block -> count
    order: list = field(default_factory=list)          # [(block, count)] 供布局使用
    demand: dict = field(default_factory=dict)         # 边界物品每秒需求
    power_need: float = 0.0
    warnings: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "target": self.target,
            "requested_rate": self.requested_rate,
            "achieved_rate": round(self.achieved_rate, 4),
            "machines": self.machines,
            "boundary_demand": {k: round(v, 4) for k, v in self.demand.items()},
            "power_need": round(self.power_need, 2),
            "warnings": self.warnings,
        }


def expand(gd, target: str, rate: float, boundary=(), force: dict | None = None) -> Plan:
    """把目标产量展开成建筑清单。`force` 可指定某物品由哪个方块生产（item=block）。"""
    boundary = set(boundary)
    force = dict(force or {})
    plan = Plan(target=target, requested_rate=rate)

    if target not in gd.items:
        raise KeyError("未知物品 %r" % target)

    def producers(item: str) -> list:
        return gd.producers_of(item)

    def servable(item: str, seen=frozenset()) -> bool:
        """能不能只靠 boundary 供给做出来（递归闭包，防环）。"""
        if item in boundary:
            return True
        if item in seen:
            return False
        cands = producers(item)
        if not cands:
            return False
        return any(
            all(servable(i, seen | {item}) for i, _ in b.recipe.inputs)
            for b in cands
        )

    def choose(item: str, amount: float):
        """选配方：优先“不引入新边界”的，其次超产量最小（E1 期望贴合目标），再少方块。"""
        cands = producers(item)
        pick = force.get(item)
        if pick:
            cands = [b for b in cands if b.name == pick]
            if not cands:
                raise KeyError("%s 不能生产 %r" % (pick, item))
        scored = []
        for b in cands:
            per = b.recipe.outputs_per_second.get(item, 0.0)
            if per <= 0:
                continue
            n = max(1, math.ceil(amount / per - 1e-9))
            scored.append((not all(servable(i) for i, _ in b.recipe.inputs),
                           round(n * per, 6), n, b.size * b.size, b.name, b, n))
        if not scored:
            raise ValueError("%s 没有可用配方" % item)
        scored.sort(key=lambda s: s[:5])
        return scored[0][5], scored[0][6]

    def need(item: str, amount: float, depth: int = 0):
        if amount <= 1e-9:
            return
        if item in boundary or depth > 8:
            plan.demand[item] = plan.demand.get(item, 0.0) + amount
            return
        cands = producers(item)
        if not cands:
            plan.demand[item] = plan.demand.get(item, 0.0) + amount
            plan.warnings.append("%s 没有配方产出，按外部输入处理" % item)
            return
        block, n = choose(item, amount)
        per_rate = block.recipe.outputs_per_second.get(item, 0.0)
        if per_rate <= 0:
            raise ValueError("%s 的配方不产 %r" % (block.name, item))
        n = max(1, math.ceil(amount / per_rate - 1e-9))
        plan.machines[block.name] = plan.machines.get(block.name, 0) + n
        plan.order.append((block.name, n))

        # 上游：按 n 台的实际消耗继续展开
        for iname, iamt in block.recipe.inputs_per_second.items():
            need(iname, n * iamt, depth + 1)

    need(target, rate)
    plan.achieved_rate = rate

    # 汇总电力需求（只算配方机器，电源不参与）
    for block_name, cnt in plan.machines.items():
        plan.power_need += cnt * gd.block(block_name).power_usage_per_second
    return plan


def predict_rate(gd, plan: Plan, layout=None) -> float:
    """按布局里的实际方块推算目标物品产量（比 plan 更保守，能发现布局漏放）。"""
    if layout is None:
        counts = plan.machines
    else:
        counts = {}
        for t in layout.tiles:
            counts[t.block] = counts.get(t.block, 0) + 1
    total = 0.0
    for name, cnt in counts.items():
        b = gd.blocks.get(name)
        if b is None or b.recipe is None:
            continue
        total += cnt * b.recipe.outputs_per_second.get(plan.target, 0.0)
    return total
