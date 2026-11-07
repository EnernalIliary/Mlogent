"""L4 真机执行：把一张 `.msch` 丢进官方服务端跑真帧循环，读回真实产量。

为什么不用 mlogsim 的 `--steps`：快进模式下 power 被打了桩（docs/12 §1.7），
电量/效率读数不可信，必须让世界真跑 60Hz。

读数口径（docs/03 §3.1 / docs/13 §2）：

- 一律扫 `Vars.world.tile(x,y).build`，**不用 Groups.build**（服务端里它可能是空的）；
- 容器/核心按 tile 差分计数；机器看 `efficiency` / `progress` / `power.graph.satisfaction`；
- 服务端启动后约 12 s 会用自己的地图替换我们的世界（"Game over"），所以先等 13 s 再放置；
- `srv.js()` 每次只可靠返回一行 → 所有读数压成 tab 分隔的单行。
"""

from __future__ import annotations

import json
import os
import sys
import time

from .gamedata import MBO_ROOT

REPO_ROOT = os.path.dirname(MBO_ROOT)
_SIM = os.path.join(MBO_ROOT, "spikes", "sim")
if _SIM not in sys.path:
    sys.path.insert(0, _SIM)

import engine_probe as ep  # noqa: E402  工作区已验证的引擎封装

PX, PY = 64, 64          # 蓝图中心放在世界的哪里
WARMUP_S = 13.0          # 必须等过服务端换图


def _js_sample(spec: list) -> str:
    body = json.dumps(spec, separators=(",", ":"))
    return (
        "var S=" + body + ";var o=[];"
        "for(var i=0;i<S.length;i++){var e=S[i];"
        "var t=Vars.world.tile(e.x,e.y);var b=t?t.build:null;"
        "if(!b){o.push(e.tag+'=null');continue}"
        "if(e.kind=='items'){var it=Vars.content.item(e.item);"
        "o.push(e.tag+'='+b.items.get(it)+'/'+b.items.total())}"
        "else{o.push(e.tag+'='+(Math.round(b.efficiency*1000)/1000)"
        "+'/'+(Math.round(b.progress*1000)/1000)"
        "+'/'+(b.power?Math.round(b.power.graph.satisfaction*1000)/1000:1))}}"
        "print('SAMPLE\\t'+Vars.state.tick+'\\t'+o.join('|'));"
    )


