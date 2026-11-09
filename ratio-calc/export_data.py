"""把 MBO 的游戏数据快照 + 原版贴图导出成网页可直接用的一份 JS 数据。

为什么导出成 .js 而不是 .json：双击打开 index.html 时，浏览器对 file:// 的
fetch/JSON 有 CORS 限制，而 `<script src="data/gamedata.js">` 不受影响。

图标内联成 base64 data URI，**优先用 `-full` 尾缀的原尺寸大图**：
方块取 `sprites/generated/block-<名字>-full.png`，单位取 `sprites/generated/unit-<名字>-full.png`；
没有 `-full` 时回退到 物品 `sprites/items/item-<名字>.png`、方块 `sprites/blocks/**/<名字>.png`、
单位 `sprites/units/<名字>-base.png`（再退 `-cell.png`）。
同时导出中文名（`bundle_zh_CN.properties` 的 item/block/unit 名字），页面显示「中文名 (英文名)」。

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
KNOWLEDGE = os.path.join(ROOT, "knowledge")
GENERATED = os.path.join(SPRITES, "generated")
ZH_BUNDLE = os.path.join(ROOT, "assetsraw", "assets", "bundles", "bundle_zh_CN.properties")
FULL_SPRITES = {"block": {}, "unit": {}}


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


def _index_full_sprites() -> dict:
    """-full 尾缀的全尺寸贴图：block-<名字>-full.png / unit-<名字>-full.png。"""
    idx = {"block": {}, "unit": {}}
    if not os.path.isdir(GENERATED):
        return idx
    for fn in os.listdir(GENERATED):
        if not fn.endswith("-full.png"):
            continue
        stem = fn[:-len("-full.png")]
        for kind in ("block", "unit"):
            pre = kind + "-"
            if stem.startswith(pre):
                idx[kind][stem[len(pre):]] = os.path.join(GENERATED, fn)
                break
    return idx


def load_zh_names() -> dict:
    """bundle_zh_CN.properties 里的 物品/方块/单位 中文名。"""
    out = {"items": {}, "blocks": {}, "units": {}}
    if not os.path.exists(ZH_BUNDLE):
        return out
    with open(ZH_BUNDLE, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip()
            if not key.endswith(".name"):
                continue
            parts = key.split(".")
            if len(parts) != 3:
                continue
            kind, name = parts[0], parts[1]
            bucket = {"item": "items", "block": "blocks", "unit": "units"}.get(kind)
            if bucket:
                out[bucket][name] = val
    return out


def block_icon(name: str, block_index: dict) -> str:
    """方块图标：优先 generated/block-<名字>-full.png，回退原贴图索引。"""
    return icon_data_uri(FULL_SPRITES["block"].get(name) or block_index.get(name))


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
    full = FULL_SPRITES["unit"].get(name)
    if full:
        return icon_data_uri(full)
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
            "icon": block_icon(g["name"], block_index),
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
            "icon": block_icon(d["name"], block_index),
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
            "icon": block_icon(s["name"], block_index),
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


# ---- 外部入料方式（带子/接收台的吞吐）----
# 带子吞吐 = speed × 60 / itemSpace(0.4)（Conveyor.java:27-32）。
# 数值以 v160.7 jar 为准（knowledge/00-data/blocks.json：conveyor.speed = 0.035 ⇒ 5.25/s，
# titanium-conveyor 0.0801 ⇒ 12.015/s）；v159.3 源码的 0.046 已不再使用。
# 数值可在页面上单选切换；如需按别的版本覆盖，改这张表即可。
INPUT_CHANNELS = [
    {"key": "belt-grey", "label": "灰带 conveyor", "block": "conveyor",
     "perSecond": 5.25, "power": 0.0,
     "note": "最基础，1 格 1 条（v160.7 jar speed 0.035 → speed×60/0.4 = 5.25/s）"},
    {"key": "belt-blue", "label": "蓝带 titanium-conveyor", "block": "titanium-conveyor",
     "perSecond": 12.015, "power": 0.0, "note": "钛带，约 2.3 倍灰带"},
    {"key": "belt-green", "label": "绿带 plastanium-conveyor", "block": "plastanium-conveyor",
     "perSecond": 40.0, "power": 0.0, "note": "塑料带，一次运 10 件（约 7.6 倍灰带）"},
    {"key": "phase-bridge", "label": "布桥 phase-conveyor", "block": "phase-conveyor",
     "perSecond": 30.0, "power": 18.0, "note": "隔空传送，要电"},
    {"key": "mass-driver", "label": "质驱 mass-driver", "block": "mass-driver",
     "perSecond": 36.0, "power": 105.0, "note": "远距离投送，要电"},
    {"key": "pad", "label": "接收台 landing-pad", "block": "landing-pad",
     "perSecond": 0.0, "power": 0.0, "note": "不限速，外部直接投送"},
    {"key": "other", "label": "其它（不限）", "block": "",
     "perSecond": 0.0, "power": 0.0, "note": "随意，按不限速处理"},
]


def build_pumps(raw: dict, block_index: dict) -> list:
    """抽水泵（Pump / SolidPump / Fracker）。

    数值口径：`raw.pumpAmount` 是 **每 tick** 的量 ⇒ ×60 = 每秒；
    `raw.result` 是产出液体（Pump 基类没有该字段，默认水）；
    `Fracker`（oil-extractor）每 `itemUseTime` 帧吃一次物品 ⇒ 每秒 = amount × 60 / itemUseTime。
    """
    pumps = []
    for b in raw.get("blocks", []):
        rr = b.get("raw") or {}
        pa = rr.get("pumpAmount")
        if pa is None:
            continue
        liquid = rr.get("result") or "water"
        item_use = float(rr.get("itemUseTime") or 0.0)
        inputs, input_liquids = [], []
        for cons in b.get("consumers") or []:
            for it in cons.get("items") or []:
                per = float(it["amount"])
                if item_use > 0:
                    per = per * 60.0 / item_use
                inputs.append([it["name"], per])
            for lq in cons.get("liquids") or []:
                # consumers 里的液体量是 per-tick
                input_liquids.append([lq["name"], float(lq["amount"]) * 60.0])
        pumps.append({
            "name": b["name"],
            "size": int(b.get("size") or 1),
            "icon": block_icon(b["name"], block_index),
            "perSecond": round(float(pa) * 60.0, 6),
            "liquid": liquid,
            "kind": (rr.get("subclass") or "").rsplit(".", 1)[-1],
            "power": float((b.get("power") or {}).get("usagePerSecond") or 0.0),
            "inputs": inputs,
            "inputLiquids": input_liquids,
        })
    pumps.sort(key=lambda p: -p["perSecond"])
    return pumps


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
        in_liquids = []
        for cons in r.get("inputs") or []:
            for it in cons.get("items") or []:
                inputs.append([it["name"], float(it["amount"])])
            for lq in cons.get("liquids") or []:
                # consumers 里的液体量是 per-tick
                in_liquids.append([lq["name"], float(lq["amount"]) * 60.0])
        outputs = [[it["name"], float(it["amount"])] for it in r.get("outputItems") or []]
        out_liquids = []
        for lq in r.get("outputLiquidsPerSecond") or []:
            out_liquids.append([lq["name"], float(lq["amount"])])
        if not out_liquids:
            cps = float(r.get("cyclesPerSecond") or 0.0)
            for lq in r.get("outputLiquids") or []:
                out_liquids.append([lq["name"], float(lq["amount"]) * cps])
        pw = b.get("power") or {}
        blocks.append({
            "name": b["name"],
            "kind": "item",
            "size": int(b.get("size") or 1),
            "power": float(pw.get("usagePerSecond") or 0.0),
            "craft_time": int(frames),
            "inputs": inputs,
            "outputs": outputs,
            "input_liquids": in_liquids,
            "output_liquids": out_liquids,
            "icon": block_icon(b["name"], block_index),
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
            "icon": block_icon(name, block_index),
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

    # ---- 液体颜色（液体在原版没有独立贴图，用 knowledge 里 jar 导出的 colorHex 画色点）----
    liquid_colors = {}
    lq_path = os.path.join(KNOWLEDGE, "00-data", "liquids.json")
    if os.path.isfile(lq_path):
        with io.open(lq_path, encoding="utf-8") as fh:
            for lq in json.load(fh):
                hx = (lq.get("colorHex") or "").strip()
                if hx:
                    liquid_colors[lq["name"]] = "#" + hx[:6].lower()

    return {
        "snapshot": (raw.get("meta") or {}).get("gameVersion") or "",
        "generated_from": "MBO/gamedata + assetsraw sprites + knowledge/00-data/liquids.json",
        "items": items,
        "blocks": blocks,
        "units": (unit_prod or {}).get("units") or [],
        "unit_icons": unit_icons,
        "generators": power["generators"],
        "drills": power["drills"],
        "multi": power["multi"],
        "pumps": build_pumps(raw, block_index),
        "channels": [dict(c) for c in INPUT_CHANNELS],
        "liquid_colors": liquid_colors,
        "names": load_zh_names(),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default="v160.7")
    ap.add_argument("--out", default=os.path.join(HERE, "data", "gamedata.js"))
    args = ap.parse_args()

    raw = load(args.snapshot)
    unit_prod = load(args.snapshot, "units_production.json")
    power_drill = load(args.snapshot, "power_drill.json")
    global FULL_SPRITES
    FULL_SPRITES = _index_full_sprites()
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
          "%d 抽水泵 / %d 个物品 / %d 个图标 / 中文名 %d 条 / %.1f KB"
          % (args.out, n_item_blocks, n_unit_blocks, len(data["generators"]),
             len(data["drills"]), len(data["multi"]), len(data["pumps"]),
             len(data["items"]), n_icon, len(data["names"]["blocks"]) + len(data["names"]["units"])
             + len(data["names"]["items"]), os.path.getsize(args.out) / 1024))


if __name__ == "__main__":
    main()
