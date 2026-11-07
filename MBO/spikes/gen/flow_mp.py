# -*- coding: utf-8 -*-
"""微探针：源 -> 带子 -> 门 -> 压机（下方黑洞），看"门喂压机"这条边到底多少吞吐。

注意：2×2 方块的 (x,y) 就是左上角（origin == 中心格 == 左上角）。

用法：python -X utf8 spikes/gen/flow_mp.py
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


def blocks(mode):
    if mode == "gate3":
        # 压机 (2,2)-(3,3)；门在正上方 (2,1)、rot=3（正面 +y 朝下）；黑洞在下方
        return [("item-source", 0, 0, 0, "coal"), ("conveyor", 1, 0, 0, None),
                ("conveyor", 2, 0, 0, None),
                ("underflow-gate", 2, 1, 3, None),
                ("graphite-press", 2, 2, 0, None),
                ("item-void", 2, 4, 0, None)]
    if mode == "gate0":
        # 压机 (3,2)-(4,3)；门在左侧 (2,2)、rot=0（正面 +x 朝右）
        return [("item-source", 0, 2, 0, "coal"), ("conveyor", 1, 2, 0, None),
                ("underflow-gate", 2, 2, 0, None),
                ("graphite-press", 3, 2, 0, None),
                ("item-void", 3, 4, 0, None)]
    # 源直接贴压机顶
    return [("item-source", 2, 1, 0, "coal"),
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
    for mode in ("gate3", "gate0", "direct"):
        lay, gd = build(blocks(mode))
        eng = engine.run(lay, gd, "graphite", ticks=1800, timeout=240.0)
        m = (eng or {}).get("metrics") or {}
        out[mode] = {"rate": m.get("rate"), "eff_avg": m.get("eff_avg"),
                     "deadlock": m.get("deadlock"), "err": (eng or {}).get("error")}
        print(mode, json.dumps(out[mode], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
