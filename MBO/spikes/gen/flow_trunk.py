# -*- coding: utf-8 -*-
"""测"输入链路"本身能搬多少煤：源 -> ... -> 容器，用容器增量量吞吐。

--mode belts  : 一条直带子（基线，应 4.9/s）
--mode routers: 带子 + 3 台路由器串起来的干线
--mode gate   : 源 -> 带子 -> 单个反溢门 -> 容器（门本身是不是限速）

用法：python -X utf8 spikes/gen/flow_trunk.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from mbo import engine  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402
from mbo.model import Layout, item_cfg  # noqa: E402


def mode_belts():
    b = [("item-source", 0, 0, 0, "coal")]
    for x in range(1, 11):
        b.append(("conveyor", x, 0, 0, None))
    b.append(("container", 11, 0, 0, None))
    return b


def mode_routers():
    b = [("item-source", 0, 0, 0, "coal"), ("conveyor", 1, 0, 0, None),
         ("router", 2, 0, 0, None), ("conveyor", 3, 0, 0, None), ("conveyor", 4, 0, 0, None),
         ("router", 5, 0, 0, None), ("conveyor", 6, 0, 0, None), ("conveyor", 7, 0, 0, None),
         ("router", 8, 0, 0, None), ("conveyor", 9, 0, 0, None), ("conveyor", 10, 0, 0, None),
         ("router", 11, 0, 0, None), ("conveyor", 12, 0, 0, None),
         ("container", 13, 0, 0, None)]
    return b


def mode_gate():
    b = [("item-source", 0, 0, 0, "coal"), ("conveyor", 1, 0, 0, None),
         ("underflow-gate", 2, 0, 0, None), ("conveyor", 3, 0, 0, None),
         ("container", 4, 0, 0, None)]
    return b


MODES = {"belts": mode_belts, "routers": mode_routers, "gate": mode_gate}


def build(blocks, size=(20, 6)):
    gd = GameData()
    lay = Layout(size[0], size[1], {name: b.size for name, b in gd.blocks.items()})
    for name, x, y, rot, item in blocks:
        lay.add(name, x, y, rot, item_cfg(gd, item) if item else None)
    return lay, gd


def main() -> int:
    out = {}
    for mode, fn in MODES.items():
        lay, gd = build(fn())
        eng = engine.run(lay, gd, "coal", ticks=1800, timeout=240.0)
        m = (eng or {}).get("metrics") or {}
        out[mode] = {"rate": m.get("rate"), "rate_containers": m.get("rate_containers"),
                     "containers_delta": m.get("containers_delta"), "window_s": m.get("window_s"),
                     "err": (eng or {}).get("error")}
        print(mode, json.dumps(out[mode], ensure_ascii=False))
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
