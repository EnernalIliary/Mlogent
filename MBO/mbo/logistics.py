"""L2.5 物流吞吐模型：速率由物流元件决定（用户口径 m02384）。

旧产量模型只有一个上限——机器能力（`n × 单机速率`）。用户指出两条新口径：

1. **输入/输出标记必须在绘制区域外**：`item-source` / `item-void` 是端口，不算工厂
   的一部分，不能塞在机器中间（见 `ports_outside`）；
2. **速率由物流元件决定**：传送带/物流门/路由器自身的吞吐会截断产量。必须从布局的
   运输网络算，而不是从机器台数算。

做法：把布局看成**容量网络**，两个方向各算一次最大流

    输入流  item-source →（传送带/门/路由器）→ 机器输入端口      items/s
    输出流  机器输出端口 →（传送带/门/路由器）→ item-void/容器    items/s

    可达速率 = min(机器能力, 输入流 ÷ 每件产成品的输入需求, 输出流 ÷ 每件输出)

边容量（docs/19）：传送带/管道每格 4.9 items/s（`BELT_RATE`，docs/14 实测）；物流门/
路由器/交叉器同样是 4.9（分流不增容）；`item-source` 供给 100 items/s
（`ItemSource.itemsPerSecond`）；机器端口按配方每秒需求/产出。

它是**稳态容量上界**：忽略在途品、门的交替偏斜与带子长度延迟，所以是乐观值，真机略低。
"""

from __future__ import annotations

from collections import deque

from .model import BELT_RATE, DIRV, GATES

TILE_CAP = BELT_RATE

TRANSPORT = ("conveyor", "duct")
NODES = ("junction", "router") + tuple(GATES)
SINKS = ("item-void", "container", "vault", "core-shard", "core-foundation",
         "core-nucleus", "reinforced-container", "reinforced-vault")
PORTS = ("item-source", "item-void", "liquid-source", "liquid-void")

SOURCE_CAP = 100.0      # ItemSource.itemsPerSecond


class _Dinic:
    """小图最大流（浮点容量）：BFS 分层 + DFS 增广。"""

    def __init__(self) -> None:
        self.edges: list = []
        self.adj: dict = {}

    def node(self, key) -> int:
        if not hasattr(self, "_ids"):
            self._ids: dict = {}
        if key not in self._ids:
            self._ids[key] = len(self._ids)
            self.adj.setdefault(self._ids[key], [])
        return self._ids[key]

    def add(self, u_key, v_key, cap: float) -> None:
        u, v = self.node(u_key), self.node(v_key)
        self.adj[u].append(len(self.edges))
        self.edges.append([u, v, cap])
        self.adj[v].append(len(self.edges))
        self.edges.append([v, u, 0.0])

    def max_flow(self, s_key, t_key) -> float:
        s, t = self.node(s_key), self.node(t_key)
        total = 0.0
        while True:
            level = {s: 0}
            q = deque([s])
            while q:
                u = q.popleft()
                for ei in self.adj.get(u, ()):
                    _, b, cap = self.edges[ei]
                    if cap > 1e-9 and b not in level:
                        level[b] = level[u] + 1
                        q.append(b)
            if t not in level:
                return total
            it = {u: 0 for u in level}

            def dfs(u: int, f: float) -> float:
                if u == t:
                    return f
                nbrs = self.adj.get(u, ())
                while it[u] < len(nbrs):
                    ei = nbrs[it[u]]
                    _, b, cap = self.edges[ei]
                    if cap > 1e-9 and level.get(b) == level[u] + 1:
                        d = dfs(b, min(f, cap))
                        if d > 1e-9:
                            self.edges[ei][2] -= d
                            self.edges[ei ^ 1][2] += d
                            return d
                    it[u] += 1
                return 0.0

            while True:
                d = dfs(s, 1e18)
                if d <= 1e-9:
                    break
                total += d


def _in(tile):
    """方块的入口（接收物品）。"""
    return ("in", id(tile))


def _out(tile):
    """方块的出口（送出物品）。"""
    return ("out", id(tile))


def _front(lay, tile):
    dx, dy = DIRV[tile.rotation]
    return lay.tile_at(tile.x + dx, tile.y + dy)


def _neighbors(lay, tile):
    out = []
    for cx, cy in lay.cells(tile.block, tile.x, tile.y):
        for dx, dy in DIRV.values():
            o = lay.tile_at(cx + dx, cy + dy)
            if o is not None and o is not tile and o not in out:
                out.append(o)
    return out


def _machine(gd, tile):
    b = gd.blocks.get(tile.block)
    return b if (b is not None and b.recipe is not None) else None


