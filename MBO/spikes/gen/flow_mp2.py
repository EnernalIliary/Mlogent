# -*- coding: utf-8 -*-
"""微探针 v2：真实路径 源->带子->路由器->门->压机，只改门的 rot，看哪一档能喂进去。

--mode rot3 / rot1 / rot2 / rot0 都跑一遍，直接给吞吐。

用法：python -X utf8 spikes/gen/flow_mp2.py
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


def blocks(rot):
    # 源 -> 带子(1,0) -> 路由器(2,0)；门在路由器正下方 (2,1)；压机 (2,2)-(3,3)；黑洞下方
    return [("item-source", 0, 0, 0, "coal"),
            ("conveyor", 1, 0, 0, None),
            ("router", 2, 0, 0, None),
            ("underflow-gate", 2, 1, rot, None),
            ("graphite-press", 2, 2, 0, None),
            ("item-void", 2, 4, 0, None)]


def build(bl, size=(10, 9)):
    gd = GameData()
    lay = Layout(size[0], size[1], {name: b.size for name, b in gd.blocks.items()})
    for name, x, y, rot, item in bl:
        lay.add(name, x, y, rot, item_cfg(gd, item) if item else None)
    return lay, gd


def main() -> int:
    out = {}
    for rot in (0, 1, 2, 3):
        lay, gd = build(blocks(rot))
        eng = engine.run(lay, gd, "graphite", ticks=1800, timeout=240.0)
        m = (eng or {}).get("metrics") or {}
        out["rot%d" % rot] = {"rate": m.get("rate"), "deadlock": m.get("deadlock")}
        print("rot%d" % rot, json.dumps(out["rot%d" % rot], ensure_ascii=False))
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