def run(lay, gd, target: str, ticks: int = 1800, sample_s: float = 0.3,
        timeout: float = 180.0, keep_spec: bool = False) -> dict:
    """在真引擎里放置并运行，返回 {ok, ticks, wall_s, samples, metrics, error?}。"""
    ox, oy = PX - lay.w // 2, PY - lay.h // 2   # place() 以蓝图中心为锚
    spec = []
    containers = [t for t in lay.tiles if t.block in ("container", "vault", "core-shard")]
    for i, c in enumerate(containers):
        spec.append({"tag": "c%d" % i, "x": ox + c.x, "y": oy + c.y, "kind": "items",
                     "item": target})
    crafters = [t for t in lay.tiles if gd.block(t.block).recipe is not None]
    machines = []
    for i, c in enumerate(crafters):
        tag = "m%d" % i
        spec.append({"tag": tag, "x": ox + c.x, "y": oy + c.y, "kind": "craft"})
        r = gd.block(c.block).recipe
        out = sum(o["amount"] for o in r.output_items if o.get("name") == target) \
            if getattr(r, "output_items", None) else 0.0
        machines.append({"tag": tag, "craft": r.craft_time_frames, "out": out or 1.0})

    data = lay.to_bytes()
    b64 = ep.load_schematic_b64_from_bytes(data) if hasattr(ep, "load_schematic_b64_from_bytes") else None
    if b64 is None:
        import base64

        b64 = base64.b64encode(data).decode("ascii")

    t0 = time.time()
    srv = ep.Server()
    samples: list[dict] = []
    try:
        time.sleep(WARMUP_S)
        srv.js(ep.BP_PREP_JS % {"n": 128})
        out = srv.js(ep.BP_PLACE_JS % {"b64": b64, "i": 0, "px": PX, "py": PY})
        placed = next((ln for ln in out if "PLACED" in ln), "")
        if not placed:
            return {"ok": False, "error": "放置失败：%s" % (out[:3],), "wall_s": time.time() - t0}
        srv.js(ep.CLOCK_PLAYING_JS)

        script = _js_sample(spec)
        last_tick = -1.0
        while True:
            if time.time() - t0 > timeout:
                return {"ok": False, "error": "超时 %.0fs（tick=%s）" % (timeout, last_tick),
                        "samples": samples, "wall_s": time.time() - t0}
            lines = srv.js(script)
            line = next((ln for ln in lines if ln.startswith("SAMPLE")), None)
            if line is not None:
                parts = line.split("\t")
                tick = float(parts[1])
                rec = {"tick": tick}
                for kv in parts[2].split("|") if len(parts) > 2 else []:
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        rec[k] = v
                samples.append(rec)
                if tick <= last_tick:
                    return {"ok": False, "error": "tick 回退（世界被重置）", "samples": samples,
                            "wall_s": time.time() - t0}
                last_tick = tick
                if tick >= ticks:
                    break
            time.sleep(sample_s)

        metrics = summarize(samples, target, ticks, machines=machines)
        return {
            "ok": True,
            "ticks": last_tick,
            "wall_s": round(time.time() - t0, 1),
            "placed": placed,
            "samples_n": len(samples),
            "metrics": metrics,
            "samples": samples if keep_spec else samples[:: max(1, len(samples) // 60)],
        }
    finally:
        try:
            srv.close()
        except Exception:  # noqa: BLE001 —— 关服务端失败不影响结论
            pass


def summarize(samples: list, target: str, ticks: int, skip: int = 300,
              machines=None) -> dict:
    """稳态窗口（丢前 skip tick）产量与效率。

    计量有两种口径：
      containers——容器/仓库/核心里的件数差分（首选，直接读到实物）；
      cycles——机器 `progress` 的回绕次数 × 每周期产量（出口是 item-void 时唯一办法，
               因为黑洞把产物销毁了，容器差分恒为 0）。
    """
    win = [s for s in samples if s["tick"] >= skip]
    if len(win) < 2:
        return {"rate": None, "error": "样本不足（%d）" % len(win)}
    first, last = win[0], win[-1]
    dt_s = (last["tick"] - first["tick"]) / 60.0

    def total(rec) -> float:
        tot = 0.0
        for k, v in rec.items():
            if k.startswith("c") and "/" in str(v):
                tot += float(str(v).split("/")[0])
        return tot

    delta = total(last) - total(first)
    rate_containers = delta / dt_s if dt_s > 0 else None

    # 周期回绕计数：progress 在周期结束时回落。整数回绕只能精确到“整个周期”，
    # 25 s 窗口里 ±1 个周期就是 ±6% 误差，所以用**累计进度**算分数周期：
    #     累计进度 = 回绕次数 × craftTime + (末次采样 − 首次采样)
    # 既补回窗口首尾的半截周期，也不受采样相位影响。
    items = 0.0
    cycles = 0
    cycles_frac = 0.0
    for m in (machines or []):
        seq = [float(str(rec[m["tag"]]).split("/")[1])
               for rec in win if m["tag"] in rec and "/" in str(rec[m["tag"]])]
        if len(seq) < 2:
            continue
        craft = float(m.get("craft") or 0)
        wraps = 0
        for a, b in zip(seq, seq[1:]):
            if b < a - 0.5:                     # 回绕（progress 复位）
                wraps += 1
        cycles += wraps
        if craft > 0:
            adv = wraps * craft + (seq[-1] - seq[0])
            frac = adv / craft
        else:
            frac = float(wraps)
        cycles_frac += frac
        items += frac * (m.get("out") or 1.0)
    rate_cycles = (items / dt_s) if (machines and dt_s > 0) else None

    if delta > 0.5:
        rate, measured_by = rate_containers, "containers"
    elif rate_cycles is not None:
        rate, measured_by = rate_cycles, "cycles"
    else:
        rate, measured_by = rate_containers, "containers"

    effs, progs, sats = [], [], []
    for rec in win:
        for k, v in rec.items():
            if not k.startswith("m") or "/" not in str(v):
                continue
            a, b, c = (str(v).split("/") + ["1"])[:3]
            effs.append(float(a))
            progs.append(float(b))
            sats.append(float(c))
    return {
        "rate": None if rate is None else round(rate, 4),
        "measured_by": measured_by,
        "rate_containers": None if rate_containers is None else round(rate_containers, 4),
        "rate_cycles": None if rate_cycles is None else round(rate_cycles, 4),
        "cycles": cycles,
        "cycles_frac": round(cycles_frac, 3),
        "window": [round(first["tick"], 1), round(last["tick"], 1)],
        "window_s": round(dt_s, 2),
        "containers_delta": round(delta, 1),
        "machines": len(machines) if machines else len(effs),
        "eff_avg": round(sum(effs) / len(effs), 3) if effs else None,
        "eff_low": sum(1 for e in effs if e < 0.9),
        "progress_sum": round(sum(progs), 2) if progs else None,
        "power_sat_min": round(min(sats), 3) if sats else None,
        "deadlock": bool(effs and sum(1 for e in effs if e < 0.05) >= len(effs)),
        "sample_n": len(win),
    }
