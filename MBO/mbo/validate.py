"""L4 静态校验（离线、秒级）。真机之前必须全绿。

检查项对应 docs/01 §3.3 的 R1–R7 与 docs/14 §3 的布线规则：

- R7 occupancy（重叠/越界）——游戏 `place()` 是静默覆盖，只能我们拦；
- 传送带前端必须指向“能接货”的方块，不能指向空位/电源；
- 每台机器的每种输入都必须有相邻供给（item-source 或指向它的带子）；
- R4 consumer 必须与 power-node 正交相邻；R3 连线必须显式写且双向对称；
- 电力连通块数必须为 1（否则真机里就是孤岛，eff 直接 0）。
"""

from __future__ import annotations

from .model import BELT_RATE, DIRV, GATES, read_points

ROUTERS = ("router", "junction", "duct", "duct-router", "sorter", "inverted-sorter")

POWER = ("power-node", "power-source")


def static_check(lay, gd, plan=None, strict_ports: bool = False) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    info: dict = {}

    sizes = lay.sizes

    # ---- occupancy（重算，不信任构造期状态）
    occ = {}
    for t in lay.tiles:
        for cx, cy in lay.cells(t.block, t.x, t.y):
            if not (0 <= cx < lay.w and 0 <= cy < lay.h):
                errors.append("越界：%s@(%d,%d)" % (t.block, t.x, t.y))
            if (cx, cy) in occ and occ[(cx, cy)] is not t:
                errors.append("重叠：%s@(%d,%d) 与 %s 冲突于 (%d,%d)"
                              % (t.block, t.x, t.y, occ[(cx, cy)].block, cx, cy))
            occ[(cx, cy)] = t

    # ---- 传送带前端
    for t in lay.tiles:
        if t.block != "conveyor":
            continue
        dx, dy = DIRV[t.rotation]
        fwd = lay.tile_at(t.x + dx, t.y + dy)
        if fwd is None:
            errors.append("传送带@(%d,%d) rot=%d 前端是空位" % (t.x, t.y, t.rotation))
        elif fwd.block in POWER or fwd.block == "item-source":
            errors.append("传送带@(%d,%d) 前端是 %s（接不了货）" % (t.x, t.y, fwd.block))

    # ---- 每台机器的输入供给
    def feeds(tile) -> dict:
        """返回 {item: 供给源数量}：相邻 item-source 或前端指向它的传送带。"""
        got: dict[str, int] = {}
        for cx, cy in lay.cells(tile.block, tile.x, tile.y):
            for dx, dy in DIRV.values():
                o = lay.tile_at(cx + dx, cy + dy)
                if o is None:
                    continue
                if o.block == "item-source" and isinstance(o.config, dict):
                    name = gd.item_name(o.config.get("id"))
                    if name:
                        got[name] = got.get(name, 0) + 1
                elif o.block == "conveyor":
                    vx, vy = DIRV[o.rotation]
                    if (o.x + vx, o.y + vy) in lay.cells(tile.block, tile.x, tile.y):
                        # 带子指向本机器，但不知道它运什么：交给上游 source 去对
                        got.setdefault("__belt__", 0)
                        got["__belt__"] += 1
                elif o.block in GATES:
                    # 物流门/带子都只说明"有东西能送过来"，具体运什么交给上层 source 对
                    got.setdefault("__belt__", 0)
                    got["__belt__"] += 1
        return got

    for t in lay.tiles:
        b = gd.blocks.get(t.block)
        if b is None or b.recipe is None or not b.consumes_power and not b.recipe.inputs_per_second:
            continue
        inputs = set(b.recipe.inputs_per_second)
        got = feeds(t)
        supplied = set(k for k in got if k != "__belt__")
        missing = inputs - supplied
        if missing and got.get("__belt__", 0) < len(missing):
            errors.append("%s@(%d,%d) 缺输入供给：%s" % (t.block, t.x, t.y, sorted(missing)))
        # 单条带能否喂饱（每条输入一行 = 一条带）
        for item, need in b.recipe.inputs_per_second.items():
            if need > BELT_RATE:
                errors.append("%s 对 %s 的需求 %.2f/s 超过单带 %.2f/s"
                              % (t.block, item, need, BELT_RATE))
            elif need > 0.9 * BELT_RATE:
                warnings.append("%s 对 %s 的需求 %.2f/s 已接近单带上限"
                                % (t.block, item, need, BELT_RATE))

    # ---- 物流门（溢流门 / 反溢流门）：必须有上游，且至少一个非电源下游
    for t in lay.tiles:
        if t.block not in GATES:
            continue
        cells = lay.cells(t.block, t.x, t.y)
        ups, downs = 0, []
        for cx, cy in cells:
            for dx, dy in DIRV.values():
                o = lay.tile_at(cx + dx, cy + dy)
                if o is None or o is t:
                    continue
                if o.block == "item-source":
                    ups += 1
                elif o.block == "conveyor":
                    vx, vy = DIRV[o.rotation]
                    if (o.x + vx, o.y + vy) in cells:
                        ups += 1
                elif o.block in GATES:
                    ups += 1
                elif o.block in ROUTERS:
                    ups += 1
                if o.block not in POWER:
                    downs.append(o)
        if ups == 0:
            errors.append("%s@(%d,%d) 没有上游供给（源或指向它的带子）"
                          % (t.block, t.x, t.y))
        if not downs:
            errors.append("%s@(%d,%d) 没有任何下游（物料会卡在门里）"
                          % (t.block, t.x, t.y))

    # ---- 电力
    consumers = [t for t in lay.tiles if gd.block(t.block).consumes_power]
    nodes = [t for t in lay.tiles if t.block == "power-node"]
    sources = [t for t in lay.tiles if t.block == "power-source"]
    comps = 0
    if consumers:
        for c in consumers:
            if not lay.adjacent(c, "power-node"):
                errors.append("%s@(%d,%d) 没有相邻 power-node（真机里会孤立）"
                              % (c.block, c.x, c.y))
        if nodes:
            for n in nodes:
                pts = read_points(n.config)
                if not pts:
                    errors.append("power-node@(%d,%d) 没有 links config" % (n.x, n.y))
                rng = gd.block("power-node").laser_range
                cap = gd.block("power-node").max_nodes
                if len(pts) > cap:
                    errors.append("power-node@(%d,%d) 连了 %d 个，超过 maxNodes=%d"
                                  % (n.x, n.y, len(pts), cap))
                for dx, dy in pts:
                    if max(abs(dx), abs(dy)) > rng:
                        errors.append("power-node@(%d,%d) 的 link (%d,%d) 超过 laserRange=%d"
                                      % (n.x, n.y, dx, dy, rng))
                    o = lay.tile_at(n.x + dx, n.y + dy)
                    if o is None or o.block not in POWER:
                        errors.append("power-node@(%d,%d) 的 link 落点不是电力方块"
                                      % (n.x, n.y))
                    elif not any(ox == -dx and oy == -dy for ox, oy in read_points(o.config)):
                        errors.append("power-node@(%d,%d) 与 (x+%d,y+%d) 的 link 不对称"
                                      % (n.x, n.y, dx, dy))
            comps = _components(lay, nodes + sources)
            if comps != 1:
                errors.append("电力连通块数=%d（应为 1）" % comps)
        else:
            errors.append("有 consumer 但没有 power-node")

    # ---- 产物出口（容器/黑洞/核心，或能转交出去的传送带/物流门/路由器）
    SINK = ("container", "vault", "core-shard", "item-void")
    OUT_TAKE = SINK + ("conveyor", "duct", "junction", "router", "sorter",
                       "inverted-sorter", "overflow-gate", "underflow-gate")
    for t in lay.tiles:
        if gd.block(t.block).recipe is None:
            continue
        if not any(lay.adjacent(t, s) for s in OUT_TAKE):
            warnings.append("%s@(%d,%d) 的产物没有出口（旁边既没有容器/黑洞，"
                            "也没有传送带或物流门）" % (t.block, t.x, t.y))

    st = lay.stats()
    info.update({
        "blocks": st["blocks"], "tiles": st["tiles"], "footprint": st["footprint"],
        "counts": st["counts"],
        "power_consumers": len(consumers), "power_nodes": len(nodes),
        "power_sources": len(sources), "power_components": comps,
        "power_need": round(sum(gd.block(c.block).power_usage_per_second for c in consumers), 2),
        "warnings": warnings,
    })
    # 端口在外（docs/19）：item-source / item-void 只能当工厂边界之外的 I/O 标记
    from . import logistics
    ports_ok, ports_msg = logistics.ports_outside(lay, gd)
    info["ports_outside"] = ports_ok
    info["ports_msg"] = ports_msg
    if strict_ports and not ports_ok:
        errors.append("端口位置违规：" + ports_msg)
    elif not strict_ports and not ports_ok:
        warnings.append("端口落在工厂矩形内（旧模板）：" + ports_msg)

    return {"ok": not errors, "errors": errors, "warnings": warnings, "info": info}


def _components(lay, power_tiles) -> int:
    ids = {id(t) for t in power_tiles}
    seen, comps = set(), 0
    for t in power_tiles:
        if id(t) in seen:
            continue
        comps += 1
        stack = [t]
        while stack:
            cur = stack.pop()
            if id(cur) in seen:
                continue
            seen.add(id(cur))
            for dx, dy in read_points(cur.config):
                o = lay.tile_at(cur.x + dx, cur.y + dy)
                if o is not None and id(o) in ids and id(o) not in seen:
                    stack.append(o)
    return comps