def build_net(lay, gd, item: str, want: str) -> _Dinic:
    """按 item / 方向建容量网络。want="in" 供给机器，want="out" 收集机器产出。

    节点约定：每个方块都有入口 `_in(t)` 与出口 `_out(t)`；
    - 传送带/门/路由器/交叉器：入口→出口一条 `TILE_CAP` 边（整格吞吐上限）；
      传送带的出口只连**正前方**一格（方向性），其余方块出口可连所有相邻入口；
    - 机器：入口→T 容量=该物品每秒需求（in），或 S→出口 容量=每秒产出（out）；
    - 端口：item-source 接 S，item-void/容器/仓库 接 T。
    """
    d = _Dinic()
    S, T = ("S",), ("T",)

    def is_transit(b):
        return b in TRANSPORT or b in NODES

    def accepts(tile) -> bool:
        """该方块能否作为本方向的落点。"""
        b = tile.block
        if is_transit(b):
            return True
        if want == "in":
            return _machine(gd, tile) is not None
        return b in SINKS

    # 1) 所有运输/节点方块：入口 → 出口
    for t in lay.tiles:
        if is_transit(t.block):
            d.add(_in(t), _out(t), TILE_CAP)

    # 2) 传送带方向性：只推给正前方
    for t in lay.tiles:
        if t.block in TRANSPORT:
            f = _front(lay, t)
            if f is not None and accepts(f):
                d.add(_out(t), _in(f), TILE_CAP)

    # 3) 门/路由器/交叉器：任意相邻运输方块或节点之间可通（整格容量已在上一步）
    for t in lay.tiles:
        if t.block in NODES:
            for o in _neighbors(lay, t):
                if o.block in NODES:
                    d.add(_out(o), _in(t), TILE_CAP)
                elif o.block in TRANSPORT:
                    # 带子只在自己朝向门时才向门送货；门可以往任何相邻带子送货
                    if _front(lay, o) is t:
                        d.add(_out(o), _in(t), TILE_CAP)
                if is_transit(o.block):
                    d.add(_out(t), _in(o), TILE_CAP)
                elif o.block in SINKS and want == "out":
                    # 路由器/门可以往任何相邻的接收方块卸货（含黑洞/容器）
                    d.add(_out(t), _in(o), TILE_CAP)

    # 4) 机器
    for t in lay.tiles:
        b = _machine(gd, t)
        if b is None:
            continue
        if want == "in":
            need = b.recipe.inputs_per_second.get(item, 0.0)
            if need <= 1e-9:
                continue
            d.add(_in(t), T, need)
            for o in _neighbors(lay, t):
                if o.block in NODES:
                    d.add(_out(o), _in(t), TILE_CAP)
                elif o.block in TRANSPORT and _front(lay, o) is t:
                    d.add(_out(o), _in(t), TILE_CAP)
        else:
            out = b.recipe.outputs_per_second.get(item, 0.0)
            if out <= 1e-9:
                continue
            d.add(S, _out(t), out)
            for o in _neighbors(lay, t):
                if is_transit(o.block) or o.block in SINKS:
                    d.add(_out(t), _in(o), TILE_CAP)

    # 5) 端口
    for t in lay.tiles:
        if t.block == "item-source" and want == "in":
            d.add(S, _out(t), SOURCE_CAP)
            for o in _neighbors(lay, t):
                if accepts(o):
                    d.add(_out(t), _in(o), SOURCE_CAP)
        elif t.block in SINKS and want == "out":
            d.add(_in(t), T, 1e12)
    return d


def flow(lay, gd, item: str, want: str) -> float:
    """单物品、单方向的稳态吞吐上界（items/s）。"""
    d = build_net(lay, gd, item, want)
    if not d.edges:
        return 0.0
    return d.max_flow(("S",), ("T",))


def estimate(lay, gd, plan) -> dict:
    """按物流容量估可达速率；返回明细供 report/preview 展示。"""
    target = plan.target
    producers = [t for t in lay.tiles
                 if _machine(gd, t) and target in gd.blocks[t.block].recipe.outputs_per_second]
    machine_cap = sum(gd.blocks[t.block].recipe.outputs_per_second[target] for t in producers)

    in_total: dict[str, float] = {}
    out_total = 0.0
    for t in producers:
        r = gd.blocks[t.block].recipe
        out_total += r.outputs_per_second.get(target, 0.0)
        for item, need in r.inputs_per_second.items():
            in_total[item] = in_total.get(item, 0.0) + need

    in_flows = {}
    rate_in = float("inf")
    for item, need in in_total.items():
        f = flow(lay, gd, item, "in")
        in_flows[item] = f
        if need > 1e-9:
            rate_in = min(rate_in, f * (out_total / need) if out_total > 0 else f)
    if rate_in == float("inf"):
        rate_in = machine_cap
    out_flow = flow(lay, gd, target, "out")
    rate_out = out_flow

    rate = min(machine_cap, rate_in, rate_out)
    if rate >= machine_cap - 1e-9:
        bottleneck = "machine"
    elif rate_in <= rate_out:
        bottleneck = "input"
    else:
        bottleneck = "output"
    return {
        "machine_cap": round(machine_cap, 4),
        "in_flow": {k: round(v, 4) for k, v in in_flows.items()},
        "out_flow": round(out_flow, 4),
        "rate_input_limited": round(rate_in, 4),
        "rate_output_limited": round(rate_out, 4),
        "rate": round(rate, 4),
        "bottleneck": bottleneck,
    }


def ports_outside(lay, gd) -> tuple:
    """端口（输入/输出标记）是否全在工厂外接矩形之外。

    工厂 = 所有**非端口**方块的外接矩形。端口必须完全落在矩形外面
    （贴边也算在内，所以不满足）。返回 (ok, 说明)。
    """
    xs, ys, ports = [], [], []
    for t in lay.tiles:
        if t.block in PORTS:
            ports.append(t)
            continue
        for cx, cy in lay.cells(t.block, t.x, t.y):
            xs.append(cx)
            ys.append(cy)
    if not ports:
        return True, "无端口"
    if not xs:
        return False, "只有端口，没有工厂方块"
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    bad = []
    for t in ports:
        for cx, cy in lay.cells(t.block, t.x, t.y):
            if x0 <= cx <= x1 and y0 <= cy <= y1:
                bad.append("%s@(%d,%d)" % (t.block, t.x, t.y))
                break
    if bad:
        return False, "端口落在工厂矩形 [%d..%d]×[%d..%d] 内：%s" % (x0, x1, y0, y1, "、".join(bad))
    return True, "工厂矩形 [%d..%d]×[%d..%d]，端口全在外部" % (x0, x1, y0, y1)
