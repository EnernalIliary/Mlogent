# -*- coding: utf-8 -*-
"""量"单源主干 + 4 个门"到底送进来多少煤：把压机换成容器做汇点。

用法：python -X utf8 spikes/gen/flow_gates4.py
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

PRESS_X = [1, 4, 7, 10]


def blocks():
    b = [("item-source", 0, 0, 0, "coal"), ("conveyor", 1, 0, 0, None)]
    for px in PRESS_X:
        b.append(("router", px + 1, 0, 0, None))
        b.append(("underflow-gate", px + 1, 1, 3, None))
        b.append(("container", px + 1, 2, 0, None))
    for x in (3, 4, 6, 7, 9, 10):
        b.append(("conveyor", x, 0, 0, None))
    return b


def main() -> int:
    gd = GameData()
    lay = Layout(20, 8, {name: blk.size for name, blk in gd.blocks.items()})
    for name, x, y, rot, item in blocks():
        lay.add(name, x, y, rot, item_cfg(gd, item) if item else None)
    eng = engine.run(lay, gd, "coal", ticks=1800, timeout=240.0)
    m = (eng or {}).get("metrics") or {}
    print(json.dumps({"rate": m.get("rate"), "containers_delta": m.get("containers_delta"),
                      "window_s": m.get("window_s"), "deadlock": m.get("deadlock")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
