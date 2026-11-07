# -*- coding: utf-8 -*-
"""gen_trust.py -- 生成器可信度测试 v2（从零造蓝图 → 写 .msch → 真引擎验证）。

回答用户的"蓝图生成器到底可不可信"（2026-11-04）：
  T1 编码层：我们写出的字节能否被工具链/游戏完整读回（语料 body 逐字节还原）
  T2 坐标层：.msch 里存的坐标是 origin 还是中心格；place(px,py) 以谁为锚
  T3 语义层：旋转方向、多格占地、电力 config 是否按预期生效
  T4 功能层：从零造的一条产线能否真跑、产量能否按"tile 扫描"测出来

重要：读数**不用** Groups.build —— 源码自承 "Groups.build can be empty,
indexer is probably inaccurate"（MapProcessorsDialog.java:146），实测从
Schematics.place 放下的 21 个 tile 只有 5 个进组。改为直接扫 world.tile。

用法：
    python -X utf8 MBO\\spikes\\gen\\gen_trust.py                # 全部（约 90 s）
    python -X utf8 MBO\\spikes\\gen\\gen_trust.py --skip-engine  # 只跑静态层
产物：MBO/spikes/gen/out/{trust_sem,trust_run,trust_rot}.msch + trust.json
"""
from __future__ import annotations

import base64
import glob
import json
import os
import sys
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))       # ...\AtomicStates
SPIKES = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(SPIKES, "sim"))
sys.path.insert(0, os.path.join(SPIKES, "bp"))

import msch                      # noqa: E402
import scan_corpus as sc         # noqa: E402
import engine_probe as ep        # noqa: E402

OUT = os.path.join(HERE, "out")
ITEM_ID = {"copper": 0, "lead": 1, "metaglass": 2, "graphite": 3, "sand": 4, "coal": 5,
           "titanium": 6, "thorium": 7, "scrap": 8, "silicon": 9, "plastanium": 10,
           "phase-fabric": 11, "surge-alloy": 12, "spore-pod": 13, "blast-compound": 14,
           "pyratite": 15}

# 扫世界（不信 Groups.build）：每个 build 只打一次；同时给出 container 里的物品
JS_SCAN = r"""
(function(){
var W = Vars.world, out = [], seen = {};
for(var x = 0; x < W.width(); x++){
  for(var y = 0; y < W.height(); y++){
    var t = W.tile(x,y); if(t == null || t.build == null) continue;
    var b = t.build; if(seen[b.id] != null) continue; seen[b.id] = 1;
    var its = "";
    if(b.items != null){
      var I = Vars.content.items();
      for(var j = 0; j < I.size; j++){ var amt = b.items.get(I.get(j)); if(amt > 0) its += I.get(j).name + "=" + Math.round(amt*100)/100 + " "; }
    }
    var f = null; try { f = b.front(); } catch(e){}
    var pw = "-";
    if(b.power != null){
      pw = "links=" + (b.power.links == null ? -1 : b.power.links.size)
         + ",sat=" + Math.round(b.power.status*100)/100
         + ",prox=" + (b.proximity == null ? -1 : b.proximity.size);
    }
    out.push(b.block.name + "@" + b.tileX() + "," + b.tileY()
      + "|rot=" + b.rotation
      + "|front=" + (f == null ? "none" : (f.x + "," + f.y))
      + "|i[" + its.trim() + "]"
      + "|prog=" + Math.round(b.progress*100)/100
      + "|eff=" + Math.round(b.efficiency*100)/100
      + "|" + pw);
  }
}
print("SCAN\t" + Vars.state.tick + "\t" + out.length + "\t" + out.join("\t"));
})();
"""


def mk(w, h, tiles, name):
    return msch.Schematic(w, h, {"name": name}, tiles, version=msch.CURRENT_VERSION)


def T(block, x, y, rot=0, config=None):
    return msch.Stile(block, x, y, rot, config)


def item(name):
    return {"__content__": "item", "id": ITEM_ID[name]}


def pts(seq):
    return sc.TaggedList([tuple(p) for p in seq], tag=8)


