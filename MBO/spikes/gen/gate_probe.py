"""反/正溢流门（underflow/overflow gate）实测：一条煤带能否稳定分流到两台石墨压机。

布局（源直接贴在门上方，门左右各一台 2x2 压机，直行方向留空堵死）：

       源(6,4)  <- coal，100/s 直塞
          v
      (6,5) 门  --- 东 -> A 压机 (7..8 x 5..6)
       /     \\--> 西 -> B 压机 (4..5 x 5..6)
      直行(6,6) = 空地（堵死）
    B 仓(4,3..4) 压 B 上方        A 仓(9..10 x 5..6)

语义来自源码 `OverflowGate.getTileTarget`：
  - 溢流门(invert=false)：直行能走就直行，直行堵了才走两侧（两侧都通 → 按 rotation 位交替）
  - 反溢门(invert=true) ：优先走两侧（两侧都通 → 交替），两侧都堵才走直行
直行是空地 → 两种门都只能往左右两侧交替塞，正好当 50/50 分流器。
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mbo import engine, gamedata, model  # noqa: E402


def build(gd, gate: str, w=16, h=12):
    lay = model.Layout(w, h, {n: b.size for n, b in gd.blocks.items()},
                       name="gate-" + gate, description="gate split probe")
    lay.add("item-source", 6, 4, rotation=model.ROT["S"], config=model.item_cfg(gd, "coal"))
    lay.add(gate, 6, 5)
    lay.add("graphite-press", 4, 5)     # 西（占 4..5 x 5..6）→ 门西邻 (5,5)
    lay.add("graphite-press", 7, 5)     # 东（占 7..8 x 5..6）→ 门东邻 (7,5)
    lay.add("container", 4, 3)          # B 的仓（占 4..5 x 3..4），贴压机上方
    lay.add("container", 9, 5)          # A 的仓（占 9..10 x 5..6），贴压机右侧
    return lay


def per_container(samples, tags):
    out = {}
    for tag in tags:
        prev = None
        tot = 0
        for s in samples:
            v = s.get(tag)
            if v is None or "/" not in v:
                continue
            cur = int(v.split("/")[0])
            if s["tick"] < 300:
                prev = cur
                continue
            if prev is not None:
                tot += max(0, cur - prev)
            prev = cur
        last = [s for s in samples if s["tick"] >= 300]
        dt = (last[-1]["tick"] - 300.0) / 60.0 if last else 0.0
        out[tag] = tot / dt if dt > 0 else 0.0
    return out


def one(gd, gate, ticks=1800):
    lay = build(gd, gate)
    st = lay.stats()
    print("\n=== %s ===  blocks=%d tiles=%d" % (gate, st["blocks"], st["tiles"]))
    r = engine.run(lay, gd, "graphite", ticks=ticks)
    if not r["ok"]:
        print("  FAIL", r.get("error"))
        return None
    m = r["metrics"]
    rates = per_container(r["samples"], ["c0", "c1"])
    print("  total=%.3f/s (理论 1.333)  deadlock=%s  wall=%.1fs  eff_avg=%.2f"
          % (m["rate"], m["deadlock"], r["wall_s"], m["eff_avg"]))
    print("  A(东)=%.3f/s  B(西)=%.3f/s" % (rates["c0"], rates["c1"]))
    return m["rate"], rates, st


if __name__ == "__main__":
    gd = gamedata.GameData()
    res = {}
    for gate in ("underflow-gate", "overflow-gate"):
        res[gate] = one(gd, gate)
    print("\nSUMMARY")
    for k, v in res.items():
        if v:
            print("  %-16s total=%.3f  A=%.3f  B=%.3f  blocks=%d tiles=%d"
                  % (k, v[0], v[1]["c0"], v[1]["c1"], v[2]["blocks"], v[2]["tiles"]))
