# -*- coding: utf-8 -*-
"""_dbg_place.py -- 为什么从零构造的蓝图进引擎后建筑数不对？

只做一件事：readBase64 后把引擎解析出的每个 Stile 原样打出来（块名/坐标/旋转/config），
再 place，再逐 tile 扫世界看真实落点，最后列 Groups.build。
"""
from __future__ import annotations

import base64
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

ITEM = {"copper": 0, "lead": 1, "metaglass": 2, "graphite": 3, "sand": 4, "coal": 5,
        "titanium": 6, "thorium": 7, "scrap": 8, "silicon": 9}

JS_INSPECT = r"""
(function(){
var sch = Packages.mindustry.game.Schematics.readBase64("%(b64)s");
var out = [];
var it = sch.tiles.iterator();
while(it.hasNext()){
  var st = it.next();
  var cfg = "-";
  try { cfg = String(st.config); } catch(e){ cfg = "?"; }
  out.push(st.block.name + "@" + st.x + "," + st.y + " r" + st.rotation + " cfg=" + cfg);
}
print("SCH\t" + sch.width + "x" + sch.height + "\t" + out.join("\t"));
})();
"""

JS_WORLD = r"""
(function(){
var W = Vars.world, out = [], bs = [];
for(var x = 30; x < 60; x++){
  for(var y = 30; y < 60; y++){
    var t = W.tile(x,y);
    if(t == null || t.block() == null || t.block().name == "air") continue;
    out.push(x + "," + y + ":" + t.block().name + (t.build == null ? "(nobuild)" : ""));
  }
}
var GB = Packages.mindustry.gen.Groups.build;
for(var k = 0; k < GB.size; k++){
  var b = GB.index(k);
  bs.push(b.block.name + "@" + b.tileX() + "," + b.tileY() + "/" + b.block.size + "x" + b.block.size);
}
print("TILES\t" + out.join("\t"));
print("BUILDS\t" + bs.join("\t"));
})();
"""


def main():
    sch = msch.Schematic(12, 10, {"name": "dbg"}, [
        msch.Stile("silicon-smelter", 2, 2, 0),
        msch.Stile("silicon-smelter", 6, 2, 0),
        msch.Stile("item-source", 1, 2, 0, {"__content__": "item", "id": 5}),
        msch.Stile("item-source", 1, 3, 0, {"__content__": "item", "id": 4}),
        msch.Stile("item-source", 5, 2, 0, {"__content__": "item", "id": 5}),
        msch.Stile("item-source", 5, 3, 0, {"__content__": "item", "id": 4}),
        msch.Stile("container", 4, 2, 0),
        msch.Stile("container", 8, 2, 0),
        msch.Stile("power-node", 3, 4, 0, sc.TaggedList([(3, 0), (0, 2)], tag=8)),
        msch.Stile("power-node", 6, 4, 0, sc.TaggedList([(-3, 0)], tag=8)),
        msch.Stile("power-source", 3, 6, 0, sc.TaggedList([(0, -2)], tag=8)),
    ], version=msch.CURRENT_VERSION)
    path = os.path.join(HERE, "out", "dbg.msch")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(sc.build_schematic_ext(sch))
    b64 = base64.b64encode(open(path, "rb").read()).decode("ascii")

    srv = ep.Server(ep.JAR, ep.JAVA, 128)
    try:
        time.sleep(13.0)
        srv.js(ep.BP_PREP_JS % {"n": 128})
        for ln in srv.js(JS_INSPECT % {"b64": b64}):
            print("INSPECT", ln[:1500])
        srv.js(ep.BP_PLACE_JS % {"b64": b64, "i": 0, "px": 40, "py": 40})
        # 再读一次世界（place 后立刻，不跑 tick）
        for ln in srv.js(JS_WORLD):
            print("WORLD", ln[:2500])
    finally:
        srv.close()


if __name__ == "__main__":
    main()
