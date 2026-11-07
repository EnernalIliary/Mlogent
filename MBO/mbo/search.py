"""L2/L3 搜索层：把“人工试模板”换成“脚本枚举 + 物流模型打分 + Pareto 选优”。

来历（用户 m02384 + m02395）：蓝图要满足
  ① 输入/输出标记（item-source / item-void）必须完全落在工厂外接矩形**之外**；
  ② 可达速率由**物流网络容量**决定，不是“机器台数 × 单机速率”。
`spikes/gen/search_ported.py` 已经用脚本证明这件事可行，本模块把它搬成生产代码。

搜索空间（石墨 1/s = 2 台 2×2 机器，可推广到任意 2 台同型号机器）：

    机器排布：水平 / 垂直 × 缝宽 0..3
    桥接元件：无 / underflow-gate / overflow-gate / router（同时贴两台机器的那一格）
    输入方案：单源经桥接元件 / 每台机器各一个源
    出口方案：每台机器各一个 void / 单个 void（不贴机器时用 1 条传送带接力）

三个目标（不塌缩，保留 Pareto 前沿）：
    端口数（ports）、工厂格数（tiles）、外接矩形面积（box）
`pick(objective=...)` 只在**用户明确给出偏好**时挑一个代表点，其余前沿始终保留在结果里。
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from . import logistics
from .model import DIRV, ROT, Layout, item_cfg

GRID = (9, 7)          # 搜索网格（够放 2 台机器 + 外圈端口）
TOL = 1e-3             # 物流模型是 4 位小数，判“够不够”必须留容差
BRIDGES = ("underflow-gate", "overflow-gate", "router")
OBJECTIVES = ("ports", "clusters", "tiles", "box")


# ---------------------------------------------------------------- 候选
@dataclass(frozen=True)
class Candidate:
    """一个可行的（端口在外）布局候选。blocks 是 (name, x, y, rot, item) 的元组。"""

    blocks: Tuple[tuple, ...]
    label: str
    ports: int
    tiles: int
    box: int
    rate: float
    bottleneck: str
    in_flow: Dict[str, float]
    out_flow: float
    ok_need: bool
    clusters: int = 0        # 端口格按 4-邻接分组的组数（1 = 工厂只有一个开口）
    padded: bool = False      # True = blocks 已在画布坐标里（模板生成），无需再平移

    def signature(self) -> tuple:
        return (self.ports, self.tiles, self.box, round(self.rate, 3))

    def as_dict(self) -> dict:
        return {
            "label": self.label, "ports": self.ports, "tiles": self.tiles,
            "box": self.box, "clusters": self.clusters,
            "rate": self.rate, "bottleneck": self.bottleneck,
            "in_flow": self.in_flow, "out_flow": self.out_flow,
        }


@dataclass
class SearchResult:
    objective: str
    candidates: int
    feasible: int
    front: List[Candidate] = field(default_factory=list)
    best: Optional[Candidate] = None
    grid: Tuple[int, int] = GRID
    all_candidates: List[Candidate] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "objective": self.objective,
            "grid": list(self.grid),
            "candidates": self.candidates,
            "feasible": self.feasible,
            "pareto": [list(c.signature()) for c in self.front],
            "picked": self.best.as_dict() if self.best else None,
        }


# ---------------------------------------------------------------- 几何工具
def _cells(size: int, x: int, y: int) -> set:
    ox, oy = x - (size - 1) // 2, y - (size - 1) // 2
    return {(ox + i, oy + j) for i in range(size) for j in range(size)}


def _sizes(gd) -> dict:
    return {b.name: b.size for b in gd.blocks.values()}


def _make(gd, blocks, grid) -> Optional[Layout]:
    w, h = grid
    lay = Layout(w, h, _sizes(gd))
    try:
        for name, x, y, rot, item in blocks:
            cfg = item_cfg(gd, item or "coal") if name in ("item-source", "liquid-source") else None
            lay.add(name, x, y, rot, cfg)
    except (ValueError, KeyError):
        return None
    return lay


def _used(blocks, gd) -> set:
    sizes = _sizes(gd)
    out = set()
    for name, x, y, _rot, _item in blocks:
        out |= _cells(sizes[name], x, y)
    return out


def _bounds(lay) -> Optional[tuple]:
    xs, ys = [], []
    for t in lay.tiles:
        if t.block in logistics.PORTS:
            continue
        for cx, cy in lay.cells(t.block, t.x, t.y):
            xs.append(cx)
            ys.append(cy)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def _ring(bb, taken, grid) -> List[tuple]:
    """工厂外接矩形外一圈的候选格（必须还在搜索网格内）。"""
    x0, y0, x1, y1 = bb
    out = []
    for x in range(x0 - 1, x1 + 2):
        for y in (y0 - 1, y1 + 1):
            if (x, y) not in taken:
                out.append((x, y))
    for y in range(y0, y1 + 1):
        for x in (x0 - 1, x1 + 1):
            if (x, y) not in taken:
                out.append((x, y))
    w, h = grid
    return [c for c in out if 0 <= c[0] < w and 0 <= c[1] < h]


def _adjacent(p, cells) -> bool:
    return any((p[0] + dx, p[1] + dy) in cells for dx, dy in DIRV.values())


def _rot_to(p, q) -> Optional[int]:
    d = (q[0] - p[0], q[1] - p[1])
    for rot, v in DIRV.items():
        if v == d:
            return rot
    return None


def _port_clusters(lay) -> int:
    """端口格（源/黑洞）按 4-邻接分组后的组数。"""
    cells = set()
    for t in lay.tiles:
        if t.block in logistics.PORTS:
            cells.update(lay.cells(t.block, t.x, t.y))
    n = 0
    while cells:
        n += 1
        stack = [cells.pop()]
        while stack:
            x, y = stack.pop()
            for p in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if p in cells:
                    cells.discard(p)
                    stack.append(p)
    return n


# ---------------------------------------------------------------- 评估
def _candidate_from_layout(lay, gd, plan, blocks, label, padded=False) -> Candidate:
    """已有 Layout → 候选（端口必须在外，速率由物流模型算）。"""
    ok, _msg = logistics.ports_outside(lay, gd)
    if not ok:
        raise ValueError("端口不在工厂外接矩形之外")
    est = logistics.estimate(lay, gd, plan)

    need_in = dict(plan.demand)
    # 产能 = 这张布局里生产 target 的机器的理论产出（不是 plan 的目标值：
    # 2 台石墨压机 = 1.333/s，比 1/s 目标多出来的富余是允许的）
    need_out = sum(
        gd.blocks[t.block].recipe.outputs_per_second.get(plan.target, 0.0)
        for t in lay.tiles
        if gd.blocks[t.block].recipe
        and plan.target in gd.blocks[t.block].recipe.outputs_per_second)
    in_flow = est["in_flow"]
    ok_need = (all(in_flow.get(item, 0.0) >= v - TOL for item, v in need_in.items())
               and est["out_flow"] >= need_out - TOL)

    port_cells = sum(len(lay.cells(t.block, t.x, t.y))
                     for t in lay.tiles if t.block in logistics.PORTS)
    bb = _bounds(lay) or (0, 0, 0, 0)
    return Candidate(
        blocks=tuple(blocks),
        label=label,
        ports=sum(1 for t in lay.tiles if t.block in logistics.PORTS),
        tiles=lay.stats()["tiles"] - port_cells,
        box=(bb[2] - bb[0] + 1) * (bb[3] - bb[1] + 1),
        rate=est["rate"],
        bottleneck=est["bottleneck"],
        in_flow=in_flow,
        out_flow=est["out_flow"],
        ok_need=ok_need,
        clusters=_port_clusters(lay),
        padded=padded,
    )


def evaluate(gd, plan, blocks, grid=GRID) -> Optional[Candidate]:
    """建 Layout → 端口必须在外 → 物流模型算速率 → 候选。不适用返回 None。"""
    lay = _make(gd, blocks, grid)
    if lay is None:
        return None
    try:
        return _candidate_from_layout(lay, gd, plan, blocks, "")
    except ValueError:
        return None


# ---------------------------------------------------------------- 枚举
def _machine_spec(plan, gd):
    """搜索目前只支持“一种机器、2 台、2×2、单输入”（石墨/硅都是这种形状）。"""
    if len(plan.order) != 1:
        raise ValueError("search 只支持单一机器类型，当前计划是 %s" % (plan.order,))
    name, n = plan.order[0]
    block = gd.block(name)
    if n != 2:
        raise ValueError("search 目前只枚举 2 台机器，当前需要 %d 台（%s）" % (n, name))
    if block.size != 2:
        raise ValueError("search 目前只支持 2×2 机器，%s 是 %d×%d" % (name, block.size, block.size))
    inputs = list(block.recipe.inputs_per_second) if block.recipe else []
    if len(inputs) != 1:
        raise ValueError("search 目前只支持单输入机器，%s 有输入 %s" % (name, inputs))
    return name, inputs[0]


def _arrangements(grid):
    out = []
    for gap in (0, 1, 2, 3):
        out.append(("h%d" % gap, [(1, 1), (3 + gap, 1)]))
        out.append(("v%d" % gap, [(1, 1), (1, 3 + gap)]))
    return out


def _bridges(gd, sizes, machines, grid):
    name = machines[0][0]
    a = _cells(sizes[name], *machines[0][1])
    b = _cells(sizes[name], *machines[1][1])
    w, h = grid
    out = []
    for x in range(w):
        for y in range(h):
            if (x, y) in a or (x, y) in b:
                continue
            if _adjacent((x, y), a) and _adjacent((x, y), b):
                out.append((x, y))
    return out


def _routes_to(blocks, gd, c, v, cand) -> List[list]:
    """把机器 c 的产出送到汇点 v：直接 1 条带子，或 带子→路由器→v（≤2 个元件）。"""
    taken = _used(blocks, gd)
    out: List[list] = []
    for b in cand:
        if b == v or b in taken:
            continue
        if not _adjacent(b, c):
            continue
        rot = _rot_to(b, v)
        if rot is not None:
            out.append([("conveyor", b[0], b[1], rot, None)])
        # 带子先送进路由器，路由器再贴 void（p-one 的合流形状）
        for r in cand:
            if r in (v, b) or r in taken:
                continue
            if not _adjacent(r, v) or not _adjacent(r, b):
                continue
            rot_r = _rot_to(b, r)
            if rot_r is None:
                continue
            out.append([("conveyor", b[0], b[1], rot_r, None),
                        ("router", r[0], r[1], 0, None)])
    return out


def _sink_options(gd, blocks, machines, grid) -> List[list]:
    """出口：每台机器各贴一个外部 void；或单个 void（其余机器用 1–2 个元件接力）。"""
    layb = _make(gd, blocks, grid)
    if layb is None:
        return []
    bb = _bounds(layb)
    sizes = _sizes(gd)
    name = machines[0][0]
    pcells = [_cells(sizes[name], *m[1]) for m in machines]
    cand = _ring(bb, _used(blocks, gd), grid)
    opts: List[list] = []

    # A) 每台机器各配一个外部 void
    per = [[v for v in cand if _adjacent(v, c)] for c in pcells]
    if all(per):
        for combo in itertools.product(*per):
            if len(set(combo)) == len(combo):
                opts.append([("item-void", v[0], v[1], 0, None) for v in combo])

    # B) 单个 void：贴机器就直连，不贴就用 带子 / 带子+路由器 接力
    for v in cand:
        per_r: List[List[list]] = []
        dead = False
        for c in pcells:
            if _adjacent(v, c):
                per_r.append([[]])
                continue
            routes = _routes_to(blocks, gd, c, v, cand)
            if not routes:
                dead = True
                break
            per_r.append(routes)
        if dead:
            continue
        for combo in itertools.product(*per_r):
            parts = [x for route in combo for x in route]
            cells_used = {(x[1], x[2]) for x in parts}
            if len(cells_used) != len(parts):
                continue
            opts.append([("item-void", v[0], v[1], 0, None)] + parts)
    return opts


def _source_options(gd, blocks, machines, grid, bridge=None) -> List[list]:
    """输入：单源经桥接元件；或每台机器各一个源。"""
    layb = _make(gd, blocks, grid)
    if layb is None:
        return []
    bb = _bounds(layb)
    sizes = _sizes(gd)
    name, item = machines[0][0], machines[0][2]
    cand = _ring(bb, _used(blocks, gd), grid)
    out = []
    if bridge is not None:
        bc = _cells(sizes[bridge[0]], bridge[1], bridge[2])
        for s in cand:
            if _adjacent(s, bc):
                out.append([("item-source", s[0], s[1], 0, item)])
        return out
    per = [[s for s in cand if _adjacent(s, _cells(sizes[name], *m[1]))] for m in machines]
    if all(per):
        for combo in itertools.product(*per):
            if len(set(combo)) == len(combo):
                out.append([("item-source", s[0], s[1], 0, item) for s in combo])
    return out


def enumerate_candidates(gd, plan, grid=GRID) -> List[Candidate]:
    """结构化枚举；结果顺序固定（确定性）。"""
    name, item = _machine_spec(plan, gd)
    sizes = _sizes(gd)
    rows: List[Candidate] = []
    seen: set = set()

    for label, positions in _arrangements(grid):
        machines = [(name, positions[0], item), (name, positions[1], item)]
        base = [(name, positions[0][0], positions[0][1], 0, None),
                (name, positions[1][0], positions[1][1], 0, None)]
        bodies = [(None, base)]
        for bc in _bridges(gd, sizes, machines, grid):
            for gate in BRIDGES:
                bodies.append(((gate, bc[0], bc[1]),
                               base + [(gate, bc[0], bc[1], 0, None)]))

        for bridge, body in bodies:
            for srcs in _source_options(gd, body, machines, grid, bridge):
                body2 = body + srcs
                for sinks in _sink_options(gd, body2, machines, grid):
                    blocks = tuple(body2 + sinks)
                    key = tuple(sorted(blocks))
                    if key in seen:
                        continue
                    seen.add(key)
                    cand = evaluate(gd, plan, blocks, grid)
                    if cand is None:
                        continue
                    rows.append(Candidate(
                        blocks=cand.blocks,
                        label="%s/%s/src%d/out%d" % (
                            label, bridge[0] if bridge else "-", len(srcs), len(sinks) - 1),
                        ports=cand.ports, tiles=cand.tiles, box=cand.box,
                        rate=cand.rate, bottleneck=cand.bottleneck,
                        in_flow=cand.in_flow, out_flow=cand.out_flow,
                        ok_need=cand.ok_need, clusters=cand.clusters))
    return rows


# ---------------------------------------------------------------- 模板候选
def _blocks_of(lay, gd, plan) -> List[tuple]:
    """Layout → (name,x,y,rot,item) 列表（item 只对 item-source 有意义）。"""
    item = next(iter(plan.demand), None)
    sizes = _sizes(gd)
    out = []
    for t in lay.tiles:
        rot = t.rotation
        if t.block == "item-source":
            out.append((t.block, t.x, t.y, rot, item))
        else:
            out.append((t.block, t.x, t.y, rot, None))
    assert sizes  # 只为保持签名一致的可读性
    return out


def template_candidates(gd, plan, canvas=(24, 24)) -> List[Candidate]:
    """把手写模板（cells/split/ported×3）也当成候选，补齐枚举够不到的几何。

    枚举只铺"机器外一圈"的端口，像 p-one（2 端口 / 12 格）这种"void 再往外退一格"的
    形状枚举不到；模板本来就是为这些形状写的，放进同一个池子一起比才公平。
    """
    from . import layout as layout_mod

    lay_tiles = {}
    combos = [("cells", {}), ("split", {}), ("split", {"gate": "overflow-gate"}),
              ("ported", {"merge": "both"}), ("ported", {"merge": "gate"}),
              ("ported", {"merge": "one"})]
    rows: List[Candidate] = []
    for name, kw in combos:
        try:
            lay = layout_mod.build_for(gd, plan, canvas=canvas, layout=name, **kw)
        except (ValueError, RuntimeError):
            continue
        lay.crop()
        blocks = tuple(_blocks_of(lay, gd, plan))
        # 新口径要求"输入和输出标记"都在工厂外，所以没有 item-void 的老模板（cells/split，
        # 产物装进厂内容器）不进池子——它们不是同一个问题的解
        if not any(b[0] == "item-void" for b in blocks):
            continue
        label = "template:%s%s" % (name, ":" + kw["merge"] if "merge" in kw else "")
        try:
            cand = _candidate_from_layout(lay, gd, plan, blocks, label, padded=True)
        except (ValueError, RuntimeError):
            continue
        lay_tiles[label] = cand
        rows.append(cand)
    assert lay_tiles is not None
    return rows


# ---------------------------------------------------------------- 选优
def _order(objective: str):
    if objective == "ports":
        return lambda c: (c.ports, c.tiles, c.box, -c.rate, c.label)
    if objective == "clusters":
        return lambda c: (c.clusters, c.ports, c.tiles, c.box, -c.rate, c.label)
    if objective == "tiles":
        return lambda c: (c.tiles, c.ports, c.box, -c.rate, c.label)
    if objective == "box":
        return lambda c: (c.box, c.tiles, c.ports, -c.rate, c.label)
    raise ValueError("objective 只能是 %s，收到 %r" % (OBJECTIVES, objective))


def pareto(cands: Sequence[Candidate]) -> List[Candidate]:
    """(ports, tiles, box) 三目标非支配集；同签名只留一张（顺序确定）。"""
    pts = [c for c in cands if c.ok_need]
    pts.sort(key=_order("ports"))
    front: List[Candidate] = []
    for c in pts:
        v = (c.ports, c.tiles, c.box)
        if any((o.ports <= v[0]) and (o.tiles <= v[1]) and (o.box <= v[2]) for o in front):
            continue
        front.append(c)
    return front


def pick(cands: Sequence[Candidate], objective: str = "ports") -> Optional[Candidate]:
    feasible = [c for c in cands if c.ok_need]
    return min(feasible, key=_order(objective)) if feasible else None


def search(gd, plan, grid=GRID, objective: str = "ports",
           canvas=(24, 24), with_templates: bool = True) -> SearchResult:
    """枚举 + 手写模板 → 过滤产能 → Pareto → 按 objective 选一个代表点。"""
    rows = enumerate_candidates(gd, plan, grid)
    if with_templates:
        rows = rows + template_candidates(gd, plan, canvas)
    front = pareto(rows)
    best = pick(rows, objective)
    return SearchResult(objective=objective, candidates=len(rows),
                        feasible=sum(1 for c in rows if c.ok_need),
                        front=front, best=best, grid=tuple(grid),
                        all_candidates=list(rows))


# ---------------------------------------------------------------- 落到 Layout
def to_layout(cand: Candidate, gd, canvas=(24, 24), margin: int = 2) -> Layout:
    """把候选变成画布坐标的 Layout。

    枚举候选在 9×7 搜索网格里 → 平移 `margin+1`；模板候选本来就在画布坐标里 → 不平移。
    """
    w, h = canvas
    lay = Layout(w, h, _sizes(gd),
                 name="mbo search ports=%d tiles=%d" % (cand.ports, cand.tiles),
                 description="enumerated by mbo.search (%s)" % cand.label)
    dx = dy = 0 if cand.padded else margin + 1
    for name, x, y, rot, item in cand.blocks:
        cfg = item_cfg(gd, item) if name in ("item-source", "liquid-source") and item else None
        try:
            lay.add(name, x + dx, y + dy, rot, cfg)
        except ValueError as e:
            raise ValueError("候选 %s 放不进 %dx%d 画布：%s" % (cand.label, w, h, e))
    return lay
