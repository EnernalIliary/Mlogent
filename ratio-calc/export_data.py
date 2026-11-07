"""把 MBO 的游戏数据快照 + 原版贴图导出成网页可直接用的一份 JS 数据。

为什么导出成 .js 而不是 .json：双击打开 index.html 时，浏览器对 file:// 的
fetch/JSON 有 CORS 限制，而 `<script src="data/gamedata.js">` 不受影响。

图标内联成 base64 data URI，**用原尺寸**（1×1=32、2×2=64、3×3=96、5×5=160）：
物品取 `sprites/items/item-<名字>.png`，方块取 `sprites/blocks/**/<名字>.png`，
单位取 `sprites/units/<名字>-base.png`（没有就用 `-cell.png` 兜底）。

数据来源：
    MBO/gamedata/<snapshot>/gamedata.json          物品配方 + 各方块电力
    MBO/gamedata/<snapshot>/units_production.json  兵厂（单位工厂 / 升级厂 / 组装厂）
    MBO/gamedata/<snapshot>/power_drill.json       发电厂 / 钻头 / 分离机·解离机

用法（在工作区根）：
    python -X utf8 ratio-calc/export_data.py
    python -X utf8 ratio-calc/export_data.py --snapshot v160.7 --out ratio-calc/data/gamedata.js
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # AtomicStates
MBO = os.path.join(ROOT, "MBO")
SPRITES = os.path.join(ROOT, "assetsraw", "assets-raw", "sprites")


def load(snapshot: str, name: str = "gamedata.json") -> dict | None:
    path = os.path.join(MBO, "gamedata", snapshot, name)
    if not os.path.exists(path):
        if name == "gamedata.json":
            sys.exit("找不到快照：%s" % path)
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _index_block_sprites() -> dict:
    """方块名 -> png 路径。带子这类是 <名字>-<混合位>-<帧>.png，取 -0-0。"""
    idx = {}
    root = os.path.join(SPRITES, "blocks")
    if not os.path.isdir(root):
        return idx
    for base, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".png"):
                continue
            stem = fn[:-4]
            idx.setdefault(stem, os.path.join(base, fn))
            if stem.endswith("-0-0"):
                idx.setdefault(stem[:-4], os.path.join(base, fn))
            elif stem.endswith("-0"):
                idx.setdefault(stem[:-2], os.path.join(base, fn))
    return idx


def icon_data_uri(path: str | None) -> str:
    """读 PNG 原样转 base64 data URI（不做缩放）；找不到就返回空串。"""
    if not path or not os.path.exists(path):
        return ""
    try:
        from PIL import Image
    except ImportError:
        return ""
    im = Image.open(path).convert("RGBA")
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def unit_icon(name: str) -> str:
    root = os.path.join(SPRITES, "units")
    for pat in ("%s-base.png", "%s-cell.png", "%s.png"):
        path = os.path.join(root, pat % name)
        if os.path.exists(path):
            return icon_data_uri(path)
    return ""


def _float_items(pairs) -> list:
    return [[name, float(amount)] for name, amount in pairs]


def build_power(raw: dict, power_drill: dict | None, block_index: dict) -> dict:
    """发电厂 / 钻头 / 多产物方块（分离机·解离机）。"""
    usage = {}
    for b in raw.get("blocks", []):
        pw = b.get("power") or {}
        usage[b["name"]] = float(pw.get("usagePerSecond") or 0.0)

    pd = power_drill or {}
    generators = []
    for g in pd.get("generators", []):
        generators.append({
            "name": g["name"],
            "size": int(g.get("size") or 1),
            "icon": icon_data_uri(block_index.get(g["name"])),
            "perSecond": float(g.get("perSecond") or 0.0),
            "kind": g.get("kind") or "",
            # 自耗电（impact-reactor 的 consumePower）
            "powerUsage": float(g.get("powerUsagePerSecond") or 0.0),
            "fuels": [[f["name"], float(f["perSecond"]), float(f["powerPerSecond"])]
                      for f in g.get("fuels") or []],
            "liquids": [[l["name"], float(l["perSecond"])] for l in g.get("liquids") or []],
        })

    drills = []
    for d in pd.get("drills", []):
        drills.append({
            "name": d["name"],
            "size": int(d.get("size") or 1),
            "icon": icon_data_uri(block_index.get(d["name"])),
            "tier": int(d.get("tier") or 0),
            "drillTime": float(d.get("drillTime") or 300.0),
            "hardnessMult": float(d.get("hardnessMult") or 0.0),
            "boostLiquid": d.get("boostLiquid") or "",
            "boostLiquidPerSecond": float(d.get("boostLiquidPerSecond") or 0.0),
            "boostIntensity": float(d.get("boostIntensity") or 1.0),
            "power": usage.get(d["name"], 0.0),
        })

    multi = []
    for s in pd.get("separators", []):
        multi.append({
            "name": s["name"],
            "size": int(s.get("size") or 1),
            "icon": icon_data_uri(block_index.get(s["name"])),
            "craftTime": float(s.get("craftTime") or 0.0),
            "cps": float(s.get("cps") or 0.0),
            "power": float(s.get("power") or 0.0),
            "inputs": [[k, float(v)] for k, v in (s.get("inputs") or {}).items()],
            "inputLiquids": [[k, float(v)] for k, v in (s.get("inputLiquids") or {}).items()],
            "outputs": [[o["name"], float(o["perSecond"]), float(o["share"])]
                        for o in s.get("outputs") or []],
        })

    return {"generators": generators, "drills": drills, "multi": multi,
            "item_props": pd.get("items") or {}}


def build(raw: dict, block_index: dict, unit_prod: dict | None,
          power_drill: dict | None = None) -> dict:
    # ---- 物品工厂（craftTime > 0）----
    blocks = []
    for b in raw.get("blocks", []):
        r = b.get("recipe") or {}
        frames = r.get("craftTime") or 0
        if frames <= 0:
            continue
        inputs = []
        for cons in r.get("inputs") or []:
            for it in cons.get("items") or []:
                inputs.append([it["name"], float(it["amount"])])
        outputs = [[it["name"], float(it["amount"])] for it in r.get("outputItems") or []]
        pw = b.get("power") or {}
        blocks.append({
            "name": b["name"],
            "kind": "item",
            "size": int(b.get("size") or 1),
            "power": float(pw.get("usagePerSecond") or 0.0),
            "craft_time": int(frames),
            "inputs": inputs,
            "outputs": outputs,
            "icon": icon_data_uri(block_index.get(b["name"])),
        })

    # ---- 兵厂（单位工厂 / 升级厂 / 组装厂）----
    for f in (unit_prod or {}).get("factories", []):
        name = f["block"]
        size = 3
        for b in raw.get("blocks", []):
            if b["name"] == name:
                size = int(b.get("size") or 3)
                break
        entry = {
            "name": name,
            "kind": "unit",
            "size": size,
            "power": float(f.get("power") or 0.0),
            "icon": icon_data_uri(block_index.get(name)),
            "factory_kind": f["kind"],
        }
        if f["kind"] == "reconstructor":
            # 升级厂：一个周期 = constructTime，消耗固定材料、把 from 单位升级成 to
            entry["craft_time"] = int(f.get("constructTime") or 120)
            entry["inputs"] = _float_items((f.get("items") or {}).items())
            entry["outputs"] = []
            entry["upgrades"] = f.get("upgrades") or []
        else:
            plans = []
            for p in f.get("units") or []:
                plans.append({
                    "unit": p["unit"],
                    "time": float(p["time"]),
                    "items": _float_items((p.get("items") or {}).items()),
                })
            entry["plans"] = plans
        blocks.append(entry)

    blocks.sort(key=lambda x: x["name"])

    # ---- 物品（含钻头要用的 hardness）----
    power = build_power(raw, power_drill, block_index)
    props = power["item_props"]
    items_dir = os.path.join(SPRITES, "items")
    items = []
    for it in raw.get("items", []):
        name = it["name"]
        path = os.path.join(items_dir, "item-%s.png" % name)
        pr = props.get(name) or {}
        items.append({
            "name": name,
            "id": int(it["id"]),
            "icon": icon_data_uri(path),
            "hardness": float(pr.get("hardness") or 0.0),
            "flammability": float(pr.get("flammability") or 0.0),
            "radioactivity": float(pr.get("radioactivity") or 0.0),
        })
    items.sort(key=lambda x: x["name"])

    # ---- 单位图标（兵厂大循环表用）----
    unit_icons = {}
    for u in (unit_prod or {}).get("units") or []:
        unit_icons[u["name"]] = unit_icon(u["name"])

    return {
        "snapshot": (raw.get("meta") or {}).get("gameVersion") or "",
        "generated_from": "MBO/gamedata + assetsraw sprites",
        "items": items,
        "blocks": blocks,
        "units": (unit_prod or {}).get("units") or [],
        "unit_icons": unit_icons,
        "generators": power["generators"],
        "drills": power["drills"],
        "multi": power["multi"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default="v160.7")
    ap.add_argument("--out", default=os.path.join(HERE, "data", "gamedata.js"))
    args = ap.parse_args()

    raw = load(args.snapshot)
    unit_prod = load(args.snapshot, "units_production.json")
    power_drill = load(args.snapshot, "power_drill.json")
    block_index = _index_block_sprites()
    data = build(raw, block_index, unit_prod, power_drill)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("// 自动生成，别手改：python -X utf8 ratio-calc/export_data.py\n")
        fh.write("window.MBO_DATA = ")
        fh.write(body)
        fh.write(";\n")
    n_item_blocks = sum(1 for b in data["blocks"] if b["kind"] == "item")
    n_unit_blocks = sum(1 for b in data["blocks"] if b["kind"] == "unit")
    n_icon = (sum(1 for b in data["blocks"] if b["icon"])
              + sum(1 for i in data["items"] if i["icon"])
              + sum(1 for v in data["unit_icons"].values() if v))
    print("写出 %s：%d 个物品工厂 / %d 个兵厂 / %d 发电厂 / %d 钻头 / %d 多产物方块 / "
          "%d 个物品 / %d 个图标 / %.1f KB"
          % (args.out, n_item_blocks, n_unit_blocks, len(data["generators"]),
             len(data["drills"]), len(data["multi"]), len(data["items"]),
             n_icon, os.path.getsize(args.out) / 1024))


if __name__ == "__main__":
    main()
