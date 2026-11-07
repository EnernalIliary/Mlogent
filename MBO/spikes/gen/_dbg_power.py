# -*- coding: utf-8 -*-
"""_dbg_power.py -- 决定性问题：consumer（硅炉）怎么才能拿到电？

三个变体，同世界不同位置，跑 900 tick，看 eff 与产量：
  A 节点紧贴硅炉 + 显式 config（node->source, source->node）
  B 节点离硅炉 3 格 + 显式 config
  C 节点紧贴硅炉 + 全空 config（期望：孤岛、无电）

这个问题的答案决定生成器"电力布线"这一步的硬约束，是 E1 的前置。
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SPIKES = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(SPIKES, "sim"))
sys.path.insert(0, os.path.join(SPIKES, "bp"))

import msch  # noqa: E402
import scan_corpus as sc  # noqa: E402
import engine_probe as ep  # noqa: E402

from gen_trust import JS_SCAN, item, pts, parse_scan, sum_item, T, mk, OUT  # noqa: E402


def rig(node_dy: int, wired: bool, name: str, h: int = 9):
    """node 在 (2, 1+node_dy)，source 在其上方 2 格。"""
    node_y = 1 + node_dy
    src_y = node_y + 2
    tiles = [
        T("item-source", 0, 1, 0, item("coal")),
        T("item-source", 0, 2, 0, item("sand")),
        T("silicon-smelter", 1, 1, 0),
        T("container", 3, 1, 0),
        T("power-node", 2, node_y, 0, pts([(0, 2)]) if wired else None),
        T("power-source", 2, src_y, 0, pts([(0, -2)]) if wired else None),
    ]
    return mk(8, h, tiles, name)


def main():
    variants = {"A_node_adjacent": rig(2, True, "A"),
                "B_node_3away": rig(4, True, "B", h=10),
                "C_no_config": rig(2, False, "C")}
    b64s = {}
    for k, sch in variants.items():
        os.makedirs(OUT, exist_ok=True)
        p = os.path.join(OUT, "pw_%s.msch" % k.split("_")[0])
        with open(p, "wb") as fh:
            fh.write(sc.build_schematic_ext(sch))
        b64s[k] = base64.b64encode(open(p, "rb").read()).decode("ascii")

    srv = ep.Server(ep.JAR, ep.JAVA, 128)
    try:
        time.sleep(13.0)
        srv.js(ep.BP_PREP_JS % {"n": 128})
        spots = {"A_node_adjacent": (20, 20), "B_node_3away": (40, 20), "C_no_config": (60, 20)}
        for i, (k, (px, py)) in enumerate(spots.items()):
            ln = srv.js(ep.BP_PLACE_JS % {"b64": b64s[k], "i": i, "px": px, "py": py})
            print("PLACE", k, ln[-1][:160])
        print("T0", srv.js(JS_SCAN)[-1][:1500])
        srv.js(ep.CLOCK_PLAYING_JS)
        t_end = time.time() + 15.0
        while time.time() < t_end:
            time.sleep(5.0)
        tick, rows = parse_scan(srv.js(JS_SCAN)[-1])
        print("T1 tick=%.1f tiles=%d" % (tick, len(rows)))
        for r in rows:
            print("   ", r["raw"][:150])
        res = {"tick": tick,
               "A_silicon": sum_item(rows, "container", "silicon"),
               "smelters": [{"xy": r["xy"], "eff": r["eff"], "items": r["items"], "power": r["power"],
                             "prog": r["prog"]} for r in rows if r["block"] == "silicon-smelter"],
               "nodes": [{"xy": r["xy"], "power": r["power"]} for r in rows if r["block"].startswith("power-")]}
        print("RESULT", json.dumps(res, ensure_ascii=False))
    finally:
        srv.close()


if __name__ == "__main__":
    main()
