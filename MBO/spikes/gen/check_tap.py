# -*- coding: utf-8 -*-
"""检查 tap 合并版是否满足"端口在工厂外接矩形之外"。"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "spikes", "gen"))

import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("fs2", os.path.join(os.path.dirname(__file__), "flow_single2.py"))
fs2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fs2)

from mbo import logistics, production, search, validate  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402

gd = GameData()
plan = production.expand(gd, "graphite", 2.45, ["coal"])
blocks = fs2.build_blocks(4, "merged")
lay = search._make(gd, blocks, (20, 7))
lay.crop()
ok, msg = logistics.ports_outside(lay, gd)
print("ports_outside =", ok, msg)
st = validate.static_check(lay, gd, plan, strict_ports=True)
print("static ok =", st["ok"], st["errors"][:3], st["info"])
cand = search.evaluate(gd, plan, blocks, (20, 7))
print("evaluate ->", None if cand is None else (cand.ports, cand.clusters, cand.tiles, cand.rate))
