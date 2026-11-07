# -*- coding: utf-8 -*-
"""_dbg_run.py -- 从零构造的产线为什么跑不起来？

改进点（相对 gen_trust.py）：
  * 读数不看 Groups.build（从 Schematics.place 放下的方块不一定进该组——
    源码注释原话：「Groups.build can be empty, indexer is probably inaccurate」），
    改为直接扫世界 tile。
  * 逐方块打印 items/progress/efficiency/power.links/power.satisfaction。
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

JS_SCAN = r"""
(function(){
var W = Vars.world, out = [];
for(var x = 30; x < 60; x++){
  for(var y = 30; y < 60; y++){
    var t = W.tile(x,y); if(t == null) continue;
    var b = t.build; if(b == null) continue;
    var its = "";
    if(b.items != null){
      var I = Vars.content.items();
      for(var j = 0; j < I.size; j++){ var amt = b.items.get(I.get(j)); if(amt > 0) its += I.get(j).name + "=" + Math.round(amt*100)/100 + " "; }
    }
    var pw = "";
    if(b.power != null){
      pw = "links=" + (b.power.links == null ? -1 : b.power.links.size)
         + " sat=" + Math.round(b.power.status*100)/100
         + " need=" + Math.round(b.power.lastPowerNeeded*100)/100
         + " got=" + Math.round(b.power.lastPowerReceived*100)/100
         + " prox=" + (b.proximity == null ? -1 : b.proximity.size);
    }
    out.push(b.block.name + "@" + b.tileX() + "," + b.tileY() + " i[" + its.trim() + "]"
      + " prog=" + Math.round(b.progress*100)/100 + " eff=" + Math.round(b.efficiency*100)/100 + " " + pw);
  }
}
print("SCAN\t" + out.join("\t"));
})();
"""


def build():
    return msch.Schematic(12, 10, {"name": "dbg"}, [
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


def main():
    sch = build()
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    path = os.path.join(HERE, "out", "dbg_run.msch")
    with open(path, "wb") as fh:
        fh.write(sc.build_schematic_ext(sch))
    b64 = base64.b64encode(open(path, "rb").read()).decode("ascii")

    srv = ep.Server(ep.JAR, ep.JAVA, 128)
    try:
        time.sleep(13.0)
        srv.js(ep.BP_PREP_JS % {"n": 128})
        srv.js(ep.BP_PLACE_JS % {"b64": b64, "i": 0, "px": 40, "py": 40})
        print("T0", srv.js(JS_SCAN)[-1][:2000])
        srv.js(ep.CLOCK_PLAYING_JS)
        t_end = time.time() + 12.0          # 约 700 tick
        while time.time() < t_end:
            time.sleep(2.0)
        print("T1", srv.js(JS_SCAN)[-1][:2500])
        snap = srv.js(ep.BP_SNAP_JS % {"tag": "x"})[-1]
        print("SNAP", snap[:600])
    finally:
        srv.close()


if __name__ == "__main__":
    main()
