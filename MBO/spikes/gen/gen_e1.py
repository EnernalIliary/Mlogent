# -*- coding: utf-8 -*-
"""gen_e1.py -- E1 最小生成：24x24 画布上从零生成「硅 3/s」产线里并在真引擎验证。

这是 docs/03 里 MVP Gate 的第一次真跑，也是 docs/13 未验证清单的两项补齐：
  Q1 传送带供料（不再是 item-source 直贴机器）
  Q2 电力布线器（消费方块 -> 选 node 位置 -> 写 links -> 校验连通）

产线结构（两条对称支线，各 1 台 silicon-smelter）：
  支线 A: coal-src(2,15) -> belt(3,15)->(4,15) -> 炉A(5,14)[每个周期 1 煤 + 2 沙]
          sand-src(2,14) -> belt(3,14)->(4,14) -> 炉A
          炉A -> container(6,16)
  支线 B: 同构，y 平移 -5
  电力:  node(5,16) <-> node(5,11) <-> power-source(2,12)

链路约束（docs/13 R1–R7）：坐标=中心格；带 rot 0/1/2/3 = 东/南/西/北（实测）；
node 必须与 consumer 正交相邻；links 必须显式写 Point2[] 相对偏移；重叠必须自校验。

用法：
    python -X utf8 MBO\\spikes\\gen\\gen_e1.py [--ticks 1800] [--skip-engine]
产物：MBO/spikes/gen/out/{e1_silicon.msch, e1_silicon.b64.txt, e1_metrics.json}
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SPIKES = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(SPIKES))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(SPIKES, "sim"))
sys.path.insert(0, os.path.join(SPIKES, "bp"))

import msch                      # noqa: E402
import scan_corpus as sc         # noqa: E402
import engine_probe as ep        # noqa: E402

OUT = os.path.join(HERE, "out")
GAMEDATA = os.path.join(SPIKES, "data", "gamedata.json")
ITEM_ID = {"copper": 0, "lead": 1, "metaglass": 2, "graphite": 3, "sand": 4, "coal": 5,
           "titanium": 6, "thorium": 7, "scrap": 8, "silicon": 9, "plastanium": 10,
           "phase-fabric": 11, "surge-alloy": 12, "spore-pod": 13, "blast-compound": 14,
           "pyratite": 15}

ROT = {"E": 0, "S": 1, "W": 2, "N": 3}
DIRV = {0: (1, 0), 1: (0, -1), 2: (-1, 0), 3: (0, 1)}     # 实测：0东 1南 2西 3北

BELT_RATE = 4.9      # items/s，docs/14 实测
NODE_RANGE = 5       # 保守（jar laserRange=6，实测相邻即可，取 5 留余量）


def load_sizes():
    with open(GAMEDATA, encoding="utf-8") as fh:
        g = json.load(fh)
    return {b["name"]: b["size"] for b in g["blocks"]}


class Layout:
    """带占用校验的蓝图构造器（R1/R7：中心格坐标 + 重叠即报错）。"""

    def __init__(self, w, h, sizes, name="untitled"):
        self.w, self.h, self.sizes, self.name = w, h, sizes, name
        self.occ = {}
        self.tiles = []

    # ---------------- 几何
    def origin(self, block, x, y):
        s = self.sizes[block]
        return x - (s - 1) // 2, y - (s - 1) // 2

    def cells(self, block, x, y):
        s = self.sizes[block]
        ox, oy = self.origin(block, x, y)
        return [(ox + i, oy + j) for i in range(s) for j in range(s)]

    def free(self, block, x, y):
        for cx, cy in self.cells(block, x, y):
            if not (0 <= cx < self.w and 0 <= cy < self.h):
                return False
            if (cx, cy) in self.occ:
                return False
        return True

    def add(self, block, x, y, rot=0, config=None):
        if block not in self.sizes:
            raise KeyError("unknown block " + block)
        if not self.free(block, x, y):
            raise ValueError("overlap/out-of-bounds: %s@(%d,%d)" % (block, x, y))
        for c in self.cells(block, x, y):
            self.occ[c] = block
        self.tiles.append(msch.Stile(block, x, y, rot, config))
        return (x, y)

    # ---------------- 查询
    def has(self, x, y):
        return (x, y) in self.occ

    def set_config(self, pos, config):
        for t in self.tiles:
            if (t.x, t.y) == pos:
                t.config = config
                return t
        raise KeyError("no tile at %s" % (pos,))

    def consumers(self):
        return [(t.block, t.x, t.y) for t in self.tiles if t.block.endswith("-smelter")]

    def to_schematic(self):
        return msch.Schematic(self.w, self.h, {"name": self.name}, self.tiles,
                              version=msch.CURRENT_VERSION)


def item_cfg(name):
    return {"__content__": "item", "id": ITEM_ID[name]}


def pts(seq):
    return sc.TaggedList([tuple(p) for p in seq], tag=8)


# ---------------------------------------------------------------- 电力布线器
def orth_adjacent(cells_a, cells_b):
    sa = set(cells_a)
    for (bx, by) in cells_b:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (bx + dx, by + dy) in sa:
                return True
    return False


def route_power(lay, anchor=(0, 0), verbose=True):
    """给 lay 里所有耗电方块布线：选 node 位置 -> 连链 -> 接 source -> 写 config。

    规则（docs/13）：
      R3 links 必须显式写 relative Point2[]
      R4 node 必须与 consumer 正交相邻
      R5 source 与 node 之间也要显式 config
    返回 {"nodes": [...], "source": (x,y), "components": 1}，布线失败抛异常。
    """
    cons = lay.consumers()
    nodes = []

    # 1. 每个 consumer 至少一个相邻 node
    for block, cx, cy in cons:
        cc = lay.cells(block, cx, cy)
        if any(orth_adjacent(lay.cells("power-node", nx, ny), cc) for nx, ny in nodes):
            continue
        cands = []
        for (x, y) in cc:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                px, py = x + dx, y + dy
                if lay.free("power-node", px, py):
                    cands.append((abs(px - anchor[0]) + abs(py - anchor[1]), px, py))
        if not cands:
            raise RuntimeError("no free cell adjacent to %s@(%d,%d)" % (block, cx, cy))
        cands.sort()
        _, px, py = cands[0]
        lay.add("power-node", px, py)
        nodes.append((px, py))
        if verbose:
            print("  node@(%d,%d) 贴 %s@(%d,%d)" % (px, py, block, cx, cy))

    # 2. 连通：并查集 + 就近连线；跨度超过 NODE_RANGE 时插中继 node
    def dist(a, b):
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

    links = {n: set() for n in nodes}
    while True:
        comp = _components(nodes, links)
        if len(comp) == 1:
            break
        best = None
        for i in range(len(comp)):
            for j in range(i + 1, len(comp)):
                for a in comp[i]:
                    for b in comp[j]:
                        d = dist(a, b)
                        if best is None or d < best[0]:
                            best = (d, a, b)
        if best is None:
            raise RuntimeError("cannot connect power nodes")
        d, a, b = best
        if d > NODE_RANGE:
            # 在中点方向插一个中继 node（沿切比雪夫最长轴走一半）
            mx = a[0] + (b[0] - a[0]) * (NODE_RANGE // 2) // max(1, d) * d // max(1, d)
            mx = a[0] + int(round((b[0] - a[0]) * NODE_RANGE / d / 2)) * 2
            my = a[1] + int(round((b[1] - a[1]) * NODE_RANGE / d / 2)) * 2
            placed = False
            for r in range(0, 4):
                for sx in (-1, 0, 1):
                    for sy in (-1, 0, 1):
                        px, py = mx + sx * r, my + sy * r
                        if lay.free("power-node", px, py):
                            lay.add("power-node", px, py)
                            nodes.append((px, py))
                            links[(px, py)] = set()
                            placed = True
                            break
                    if placed:
                        break
                if placed:
                    break
            if not placed:
                raise RuntimeError("cannot place relay node")
            continue
        links[a].add(b)
        links[b].add(a)

    # 3. source：放在离 anchor 近、且能连到某个 node 的空位
    src = None
    cands = []
    for x in range(lay.w):
        for y in range(lay.h):
            if not lay.free("power-source", x, y):
                continue
            if lay.has(x, y):
                continue
            dmin = min(dist((x, y), n) for n in nodes)
            if dmin <= NODE_RANGE:
                cands.append((dmin + abs(x - anchor[0]) + abs(y - anchor[1]), x, y, dmin))
    if not cands:
        raise RuntimeError("cannot place power-source within range of a node")
    cands.sort()
    _, sx, sy, _ = cands[0]
    lay.add("power-source", sx, sy)
    src = (sx, sy)
    if verbose:
        print("  source@(%d,%d)" % src)

    # 4. 写 config（对称、相对偏移）
    def offsets(me, others):
        return [(o[0] - me[0], o[1] - me[1]) for o in others]

    for n in nodes:
        lay.set_config(n, pts(offsets(n, sorted(links[n]))))
    nearest = min(nodes, key=lambda n: dist(n, src))
    links[nearest].add(src)
    lay.set_config(src, pts(offsets(src, [nearest])))
    # node 侧补 source
    lay.set_config(nearest, pts(offsets(nearest, sorted(links[nearest]))))

    comp = _components(nodes + [src], {k: set(v) for k, v in links.items()})
    return {"nodes": nodes, "source": src, "components": len(comp),
            "links": {str(k): sorted(str(x) for x in v) for k, v in links.items() if v}}


def _components(nodes, links):
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in [(a, b) for a, bs in links.items() for b in bs]:
        if a in parent and b in parent:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
    groups = {}
    for n in nodes:
        groups.setdefault(find(n), []).append(n)
    return list(groups.values())


# ---------------------------------------------------------------- 数值预测
def predict(lay):
    """按 gamedata 的 recipe 预测各方块产能与输入需求（L2 最小版）。"""
    with open(GAMEDATA, encoding="utf-8") as fh:
        g = json.load(fh)
    blocks = {b["name"]: b for b in g["blocks"]}
    out = {"buildings": {}, "demand": {}, "power_need": 0.0,
           "power_supply": 0.0, "sandbox_power": False, "yield": 0.0}
    for t in lay.tiles:
        b = blocks.get(t.block)
        if b is None:
            continue
        out["buildings"][t.block] = out["buildings"].get(t.block, 0) + 1
        r = b.get("recipe") or {}
        if r.get("craftTime", 0) > 0:
            cps = 60.0 / r["craftTime"]
            for cons in r.get("inputs") or []:
                for it in cons.get("items") or []:
                    out["demand"][it["name"]] = out["demand"].get(it["name"], 0) + cps * it["amount"]
            for it in r.get("outputItems") or []:
                if it["name"] == "silicon":
                    out["yield"] += cps * it["amount"]
        p = b.get("power") or {}
        usage = p.get("usagePerSecond")
        if usage:
            out["power_need"] += usage
        prod = p.get("productionPerSecond")
        if prod:
            if t.block == "power-source":
                # 沙盒电源的 productionPerSecond 是 999999.96，按“无限”处理，不混进净功率
                out["sandbox_power"] = True
            else:
                out["power_supply"] += prod
    out["power_net"] = out["power_need"] - out["power_supply"]
    return out


# ---------------------------------------------------------------- 静态校验
def static_check(lay):
    """R1/R4/R7 + 端口联通性 + 电力连通块数。"""
    errs = []

    # 重叠（Layout.add 已拦，这里再按 footprint 复核一遍）
    seen = {}
    for t in lay.tiles:
        for c in lay.cells(t.block, t.x, t.y):
            if c in seen:
                errs.append("overlap at %s: %s vs %s" % (c, seen[c], t.block))
            seen[c] = t.block

    # 带子必须指向真实方块（否则白铺）
    for t in lay.tiles:
        if t.block != "conveyor":
            continue
        dx, dy = DIRV[t.rotation]
        tip = (t.x + dx, t.y + dy)
        if not lay.has(*tip):
            errs.append("conveyor@(%d,%d) 指向空位 %s" % (t.x, t.y, tip))

    # 每台耗电机器必须有相邻 node
    nodes = [(t.x, t.y) for t in lay.tiles if t.block == "power-node"]
    for block, cx, cy in lay.consumers():
        cc = lay.cells(block, cx, cy)
        if not any(orth_adjacent(lay.cells("power-node", nx, ny), cc) for nx, ny in nodes):
            errs.append("%s@(%d,%d) 没有相邻 power-node" % (block, cx, cy))

    # 电力连通性：按 config 里的相对偏移重建图
    adj = {}
    pos = {}
    for t in lay.tiles:
        if t.block in ("power-node", "power-source"):
            pos[(t.x, t.y)] = t.block
            adj[(t.x, t.y)] = []
    for (x, y), _ in pos.items():
        t = next(tt for tt in lay.tiles if tt.block in ("power-node", "power-source")
                 and tt.x == x and tt.y == y)
        cfg = t.config
        if not isinstance(cfg, sc.TaggedList) or not cfg:
            errs.append("power block @(%d,%d) 没有 links config（R3）" % (x, y))
            continue
        for (dx, dy) in cfg:
            other = (x + dx, y + dy)
            if other not in pos:
                errs.append("link %s -> %s 指向非电力方块" % ((x, y), other))
            elif other not in adj[(x, y)]:
                adj[(x, y)].append(other)
                adj.setdefault(other, []).append((x, y))
    comps = _components(list(pos.keys()), {k: set(v) for k, v in adj.items()})
    if len(comps) != 1:
        errs.append("电力连通块数 = %d（应为 1）" % len(comps))
    return errs, {"power_blocks": len(pos), "components": len(comps)}


# ---------------------------------------------------------------- 引擎验证
JS_SAMPLE = r"""
(function(){
var out = [];
var want = %(want)s;
for(var i = 0; i < want.length; i++){
  var w = want[i], t = Vars.world.tile(w[1], w[2]), b = (t == null) ? null : t.build;
  if(b == null){ out.push(w[0] + "=NULL"); continue; }
  if(b.items == null){ out.push(w[0] + "=NOITEMS"); continue; }
  var tot = 0, I = Vars.content.items();
  for(var j = 0; j < I.size; j++){ tot += b.items.get(I.get(j)); }
  var sil = Math.round(b.items.get(Vars.content.item(9)) * 100) / 100;
  out.push(w[0] + "=" + Math.round(tot) + "/" + sil + "/" + Math.round(b.efficiency*100)/100
           + "/" + Math.round(b.progress*100)/100);
}
print("SAMPLE\t" + Vars.state.tick + "\t" + out.join(" "));
})();
"""


def engine_verify(path, lay, ticks=1800):
    ox, oy = PX - lay.w // 2, PY - lay.h // 2
    # 2x2 方块：origin == 中心格（(size-1)//2 = 0）；3x3 才偏 1 格。
    want = []
    for t in lay.tiles:
        if t.block in ("container", "silicon-smelter"):
            x0, y0 = lay.origin(t.block, t.x, t.y)
            tag = "c" if t.block == "container" else "s"
            want.append([tag + "%d_%d" % (t.x, t.y), x0 + ox, y0 + oy])

    t0 = time.time()
    srv = ep.Server(name="e1")
    samples = []
    try:
        time.sleep(13.0)
        srv.js(ep.BP_PREP_JS % {"n": 128})
        b64 = ep.load_schematic_b64(path)
        print(srv.js(ep.BP_PLACE_JS % {"b64": b64, "i": 0, "px": PX, "py": PY})[:300])
        srv.js(ep.CLOCK_PLAYING_JS)
        last = -1.0
        deadline = time.time() + ticks / 60.0 + 60
        while time.time() < deadline:
            lines = srv.js(JS_SAMPLE % {"want": json.dumps(want)})
            line = next((ln for ln in lines if ln.startswith("SAMPLE")), None)
            if not line:
                time.sleep(0.05)
                continue
            p = line.split("\t")
            tick = float(p[1])
            if tick <= last:
                break
            last = tick
            vals = {}
            for kv in p[2].split():
                k, v = kv.split("=")
                if v in ("NULL", "NOITEMS"):
                    vals[k] = None
                else:
                    a = v.split("/")
                    vals[k] = {"total": float(a[0]), "sil": float(a[1]),
                               "eff": float(a[2]), "prog": float(a[3])}
            samples.append({"tick": tick, "v": vals})
            if tick >= ticks:
                break
            time.sleep(0.3)
    finally:
        try:
            srv.close()
        except Exception as e:                    # noqa: BLE001
            print("close warn:", e)
    return samples, round(time.time() - t0, 1)


PX, PY = 64, 64


# ---------------------------------------------------------------- 主流程
def build_e1():
    sizes = load_sizes()
    lay = Layout(24, 24, sizes, "mbo-e1-silicon-3ps")

    # 支线：y0 = 炉底行
    for tag, y0 in (("A", 14), ("B", 9)):
        lay.add("item-source", 2, y0 + 1, 0, item_cfg("coal"))
        lay.add("conveyor", 3, y0 + 1, ROT["E"])
        lay.add("conveyor", 4, y0 + 1, ROT["E"])
        lay.add("item-source", 2, y0, 0, item_cfg("sand"))
        lay.add("conveyor", 3, y0, ROT["E"])
        lay.add("conveyor", 4, y0, ROT["E"])
        lay.add("silicon-smelter", 5, y0, 0)                     # 占 5..6 x y0..y0+1
        lay.add("container", 6, y0 + 2, 0)                       # 占 6..7 x y0+2..y0+3

    info = route_power(lay, anchor=(2, 12))
    print("  电力:", info)
    return lay, info


def main():
    ticks = 1800
    if "--ticks" in sys.argv:
        ticks = int(sys.argv[sys.argv.index("--ticks") + 1])
    skip = "--skip-engine" in sys.argv

    lay, pinfo = build_e1()
    errs, meta = static_check(lay)
    pred = predict(lay)
    print("\n静态校验:", "OK" if not errs else errs)
    print("预测: 产量 %.2f/s  输入需求 %s  耗电需求 %.0f/s（电源 %s）  格数 %d"
          % (pred["yield"], {k: round(v, 2) for k, v in pred["demand"].items()},
             pred["power_need"],
             "沙盒无限" if pred["sandbox_power"] else "%.0f/s" % pred["power_supply"],
             len(lay.occ)))
    if errs:
        print("!! 静态校验失败，停止")
        return 1

    sch = lay.to_schematic()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "e1_silicon.msch")
    raw = sc.build_schematic_ext(sch)
    with open(path, "wb") as fh:
        fh.write(raw)
    with open(os.path.join(OUT, "e1_silicon.b64.txt"), "w", encoding="ascii") as fh:
        fh.write(base64.b64encode(raw).decode("ascii"))
    print("写出:", path, len(raw), "bytes；粘贴码", len(base64.b64encode(raw)), "字符")

    metrics = {"blueprint": os.path.relpath(path, ROOT).replace("\\", "/"),
               "bytes": len(raw), "canvas": [lay.w, lay.h], "tiles": len(lay.tiles),
               "occupied_cells": len(lay.occ), "predicted_yield": pred["yield"],
               "predicted_demand": pred["demand"],
               "predicted_power_need": pred["power_need"],
               "predicted_power_supply": None if pred["sandbox_power"] else pred["power_supply"],
               "power": pinfo, "static": meta, "belt_rate": BELT_RATE}

    if not skip:
        samples, wall = engine_verify(path, lay, ticks)
        metrics["ticks"] = ticks
        metrics["wall_s"] = wall
        metrics["samples_n"] = len(samples)
        # 产量：两台炉各自 container 的 silicon 之和，窗口 300..ticks
        series = []
        for s in samples:
            tot = 0.0
            for k, v in s["v"].items():
                if k.startswith("c") and v:
                    tot += v["sil"]
            series.append((s["tick"], tot))
        win = [(t, v) for t, v in series if t >= 300]
        if len(win) >= 2:
            rate = (win[-1][1] - win[0][1]) / ((win[-1][0] - win[0][0]) / 60.0)
        else:
            rate = float("nan")
        effs = {}
        last = samples[-1]["v"] if samples else {}
        for k, v in last.items():
            if k.startswith("s") and v:
                effs[k] = {"eff": v["eff"], "prog": v["prog"],
                           "items": v["total"]}
        metrics["measured_yield"] = rate
        metrics["relative_error"] = (rate - pred["yield"]) / pred["yield"]
        metrics["smelters_last"] = effs
        print("\n=== 真机 ===")
        print("窗口 %d..%d tick：%s" % (win[0][0] if win else -1, win[-1][0] if win else -1,
              "%.2f 硅/s（预测 %.2f，误差 %+.1f%%）" % (rate, pred["yield"],
              100 * (rate - pred["yield"]) / pred["yield"]) if win else "无数据"))
        for k, v in effs.items():
            print("  %s eff=%.2f prog=%.2f 库存=%.0f" % (k, v["eff"], v["prog"], v["items"]))
        print("墙钟 %.1fs" % wall)

    with open(os.path.join(OUT, "e1_metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, ensure_ascii=False, indent=1)
    print("\nmetrics:", os.path.join(OUT, "e1_metrics.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