# ---------------------------------------------------------------- 三张实验图
def build_rot():
    """T3：四个旋转方向的传送带（检验 rotation 写回 + front 方向）。"""
    return mk(24, 6, [
        T("conveyor", 2, 2, 0),
        T("conveyor", 6, 2, 1),
        T("conveyor", 10, 2, 2),
        T("conveyor", 14, 2, 3),
        T("router", 18, 2, 0),
    ], "mbo-trust-rot")


def build_sem():
    """T2：多格方块（3x3 vault / 2x2 container）占地与锚点。"""
    return mk(24, 10, [
        T("vault", 2, 2, 0),            # 3x3
        T("container", 8, 2, 0),        # 2x2
        T("router", 12, 2, 0),          # 1x1 对照
    ], "mbo-trust-sem")


def build_run():
    """T4：两条独立硅产线（互不重叠），显式电力 config。

    A: 源 coal(1,2) sand(1,3) -> smelter(2,2)[2..3] -> container(4,2)[4..5]
    B: 源 coal(6,2) sand(6,3) -> smelter(7,2)[7..8] -> container(9,2)[9..10]
    电力: node(3,5) -- node(8,5)；power-source(3,7) -- node(3,5)
    """
    return mk(12, 10, [
        T("item-source", 1, 2, 0, item("coal")),
        T("item-source", 1, 3, 0, item("sand")),
        T("silicon-smelter", 2, 2, 0),
        T("container", 4, 2, 0),
        T("item-source", 6, 2, 0, item("coal")),
        T("item-source", 6, 3, 0, item("sand")),
        T("silicon-smelter", 7, 2, 0),
        T("container", 9, 2, 0),
        T("power-node", 3, 4, 0, pts([(5, 0), (0, 2)])),
        T("power-node", 8, 4, 0, pts([(-5, 0)])),
        T("power-source", 3, 6, 0, pts([(0, -2)])),
    ], "mbo-trust-run")


def write_sch(sch, fname):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, fname)
    with open(path, "wb") as fh:
        fh.write(sc.build_schematic_ext(sch))
    return path


def verify_static(sch, path):
    back = msch.parse_file(path)
    a = [(t.block, t.x, t.y, t.rotation) for t in sch.tiles]
    b = [(t.block, t.x, t.y, t.rotation) for t in back.tiles]
    return {"path": os.path.relpath(path, ROOT).replace("\\", "/"),
            "bytes": os.path.getsize(path), "w": sch.width, "h": sch.height,
            "tiles": len(sch.tiles), "reparse_ok": a == b,
            "holes": [t.rotation for t in back.tiles]}


def parse_scan(line):
    """SCAN\\t<tick>\\t<n>\\t<entry>... -> (tick, [entry dict])"""
    parts = line.split("\t")
    tick = float(parts[1])
    rows = []
    for e in parts[3:]:
        f = e.split("|")
        if len(f) < 7:
            continue
        name, xy = f[0].split("@")
        d = {"raw": e, "block": name, "xy": xy, "rot": int(f[1][4:]),
             "front": f[2][6:], "items": f[3][2:-1].strip(),
             "prog": float(f[4][5:]), "eff": float(f[5][4:]), "power": f[6]}
        rows.append(d)
    return tick, rows


def sum_item(rows, block, item_name):
    tot = 0.0
    for r in rows:
        if r["block"] != block:
            continue
        for kv in r["items"].split():
            k, _, v = kv.partition("=")
            if k == item_name:
                tot += float(v)
    return tot


