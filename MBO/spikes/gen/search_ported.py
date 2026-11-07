"""端口在外 / 物流限速 的蓝图搜索（脚本化推理；用户 m02384 + m02395）。

问题（石墨 1/s = 2 台 graphite-press）：

    工厂 = 所有非端口方块    端口 = item-source / item-void，必须完全在工厂外接矩形之外
    可达速率 = min(机器能力, 物流网络容量)   ← mbo/logistics.py 的最大流模型

脚本化：
1. **结构化枚举**：机器排布（水平/垂直，缝宽 0..3）× 输入方案（单源经门 / 每台一源）
   × 出口方案（1~2 个 void，必要时 ≤1 条带子合流），逐张建 Layout 并用最大流算速率；
2. **随机搜索**：随机撒机器 + 物流元件 + 端口，检查结构化枚举有没有漏解。

产物：按 (是否满足产能, 端口数, 工厂格数, 外接矩形面积, -速率) 排序的候选表。
"""

from __future__ import annotations

import itertools
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from mbo import logistics, production  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402
from mbo.model import DIRV, Layout, item_cfg  # noqa: E402

GD = GameData()
SIZES = {b.name: b.size for b in GD.blocks.values()}
PLAN = production.expand(GD, "graphite", 1.0, ["coal"])
NEED_COAL = 2 * 2 * (1.0 / 1.5)      # 2 台压机：4/3 coal/s
NEED_OUT = 2 * (1.0 / 1.5)           # 2 台压机：4/3 graphite/s
W, H = 9, 7
SQUARE = {(x, y) for x in range(W) for y in range(H)}


def cells_of(name, x, y):
    s = SIZES[name]
    ox, oy = x - (s - 1) // 2, y - (s - 1) // 2
    return {(ox + i, oy + j) for i in range(s) for j in range(s)}


def make(blocks):
    """按逻辑坐标建 Layout；放不下返回 None。"""
    lay = Layout(W, H, SIZES)
    try:
        for name, x, y, rot, item in blocks:
            if name == "item-source":
                lay.add(name, x, y, rot, item_cfg(GD, item or "coal"))
            else:
                lay.add(name, x, y, rot)
    except ValueError:
        return None
    return lay


def used_cells(blocks):
    out = set()
    for name, x, y, rot, item in blocks:
        out |= cells_of(name, x, y)
    return out


def no_overlap(blocks):
    seen = set()
    for name, x, y, rot, item in blocks:
        c = cells_of(name, x, y)
        if c & seen:
            return False
        seen |= c
    return True


def bounds(lay):
    xs, ys = [], []
    for t in lay.tiles:
        if t.block in logistics.PORTS:
            continue
        for cx, cy in lay.cells(t.block, t.x, t.y):
            xs.append(cx)
            ys.append(cy)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def ring(bb, taken):
    """工厂外接矩形外一圈候选格。"""
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
    return [c for c in out if c in SQUARE]


def adjacent(p, cells):
    return any((p[0] + dx, p[1] + dy) in cells for dx, dy in DIRV.values())


def rot_to(p, q):
    d = (q[0] - p[0], q[1] - p[1])
    for rot, v in DIRV.items():
        if v == d:
            return rot
    return None


def evaluate(blocks):
    if not no_overlap(blocks):
        return None
    lay = make(blocks)
    if lay is None:
        return None
    ok, msg = logistics.ports_outside(lay, GD)
    if not ok:
        return None
    est = logistics.estimate(lay, GD, PLAN)
    ports = sum(1 for t in lay.tiles if t.block in logistics.PORTS)
    port_cells = sum(len(lay.cells(t.block, t.x, t.y))
                     for t in lay.tiles if t.block in logistics.PORTS)
    bb = bounds(lay)
    return {
        "blocks": blocks, "lay": lay, "ports": ports,
        "tiles": lay.stats()["tiles"] - port_cells,
        "box": (bb[2] - bb[0] + 1) * (bb[3] - bb[1] + 1),
        "rate": est["rate"], "bottleneck": est["bottleneck"],
        "in_flow": est["in_flow"].get("coal", 0.0), "out_flow": est["out_flow"],
        "ok_need": (est["in_flow"].get("coal", 0.0) >= NEED_COAL - 1e-3
                    and est["out_flow"] >= NEED_OUT - 1e-3),
        "msg": msg,
    }


def key(r):
    return (0 if r["ok_need"] else 1, r["ports"], r["tiles"], r["box"], -r["rate"])


def sig(r):
    return (r["ports"], r["tiles"], r["box"], round(r["rate"], 3))


# ---------------------------------------------------------------- 枚举
def arrangements():
    out = []
    for gap in (0, 1, 2, 3):
        out.append(("h%d" % gap, [(1, 1), (1 + 2 + gap, 1)]))
        out.append(("v%d" % gap, [(1, 1), (1, 1 + 2 + gap)]))
    return out


def bridges(presses):
    a = cells_of("graphite-press", *presses[0])
    b = cells_of("graphite-press", *presses[1])
    out = []
    for (x, y) in SQUARE - (a | b):
        if adjacent((x, y), a) and adjacent((x, y), b):
            out.append((x, y))
    return out


def press_cells(presses):
    return [cells_of("graphite-press", *p) for p in presses]


