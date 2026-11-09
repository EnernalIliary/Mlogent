"""oil_floor_probe.py -- 真机测石油钻井产量 vs 地板属性。

电力接法（pwr_diag.py 验证过）：consumer 邻位放 power-node，node 与 power-source
之间**双向显式写 Point2[] links**（`b.configure(Point2[])`，`configureAny` 不生效），
这样 graph.all 才会包含三者、satisfaction=1。

三个地板（darksand 1.5 / sand-floor 0.7 / shale 2.0）各一台石油钻井，
旁边 liquid-container 接油读数；另放一台煤炭离心机确认 6 油/s -> 2 煤/s。

期望：A 22.5 / B 10.5 / C 30.0 油/s；离心机 6 油/s + 2 煤/s。
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import engine_probe as ep  # noqa: E402

WARMUP_S = 13.0
SKIP_TICKS = 90

# (标签, 地板, 期望油/s, 钻井左上, 容器左上)
RIGS = [
    ("A_darksand", "darksand", 22.5, (30, 30), (30, 33)),
    ("B_sandfloor", "sand-floor", 10.5, (30, 40), (30, 43)),
    ("C_shale", "shale", 30.0, (30, 50), (30, 53)),
]

PLACE_JS = r"""(function(){
var W = Vars.world, T = Packages.mindustry.game.Team.sharded;
var P2 = Packages.arc.math.geom.Point2;
function put(x,y,name){
  var blk = Vars.content.block(name);
  if(blk == null){ print("MISS\t" + name); return null; }
  var t = W.tile(x,y); t.setBlock(blk, T, 0); Vars.indexer.addIndex(t);
  var b = W.build(x,y);
  print("PUT\t" + name + "@" + x + "," + y + "\tbuild=" + (b != null));
  return b;
}
/* Fracker 的 envRequired 含 Env.groundOil(32)、水提取器含 groundWater(64)，
   生成世界默认 rules.env 只有 terrestrial(1)，不补这两位方块根本不 update。 */
try { Vars.state.rules.env = Vars.state.rules.env | 32 | 64; print("ENV\t" + Vars.state.rules.env); }
catch(e){ print("ENV_WARN\t" + e); }
function floorRect(x0,y0,w,h,name){
  var fl = Vars.content.block(name).asFloor();
  for(var x = x0; x < x0 + w; x++){ for(var y = y0; y < y0 + h; y++){ W.tile(x,y).setFloor(fl); } }
}
function setLinks(b, arr, tag){
  if(b == null){ print("CFG\t" + tag + "\tnull"); return; }
  var cls = java.lang.Class.forName("arc.math.geom.Point2");
  var out = java.lang.reflect.Array.newInstance(cls, arr.length);
  for(var i = 0; i < arr.length; i++){ out[i] = new P2(arr[i][0], arr[i][1]); }
  try { b.configure(out); print("CFG\t" + tag + "\tok"); }
  catch(e){ print("CFG\t" + tag + "\tFAILED\t" + e); }
}
floorRect(28,28,8,8,"darksand");
floorRect(28,38,8,8,"sand-floor");
floorRect(28,48,8,8,"shale");

/* A/B/C 三台石油钻井 3x3 @(30,y)，node @(33,y+1)，source @(33,y) */
var ys = [30, 40, 50];
for(var i = 0; i < ys.length; i++){
  var y = ys[i];
  put(30,y,"oil-extractor");
  put(33,y+1,"power-node");
  put(33,y,"power-source");
  put(30,y+3,"liquid-container");
  var nd = W.build(33,y+1);
  setLinks(nd, [[0,-1]], "A_node_" + i);
  setLinks(W.build(33,y), [[0, 1]], "A_src_" + i);
  /* 直接 setBlock 不走 placed()，consumer 不会自动并网 -> 显式加进节点所在的图 */
  try { nd.power.graph.add(W.build(30,y)); print("JOIN\tA_" + i + "\tall=" + nd.power.graph.all.size); }
  catch(e){ print("JOIN\tA_" + i + "\tFAILED\t" + e); }
}

/* D：煤炭离心机 2x2 @(40,30) + node @(42,30) + source @(42,29) + 油罐 + 煤箱 */
put(40,30,"coal-centrifuge");
put(42,30,"power-node");
put(42,29,"power-source");
put(40,32,"liquid-container");
put(42,31,"container");
var dn = W.build(42,30);
setLinks(dn, [[0,-1]], "D_node");
setLinks(W.build(42,29), [[0, 1]], "D_src");
try { dn.power.graph.add(W.build(40,30)); print("JOIN\tD\tall=" + dn.power.graph.all.size); }
catch(e){ print("JOIN\tD\tFAILED\t" + e); }
var lc = W.build(40,32);
if(lc != null){ lc.liquids.add(Vars.content.liquid("oil"), 1000); }
print("READY\tgroups=" + Packages.mindustry.gen.Groups.build.size()
  + "\toil=" + (lc == null ? -1 : Math.round(lc.liquids.get(Vars.content.liquid("oil")))));
})();"""

SAMPLE_JS = r"""(function(){
var W = Vars.world;
var oil = Vars.content.liquid("oil"), water = Vars.content.liquid("water");
var sand = Vars.content.item("sand"), coal = Vars.content.item("coal");
var eA = W.build(30,30), cA = W.build(30,33);
var eB = W.build(30,40), cB = W.build(30,43);
var eC = W.build(30,50), cC = W.build(30,53);
var ce = W.build(40,30), ct = W.build(42,31), cl = W.build(40,32);
function feed(b){ if(b != null){ b.liquids.add(water, 60); b.items.add(sand, 5); } }
feed(eA); feed(eB); feed(eC);
/* 钻井的油如果 dump 不到容器就会堵在自带 40 容量里（shouldConsume 变 false），
   所以每次采样把自带油倒空，用「本次产出」累加求速率。 */
function drainP(b, item){
  if(b == null) return -1;
  var v = b.liquids.get(item);
  b.liquids.remove(item, v);
  return v;
}
var pA = drainP(eA, oil), pB = drainP(eB, oil), pC = drainP(eC, oil);
function lp(b){ return b == null ? -1 : Math.round(b.lastPump * 600) / 10; }
function r2(v){ return Math.round(v*100)/100; }
function tank(c){ return c == null ? -1 : r2(c.liquids.get(oil)); }
function eff(b){ return b == null ? -1 : Math.round(b.efficiency*1000)/1000; }
function sat(b){ return (b == null || b.power == null || b.power.graph == null) ? -1 : Math.round(b.power.graph.getSatisfaction()*1000)/1000; }
print("SAMPLE\t" + Vars.state.tick
  + "\tpA=" + (pA < 0 ? -1 : Math.round(pA*100)/100)
  + "\tpB=" + (pB < 0 ? -1 : Math.round(pB*100)/100)
  + "\tpC=" + (pC < 0 ? -1 : Math.round(pC*100)/100)
  + "\tlpA=" + lp(eA) + "\tlpB=" + lp(eB) + "\tlpC=" + lp(eC)
  + "\tA=" + tank(cA) + "\tB=" + tank(cB) + "\tC=" + tank(cC)
  + "\teA=" + eff(eA) + "\teB=" + eff(eB) + "\teC=" + eff(eC)
  + "\tsA=" + sat(eA) + "\tsB=" + sat(eB) + "\tsC=" + sat(eC) + "\tsCe=" + sat(ce)
  + "\tce=" + eff(ce)
  + "\tcoal=" + (ct == null ? -1 : r2(ct.items.get(coal)))
  + "\toilLeft=" + (cl == null ? -1 : r2(cl.liquids.get(oil)))
  + "\tplaying=" + Vars.state.isPlaying());
})();"""


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=900)
    ap.add_argument("--sample-s", type=float, default=0.35)
    ap.add_argument("--json", default=os.path.join(ep.OUT, "oil_floor_probe.json"))
    args = ap.parse_args(argv)
    os.makedirs(ep.OUT, exist_ok=True)

    t0 = time.time()
    srv = None
    samples: list[dict] = []
    try:
        srv = ep.Server()
        time.sleep(WARMUP_S)
        srv.js(ep.BP_PREP_JS % {"n": 128})
        for ln in srv.js(PLACE_JS):
            print("P\t" + ln, flush=True)
        srv.js(ep.CLOCK_PLAYING_JS)
        tick0 = ep._read_tick(srv)
        print("TICK0\t%s" % tick0, flush=True)
        while True:
            if time.time() - t0 > 230:
                print("TIMEOUT", flush=True)
                break
            lines = srv.js(SAMPLE_JS)
            line = next((ln for ln in lines if ln.startswith("SAMPLE")), None)
            if line is None:
                continue
            rec = {}
            parts = line.split("\t")
            rec["tick"] = float(parts[1])
            for kv in parts[2:]:
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    try:
                        rec[k] = float(v)
                    except ValueError:
                        rec[k] = v
            samples.append(rec)
            if rec["tick"] - tick0 >= args.ticks:
                break
            time.sleep(args.sample_s)

        win = [s for s in samples if s["tick"] >= tick0 + SKIP_TICKS]
        out = {"ticks": args.ticks, "samples": len(samples), "wall_s": round(time.time() - t0, 1)}
        if len(win) < 5:
            out["error"] = "样本不足"
            print("RESULT\t" + json.dumps(out, ensure_ascii=False), flush=True)
            return 1
        first, last = win[0], win[-1]
        dt = (last["tick"] - first["tick"]) / 60.0
        rates = {}
        for k, _lab, _exp, _a, _b in RIGS:
            key = k[0]
            got = sum(s2.get("p" + key, 0) for s2 in win[:-1])
            rates[key] = round(got / dt, 3) if dt > 0 else None
        out["rates"] = rates
        out["expect"] = {r[0][0]: r[2] for r in RIGS}
        out["dev_pct"] = {k: (round((rates[k] - out["expect"][k]) / out["expect"][k] * 100, 1)
                              if rates.get(k) is not None else None) for k in out["expect"]}
        out["eff"] = {"A": last.get("eA"), "B": last.get("eB"), "C": last.get("eC"), "centrifuge": last.get("ce")}
        out["lastPump_x60"] = {"A": last.get("lpA"), "B": last.get("lpB"), "C": last.get("lpC")}
        out["satisfaction"] = {"A": last.get("sA"), "B": last.get("sB"), "C": last.get("sC"), "centrifuge": last.get("sCe")}
        out["centrifuge"] = {"coal_per_s": round((last["coal"] - first["coal"]) / dt, 3) if dt > 0 else None,
                             "oil_per_s": round((first["oilLeft"] - last["oilLeft"]) / dt, 3) if dt > 0 else None,
                             "expect": {"coal_per_s": 2.0, "oil_per_s": 6.0}}
        out["window_s"] = round(dt, 2)
        out["window"] = [first["tick"], last["tick"]]
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
        print("RESULT\t" + json.dumps(out, ensure_ascii=False), flush=True)
        return 0
    finally:
        if srv is not None:
            srv.close()


if __name__ == "__main__":
    sys.exit(main())
