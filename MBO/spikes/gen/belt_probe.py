# -*- coding: utf-8 -*-
"""belt_probe.py -- 传送带真实吞吐实测（补 docs/13 未验证项）。

问题（生成器必须知道的三件事）：
  Q1 一条传送带能搬多少 items/s？（决定产线是否需要并行带）
  Q2 带长是否影响吞吐（只影响延迟，还是也影响容量）？
  Q3 rotation 0/1/2/3 到底指向哪一侧？（layout 生成器按方向铺带子要靠它）

做法：一个世界里铺 8 组独立 rig，全部用 item-source(coal) 供料，
末端接 2x2 container 作为计数 sink，真 60Hz 跑 1200 tick，每秒扫一次
container 的 coal 数量 + 每条带上的 item 数。

  A 直连：source -> container（测 source 自身 dump 速率上限）
  B/C/D 带长 3/8/16（N 条 conveyor 串联，rot=0）
  E/F/G/H rot = 0/1/2/3 单条带（测方向语义）

用法：python -X utf8 MBO\\spikes\\gen\\belt_probe.py [--ticks 1200]
产物：MBO/spikes/gen/out/belt.json
"""
from __future__ import annotations

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

# ---------------------------------------------------------------- rig 定义
# 全部坐标是 schematic 局部坐标；container 记 2x2 的中心格（= origin）。
RIGS = {
    "A_direct":     {"source": (10, 10), "belts": [], "sink": (11, 10)},
    "B_belt3":      {"source": (10, 20), "belts": [(11 + i, 20, 0) for i in range(3)], "sink": (14, 20)},
    "C_belt8":      {"source": (10, 30), "belts": [(11 + i, 30, 0) for i in range(8)], "sink": (19, 30)},
    "D_belt16":     {"source": (10, 40), "belts": [(11 + i, 40, 0) for i in range(16)], "sink": (27, 40)},
    "E_rot0_east":  {"source": (60, 10), "belts": [(61, 10, 0)], "sink": (62, 10)},
    "F_rot1_south": {"source": (60, 20), "belts": [(60, 21, 1)], "sink": (60, 22)},
    "G_rot2_west":  {"source": (60, 30), "belts": [(59, 30, 2)], "sink": (57, 30)},
    "H_rot3_north": {"source": (60, 40), "belts": [(60, 39, 3)], "sink": (60, 37)},
}
W, H = 120, 70
PX, PY = 64, 36                      # place 锚点（蓝图中心）；ox = PX - W//2

JS_SAMPLE = r"""
(function(){
var out = [];
var want = %(want)s;
for(var i = 0; i < want.length; i++){
  var w = want[i], t = Vars.world.tile(w[1], w[2]);
  var b = (t == null) ? null : t.build;
  if(b == null || b.items == null){ out.push(w[0] + "=NULL"); continue; }
  var it = Vars.content.items().get(5);          /* coal */
  out.push(w[0] + "=" + Math.round(b.items.get(it) * 100) / 100);
}
print("SAMPLE\t" + Vars.state.tick + "\t" + out.join(" ") + "\t" + (Vars.state.tick / 60.0));
})();
"""


def build():
    tiles = []
    for name, r in RIGS.items():
        sx, sy = r["source"]
        tiles.append(msch.Stile("item-source", sx, sy, 0,
                                {"__content__": "item", "id": 5}))
        for (x, y, rot) in r["belts"]:
            tiles.append(msch.Stile("conveyor", x, y, rot))
        cx, cy = r["sink"]
        tiles.append(msch.Stile("container", cx, cy, 0))
    return msch.Schematic(W, H, {"name": "mbo-belt-probe"}, tiles,
                          version=msch.CURRENT_VERSION)


def main():
    ticks = 1200
    if "--ticks" in sys.argv:
        ticks = int(sys.argv[sys.argv.index("--ticks") + 1])

    sch = build()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "belt.msch")
    with open(path, "wb") as fh:
        fh.write(sc.build_schematic_ext(sch))

    # 采样点：容器 + 首条带（看占用）
    want = []
    ox, oy = PX - W // 2, PY - H // 2
    for name, r in RIGS.items():
        cx, cy = r["sink"]
        want.append([name + ".sink", cx + ox, cy + oy])
        if r["belts"]:
            bx, by, _ = r["belts"][0]
            want.append([name + ".belt0", bx + ox, by + oy])

    t0 = time.time()
    srv = ep.Server(name="belt")
    try:
        time.sleep(13.0)                       # 等服务器换图（docs/13 坑①）
        srv.js(ep.BP_PREP_JS % {"n": 128})
        b64 = ep.load_schematic_b64(path)
        print(srv.js(ep.BP_PLACE_JS % {"b64": b64, "i": 0, "px": PX, "py": PY})[:300])
        srv.js(ep.CLOCK_PLAYING_JS)

        samples = []
        last = -1
        deadline = time.time() + ticks / 60.0 + 40
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
                vals[k] = None if v == "NULL" else float(v)
            samples.append({"tick": tick, "t": float(p[3]), "v": vals})
            if tick >= ticks:
                break
            time.sleep(0.1)
    finally:
        try:
            srv.close()
        except Exception as e:                  # noqa: BLE001
            print("close warn:", e)

    res = {"msch": os.path.relpath(path, ROOT).replace("\\", "/"),
           "ticks_target": ticks, "wall_s": round(time.time() - t0, 1),
           "samples": samples}
    with open(os.path.join(OUT, "belt.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)

    # ---------------- 分析
    print("\n=== 吞吐（丢弃前 300 tick 稳定后线性回归 / 首末差）===")
    for name, r in RIGS.items():
        key = name + ".sink"
        pts = [(s["t"], s["v"][key]) for s in samples
               if s["v"].get(key) is not None]
        if len(pts) < 3:
            print(f"{name:14s} 无数据")
            continue
        # 取从第一个非零之后 >=300 tick 的窗口
        t_start = None
        for t, v in pts:
            if v > 0:
                t_start = t
                break
        if t_start is None:
            print(f"{name:14s} 一个都没送到（方向错？）  samples={pts[:3]}")
            continue
        win = [(t, v) for t, v in pts if t >= t_start]
        dt = win[-1][0] - win[0][0]
        dv = win[-1][1] - win[0][1]
        rate = dv / dt if dt > 0 else float("nan")
        belt0 = [s["v"].get(name + ".belt0") for s in samples]
        belt0 = [b for b in belt0 if b is not None]
        print(f"{name:14s} 起始t={t_start:6.1f}s Δ={dv:5.0f}/{dt:5.2f}s → "
              f"{rate:5.2f} items/s   belt0占用max={max(belt0) if belt0 else 'n/a'}")

    print("\njson:", os.path.join(OUT, "belt.json"))


if __name__ == "__main__":
    main()
