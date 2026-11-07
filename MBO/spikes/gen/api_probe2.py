"""headless 服务端里 Schematics 实例方法能不能用：`Vars.schematics` 是 null，
试试自己 new 一个实例调 writeBase64 / create。"""
import base64
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "spikes" / "sim"))

import engine_probe as ep  # noqa: E402
from mbo import gamedata, model  # noqa: E402

PX, PY = 64, 64

JS_PARTS = [
    "var S=Packages.mindustry.game.Schematics;var o=[];",
    "var sch=S.readBase64('%(b64)s');",
    "try{var inst=new S();o.push('inst=ok');}catch(e0){o.push('newerr='+e0);}",
    "try{o.push('wlen='+inst.writeBase64(sch).length);}catch(e2){o.push('werr='+e2);}",
    "try{var cap=inst.create(%(x0)d,%(y0)d,%(x1)d,%(y1)d);o.push('cap='+cap.width+'x'+cap.height+'/'+cap.tiles.size);}"
    "catch(e3){o.push('caperr='+e3);}",
    "try{var r=S.rotate(sch,1);o.push('rot='+r.width+'x'+r.height+'/'+r.tiles.size);}catch(e4){o.push('roterr='+e4);}",
    "print('PROBE\\t'+o.join('\\t'));",
]
JS = "".join(JS_PARTS)


def build(gd):
    lay = model.Layout(16, 12, {n: b.size for n, b in gd.blocks.items()}, name="api2")
    lay.add("item-source", 6, 4, rotation=model.ROT["S"], config=model.item_cfg(gd, "coal"))
    lay.add("underflow-gate", 6, 5)
    lay.add("graphite-press", 4, 5)
    lay.add("graphite-press", 7, 5)
    lay.add("container", 4, 3)
    lay.add("container", 9, 5)
    return lay


gd = gamedata.GameData()
lay = build(gd)
data = lay.to_bytes()
b64 = base64.b64encode(data).decode("ascii")
ox, oy = PX - lay.w // 2, PY - lay.h // 2

srv = ep.Server()
try:
    time.sleep(13)
    srv.js(ep.BP_PREP_JS % {"n": 128})
    print(srv.js(ep.BP_PLACE_JS % {"b64": b64, "i": 0, "px": PX, "py": PY})[-2:])
    line = next((ln for ln in srv.js(JS % {"b64": b64, "x0": ox, "y0": oy,
                                           "x1": ox + lay.w - 1, "y1": oy + lay.h - 1})
                 if ln.startswith("PROBE")), None)
    print("PROBE:", line)
finally:
    srv.close()