def sink_options(presses, body):
    """出口：1~2 个 void；不贴机器的压机用 1 条带子把货送到 void。"""
    layb = make(body)
    if layb is None:
        return []
    bb = bounds(layb)
    taken = used_cells(body)
    cand = ring(bb, taken)
    pcells = press_cells(presses)
    opts = []

    # A) 每台压机各贴一个外部 void
    per = [[v for v in cand if adjacent(v, c)] for c in pcells]
    if all(per):
        for combo in itertools.product(*per):
            if combo[0] != combo[1]:
                opts.append([("item-void", v[0], v[1], 0, None) for v in combo])

    # B) 单个 void
    for v in cand:
        per = []
        for c in pcells:
            if adjacent(v, c):
                per.append([])
                continue
            belt = None
            for b in cand:
                if b == v or b in taken:
                    continue
                rot = rot_to(b, v)
                if rot is not None and adjacent(b, c):
                    belt = [("conveyor", b[0], b[1], rot, None)]
                    break
            per.append(belt)
        if any(p is None for p in per):
            continue
        belts = [b for bl in per for b in bl]
        bcells = {(b[1], b[2]) for b in belts}
        if len(bcells) != len(belts):
            continue
        opts.append([("item-void", v[0], v[1], 0, None)] + belts)
    return opts


def source_options(presses, body, bridge=None):
    """输入方案：(a) 单源经桥接元件；(b) 每台压机各一个源。"""
    layb = make(body)
    if layb is None:
        return []
    bb = bounds(layb)
    taken = used_cells(body)
    cand = ring(bb, taken)
    out = []
    if bridge is not None:
        bc = cells_of(bridge[0], bridge[1], bridge[2])
        for s in cand:
            if adjacent(s, bc):
                out.append([("item-source", s[0], s[1], 0, "coal")])
    else:
        per = [[s for s in cand if adjacent(s, c)] for c in press_cells(presses)]
        if all(per):
            for combo in itertools.product(*per):
                if combo[0] != combo[1]:
                    out.append([("item-source", s[0], s[1], 0, "coal") for s in combo])
    return out


def structured():
    rows = []
    for label, presses in arrangements():
        base = [("graphite-press", presses[0][0], presses[0][1], 0, None),
                ("graphite-press", presses[1][0], presses[1][1], 0, None)]
        bodies = [(None, base)]
        for bc in bridges(presses):
            for gate in ("underflow-gate", "overflow-gate", "router"):
                bodies.append(((gate, bc[0], bc[1]), base + [(gate, bc[0], bc[1], 0, None)]))
        for bridge, body in bodies:
            for srcs in source_options(presses, body, bridge):
                body2 = body + srcs
                for sinks in sink_options(presses, body2):
                    r = evaluate(body2 + sinks)
                    if r:
                        r["label"] = "%s/%s/src%d/out%d" % (
                            label, bridge[0] if bridge else "-", len(srcs), len(sinks) - 1)
                        rows.append(r)
    return rows


def random_search(n=3000, seed=7):
    rnd = random.Random(seed)
    found = []
    for _ in range(n):
        gx, gy = rnd.randint(1, W - 5), rnd.randint(1, H - 5)
        horiz = rnd.random() < 0.5
        gap = rnd.randint(0, 3)
        p0 = (gx, gy)
        p1 = (gx + 2 + gap, gy) if horiz else (gx, gy + 2 + gap)
        body = [("graphite-press", p0[0], p0[1], 0, None),
                ("graphite-press", p1[0], p1[1], 0, None)]
        if make(body) is None:
            continue
        for _k in range(rnd.randint(0, 2)):
            lay_body = make(body)
            if lay_body is None:
                break
            cand = ring(bounds(lay_body), used_cells(body))
            if not cand:
                break
            c = rnd.choice(cand)
            trial = body + [(rnd.choice(("conveyor", "underflow-gate", "router")),
                             c[0], c[1], rnd.choice((0, 1, 2, 3)), None)]
            if make(trial) is not None:
                body = trial
        lay_body = make(body)
        if lay_body is None:
            continue
        for srcs in source_options((p0, p1), body):
            body2 = body + srcs
            for sinks in sink_options((p0, p1), body2):
                r = evaluate(body2 + sinks)
                if r and r["ok_need"]:
                    r["label"] = "random"
                    found.append(r)
    return found


def main():
    rows = [r for r in structured() if r]
    print("结构化候选 %d 张（满足产能 %d 张）" % (len(rows), sum(1 for r in rows if r["ok_need"])))
    best = {}
    for r in sorted(rows, key=key):
        if r["ok_need"]:
            best.setdefault(sig(r), r)
    for s, r in sorted(best.items(), key=lambda kv: key(kv[1]))[:10]:
        print("  ports=%d tiles=%2d box=%2d rate=%.4f bn=%-8s | %s"
              % (r["ports"], r["tiles"], r["box"], r["rate"], r["bottleneck"], r["label"]))
    rr = random_search()
    print("随机搜索可行 %d 张（最佳 %s）" % (len(rr), min(
        (r["ports"], r["tiles"], r["box"]) for r in rr) if rr else "-"))


if __name__ == "__main__":
    main()
