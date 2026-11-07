# -*- coding: utf-8 -*-
"""_dbg_3x3.py -- 3x3 方块到底从哪格开始占？(决定生成器布局数学)

.msch 里存的坐标，对奇数尺寸方块是"中心格"还是"原点格"？
  world = st.(x,y) + (px - w/2, py - h/2)
  若中心：vault(2,2) -> 世界中心(30,37) -> 占 29..31 / 36..38
  若原点：vault(2,2) -> 占 30..32 / 37..39
"""
from __future__ import annotations

import base64
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "sim"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "bp"))

import msch  # noqa: E402
import scan_corpus as sc  # noqa: E402
import engine_probe as ep  # noqa: E402

JS_TILES = r"""
(function(){
var W = Vars.world, out = [];
for(var x = 24; x < 48; x++){
  for(var y = 32; y < 46; y++){
    var t = W.tile(x,y); if(t == null || t.block() == null || t.block().name == "air") continue;
    out.push(x + "," + y + ":" + t.block().name);
  }
}
print("TILES\t" + out.join("\t"));
var out2 = [];
for(var x = 24; x < 48; x++){ for(var y = 32; y < 46; y++){
  var t = W.tile(x,y); if(t != null && t.build != null){ out2.push(t.build.block.name + " origin=" + t.build.tileX() + "," + t.build.tileY()); }
}}
print("BUILDS\t" + out2.join("\t"));
})();
"""


def main():
    sch = msch.Schematic(24, 10, {"name": "dbg3"}, [
        msch.Stile("vault", 2, 2, 0),
        msch.Stile("container", 8, 2, 0),
        msch.Stile("router", 12, 2, 0),
    ], version=msch.CURRENT_VERSION)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    p = os.path.join(HERE, "out", "dbg3.msch")
    with open(p, "wb") as fh:
        fh.write(sc.build_schematic_ext(sch))
    b64 = base64.b64encode(open(p, "rb").read()).decode("ascii")

    srv = ep.Server(ep.JAR, ep.JAVA, 128)
    try:
        time.sleep(13.0)
        srv.js(ep.BP_PREP_JS % {"n": 128})
        print("PLACE", srv.js(ep.BP_PLACE_JS % {"b64": b64, "i": 0, "px": 40, "py": 40})[-1][:200])
        for line in srv.js(JS_TILES):
            print(line[:2000])
    finally:
        srv.close()


if __name__ == "__main__":
    main()