def run_engine(sem_path, rot_path, run_path, ticks=1800):
    srv = ep.Server(ep.JAR, ep.JAVA, 128)
    res = {"timing": {}}
    try:
        t = time.time()
        time.sleep(13.0)                       # 服务端 ~12s 后会替换世界，等它过去
        res["timing"]["warmup_s"] = round(time.time() - t, 2)

        # ---- T3 旋转
        srv.js(ep.BP_PREP_JS % {"n": 128})
        srv.js(ep.BP_PLACE_JS % {"b64": ep.load_schematic_b64(rot_path), "i": 1, "px": 40, "py": 40})
        res["rot"] = parse_scan(srv.js(JS_SCAN)[-1])[1]
        print("T3\trotation:", json.dumps([{k: r[k] for k in ("block", "xy", "rot", "front")} for r in res["rot"]], ensure_ascii=False))

        # ---- T2 多格锚点
        srv.js(ep.BP_PREP_JS % {"n": 128})
        srv.js(ep.BP_PLACE_JS % {"b64": ep.load_schematic_b64(sem_path), "i": 2, "px": 40, "py": 40})
        _, sem_rows = parse_scan(srv.js(JS_SCAN)[-1])
        res["sem"] = [{k: r[k] for k in ("block", "xy", "rot", "front")} for r in sem_rows]
        print("T2\tmultiblock:", json.dumps(res["sem"], ensure_ascii=False))

        # ---- T4 产线
        t = time.time()
        srv.js(ep.BP_PREP_JS % {"n": 128})
        srv.js(ep.BP_PLACE_JS % {"b64": ep.load_schematic_b64(run_path), "i": 3, "px": 40, "py": 40})
        srv.js(ep.CLOCK_PLAYING_JS)
        samples = []
        t_prev = None
        while True:
            tick, rows = parse_scan(srv.js(JS_SCAN)[-1])
            samples.append({"tick": tick, "silicon": sum_item(rows, "container", "silicon"),
                            "smelter_eff": [r["eff"] for r in rows if r["block"] == "silicon-smelter"],
                            "smelter_items": [r["items"] for r in rows if r["block"] == "silicon-smelter"],
                            "nodes": [r["power"] for r in rows if r["block"].startswith("power-")],
                            "tiles": len(rows)})
            if t_prev is not None and tick - t_prev < 0:
                res["wiped"] = True
                break
            t_prev = tick
            if tick >= ticks:
                break
            time.sleep(4.0)
        res["run"] = {"samples": samples, "wall_s": round(time.time() - t, 2)}

        # 产量：丢掉前 300 tick 的启动段
        base = next((s for s in samples if s["tick"] >= 300), samples[0])
        last = samples[-1]
        dt = (last["tick"] - base["tick"]) / 60.0
        dsi = last["silicon"] - base["silicon"]
        res["yield"] = {"window_ticks": [base["tick"], last["tick"]],
                        "dsilicon": dsi, "dt_s": round(dt, 2),
                        "per_s": round(dsi / dt, 3) if dt > 0 else None,
                        "theory_per_s": 3.0,
                        "rel_err": round((dsi / dt - 3.0) / 3.0, 4) if dt > 0 else None}
        print("T4\tyield:", json.dumps(res["yield"], ensure_ascii=False))
        print("T4\tlast sample:", json.dumps(last, ensure_ascii=False))
    finally:
        srv.close()
    return res


def main(argv=None):
    skip = "--skip-engine" in (argv or sys.argv[1:])
    os.makedirs(OUT, exist_ok=True)
    report = {}

    # ---------- T1a 语料 body 逐字节还原
    corpus = []
    for pat in ("logic-corpus/*/msch/*.msch", "logic-corpus/*/schematics/*.msch"):
        corpus += glob.glob(os.path.join(ROOT, pat))
    picks = []
    for want in ("metaglass-2.msch", "graphite-1.msch", "cryofluid-2.msch"):
        picks += [p for p in corpus if p.endswith(want)][:1]
    report["t1_corpus"] = []
    for p in picks:
        orig = open(p, "rb").read()
        new = sc.build_schematic_ext(msch.parse_file(p))
        report["t1_corpus"].append({
            "file": os.path.relpath(p, ROOT).replace("\\", "/"),
            "body_identical": zlib.decompress(new[5:]) == zlib.decompress(orig[5:]),
            "ver": [orig[4], new[4]], "bytes": [len(orig), len(new)]})

    # ---------- T1b 从零写 → 读回
    rot, sem, run = build_rot(), build_sem(), build_run()
    rot_p, sem_p, run_p = (write_sch(rot, "trust_rot.msch"), write_sch(sem, "trust_sem.msch"),
                           write_sch(run, "trust_run.msch"))
    report["t1_scratch"] = [verify_static(s, p) for s, p in ((rot, rot_p), (sem, sem_p), (run, run_p))]
    print("T1a\tcorpus body identical:", [c["body_identical"] for c in report["t1_corpus"]])
    print("T1b\tfrom-scratch reparse ok:", [c["reparse_ok"] for c in report["t1_scratch"]])

    if not skip:
        report["engine"] = run_engine(sem_p, rot_p, run_p)
    with open(os.path.join(OUT, "trust.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("WROTE", os.path.join(OUT, "trust.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
