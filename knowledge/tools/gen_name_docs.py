#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_name_docs.py — 从 en/zh bundle + 00-data 生成 5 篇中英名对照文章（只读 bundle，不改数据表）。

用法:
    python knowledge/tools/gen_name_docs.py            # 生成 02-world/W13..W16 与 04-units/U06
    python knowledge/tools/gen_name_docs.py --check    # 只报告覆盖率与行数，不写文件

数据源:
    <assets>/assets/bundles/bundle.properties       英文显示名
    <assets>/assets/bundles/bundle_zh_CN.properties 中文显示名
    knowledge/00-data/{blocks,units,items,liquids,status}.json  (id 全集与分组)
    <assets> 依次找 $MLOG_ASSETS、本仓库下的 assetsraw/、以及同级的
    TextureMDT/（游戏素材拆出去后的目录名）—— 素材不在本仓库里。
key 规则: <kind>.<id>.name，kind ∈ block/unit/item/liquid/status。
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KB = HERE.parent
REPO = KB.parent


def _asset_root() -> Path:
    """Where the extracted game assets live (they are no longer in this repo)."""
    cands = [os.environ.get("MLOG_ASSETS"),
             REPO / "assetsraw",
             REPO.parent / "TextureMDT",
             REPO.parent / "Mindustry_assetsraw",
             REPO.parent / "assetsraw"]
    for c in cands:
        if c and (Path(c) / "assets" / "bundles").is_dir():
            return Path(c)
    return REPO / "assetsraw"


ASSETS = _asset_root()
B_EN = ASSETS / "assets/bundles/bundle.properties"
B_ZH = ASSETS / "assets/bundles/bundle_zh_CN.properties"
DATA = KB / "00-data"

KV_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*=\s*(.*)$")
# Mindustry 的颜色/标记形式，如 [lightgray]、[accent]、[#ff0000]
TAG_RE = re.compile(r"\[[a-zA-Z#][a-zA-Z0-9#_]{0,15}\]")
MAX_LINES = 250


def load_bundle(path: Path):
    out = {}
    with path.open(encoding="utf-8-sig", errors="replace") as fh:
        for i, raw in enumerate(fh, 1):
            m = KV_RE.match(raw.rstrip("\r\n"))
            if m:
                out[m.group(1)] = (m.group(2).strip(), i)
    return out


E = load_bundle(B_EN)
Z = load_bundle(B_ZH)


def clean(s: str) -> str:
    return TAG_RE.sub("", s).strip()


def names(kind: str, ident: str):
    """返回 (英文名, 英文行, 中文名, 中文行)，缺失为 None。"""
    key = kind + "." + ident + ".name"
    e = E.get(key)
    z = Z.get(key)
    return (clean(e[0]) if e else None, e[1] if e else None,
            clean(z[0]) if z else None, z[1] if z else None)


def rows(kind: str, idents):
    out = []
    for ident in idents:
        en, el, zh, zl = names(kind, ident)
        out.append((
            "`" + ident + "`",
            en or "—",
            zh or "—",
            ("zh:%d" % zl) if zl else "—",
            ("en:%d" % el) if el else "—",
        ))
    return out


def recs(name: str):
    obj = json.loads((DATA / name).read_text(encoding="utf-8-sig"))
    if isinstance(obj, dict):
        for k in ("records", "items", "entries", "rows", "data"):
            if isinstance(obj.get(k), list):
                return obj[k]
        return [v for v in obj.values() if isinstance(v, dict)]
    return obj


BLOCKS = recs("blocks.json")
UNITS = recs("units.json")
ITEMS = recs("items.json")
LIQUIDS = recs("liquids.json")
STATUS = recs("status.json")

TERRAIN_TYPES = {"floor", "wall", "ore"}
INDUSTRY_CATS = ["distribution", "power", "liquid", "production", "defense"]
COMBAT_CATS = ["crafting", "turret", "effect", "units", "logic"]


def is_terrain(b):
    return bool(set(b.get("types") or []) & TERRAIN_TYPES)


def terrain_blocks():
    return sorted((b for b in BLOCKS if is_terrain(b)),
                  key=lambda b: ((b.get("types") or [""])[0], b["id"]))


def cat_blocks(cats):
    return sorted((b for b in BLOCKS if b.get("category") in cats and not is_terrain(b)),
                  key=lambda b: (cats.index(b["category"]), b["id"]))


def coverage(kind, idents):
    hit = sum(1 for i in idents if names(kind, i)[2] or names(kind, i)[0])
    zh_only = sum(1 for i in idents if names(kind, i)[2])
    return hit, zh_only, len(idents)


def fm(art_id, title, data_refs, depends, tags, extra_src=()):
    src = [
        "assets/bundles/bundle_zh_CN.properties:1-3038",
        "assets/bundles/bundle.properties:1-3438",
    ] + list(extra_src)
    lines = ["---", "id: " + art_id, "title: " + title, "domain: " +
             ("world" if art_id.startswith("WORLD") else "unit"),
             "status: active", "ver: [v160.7_rt, v159.3_src]", "conf: S",
             "src:"]
    lines += ["  - \"" + s + "\"" for s in src]
    lines.append("data:")
    lines += ["  - \"" + d + "\"" for d in data_refs]
    lines.append("depends: [" + ", ".join(depends) + "]")
    lines.append("tags: [" + ", ".join(tags) + "]")
    lines.append("---")
    return lines


HDR = ("id", "英文名", "中文名", "中文名出处", "英文名出处")


def table(idents, kind="block"):
    lines = ["| " + " | ".join(HDR) + " |", "|" + "|".join(["---"] * len(HDR)) + "|"]
    for r in rows(kind, idents):
        lines.append("| " + " | ".join(r) + " |")
    return lines


def doc1():
    tb = terrain_blocks()
    ids = [b["id"] for b in tb]
    hit, zh_only, total = coverage("block", ids)
    art = "WORLD.NAMES.001"
    L = fm(art, "方块名对照①：地形 / 矿石 / 墙壁（%d 条）" % total,
           ["00-data/blocks.json"],
           ["WORLD.BLOCKS.001", "WORLD.TERRAIN.001"],
           ["名词", "中文名", "英文名", "翻译", "对照表", "地形", "矿石", "墙壁"])
    L += [
        "",
        "## 一句话",
        "",
        "界面上的中文名既不是 id、也不是英文名的直译；要在地图、沙盒与攻略之间对号，先用这张表把「看到的名字」换成 id，再去正文查机制与数值。",
        "",
        "## 规则 / 公式",
        "",
        "- 显示名的唯一来源是语言包：`block.<id>.name` 给方块名，`<kind>.<id>.name` 给其余实体；本文只收 `kind=block` 的地形层。",
        "- 分组依据是 00-data 的 `types` 字段：含 `floor` / `wall` / `ore` 的 %d 条即本文范围，涵盖地板、矿层、矿墙与编辑器专用地形。" % total,
        "- 表内「—」表示语言包里没有该 id 的 `.name` 项，不等于名字未知：这类方块在界面上通常不显示名字（编辑器、旧版遗留、矿层贴图）。",
        "- 显示串可能混入颜色标记（如 `[lightgray]`），表中已剥掉标记、保留括号内的文字。",
        "",
        "## 数值",
        "",
        "本节只列名词，不含任何数值；血量、尺寸、装甲等数值见 `00-data/blocks.json` 与 WORLD.BLOCKS.001。",
        "",
    ]
    L += table(ids)
    L += [
        "",
        "## 源码锚点",
        "",
        "- `assets/bundles/bundle_zh_CN.properties` —— 中文显示名；表内「中文名出处 zh:N」即该文件第 N 行。",
        "- `assets/bundles/bundle.properties` —— 英文显示名；「英文名出处 en:N」即该文件第 N 行。",
        "- `00-data/blocks.json` —— `id` / `types` / `category` 字段；本文按 `types` 过滤出 %d 条（其中 %d 条有中文名）。" % (total, zh_only),
        "- 生成脚本 `knowledge/tools/gen_name_docs.py`（游戏版本更新后重跑即可，不改 00-data）。",
        "",
        "## 实测与反例",
        "",
        "- 反例一：`dacite` 英文 Dacite（地质学上是英安岩），官方中文却是「安山岩」；而安山岩的英文是 andesite。中英名不对应，按地质名对号会错。",
        "- 反例二：`char` 英文 “Charred Stone”（烧焦的石头），中文「焦土」——既不是逐词直译，也不是石头类（它是地板）。",
        "- 反例三：`ore-copper` / `ore-lead` / `ore-thorium` 等矿层 id 在语言包里没有任何 `.name` 项；它们在沙盒菜单里以贴图出现、不显示名字。拿「铜矿」去搜 id 一定落空，必须反查 WORLD.DRILLING.001 的资源表。",
        "- 反例四：`block.launch-pad.name` 的原始值是「发射台[lightgray]（旧版）」，颜色标记不是名字的一部分；直接抄进文档会带上 `[lightgray]`。",
        "- 反例五：`build1`～`build16`、`air`、`target-dummy`、`legacy-*` 同样无 `.name`；它们是编辑器占位或旧版遗留，玩家界面不可见。",
        "",
        "## 常见误解",
        "",
        "- 把中文名当 id 用：`传送带` 不是 id，`conveyor` 才是；文档、蓝图、逻辑里只认 id。",
        "- 以为英文名等于 id：`Titanium Conveyor` 有空格和大小写，id 是 `titanium-conveyor`。",
        "- 以为中文名是英文名的直译：`Duo`=双管、`Dagger`=尖刀、`Mender`=修理器，都不是逐词对译。",
        "- 以为每个方块都有显示名：本文 %d 条里有 %d 条没有，查到「—」不代表名字缺失，而是该方块在界面不显示名字。" % (total, total - zh_only),
        "",
        "## 相关",
        "",
        "- WORLD.BLOCKS.001（方块模型与多格锚点，数值口径）",
        "- WORLD.TERRAIN.001（地形、矿层、墙三层结构，移动倍率）",
        "- WORLD.DRILLING.001（矿层与钻头覆盖，ore-* 的实际用途）",
        "- WORLD.SANDBOX.001（编辑器可见性与 build 系列占位）",
        "- WORLD.NAMES.002 / WORLD.NAMES.003（其余方块名）",
        "- EV.CHEAT.001（速查卡）",
    ]
    return art, "02-world/W13-name-blocks-terrain.md", L


def doc2():
    bl = cat_blocks(INDUSTRY_CATS)
    ids = [b["id"] for b in bl]
    hit, zh_only, total = coverage("block", ids)
    art = "WORLD.NAMES.002"
    L = fm(art, "方块名对照②：物流 / 电力 / 液体 / 生产（%d 条）" % total,
           ["00-data/blocks.json"],
           ["WORLD.BLOCKS.001", "WORLD.LOGISTICS.001"],
           ["名词", "中文名", "英文名", "翻译", "对照表", "物流", "电力", "液体", "生产"])
    L += [
        "",
        "## 一句话",
        "",
        "物流、电力、液体、生产四类可建造方块的「中文名 ↔ 英文名 ↔ id」对照；按 `category` 分组，组内按 id 字母序。",
        "",
        "## 规则 / 公式",
        "",
        "- `category` 属于 {distribution, power, liquid, production, defense} 的 %d 条方块（已排除地形、矿、墙，见 WORLD.NAMES.001）。" % total,
        "- 顺序即表内顺序：先 distribution（传送带、路由、交叉、桥、驱动器），再 power、liquid、production、defense。",
        "- 显示名取自 `block.<id>.name`；「—」= 语言包无该项（隐藏或占位方块）。",
        "- `defense` 在本组只有极少数条目；真正决定防御数值的墙体与门在 WORLD.NAMES.001 与 COMBAT.DEFENSE.001。",
        "",
        "## 数值",
        "",
        "本节只列名词；功耗、容量、速度等数值以 `00-data/blocks.json` 为准（见 WORLD.LOGISTICS.001 / WORLD.POWER.001 的实测章节）。",
        "",
    ]
    L += table(ids)
    L += [
        "",
        "## 源码锚点",
        "",
        "- `assets/bundles/bundle_zh_CN.properties`（中文名，zh:N 为行号）与 `bundle.properties`（英文名，en:N 为行号）。",
        "- `00-data/blocks.json` 的 `category` 字段是本文的分组依据；%d 条中 %d 条有中文名。" % (total, zh_only),
        "- 生成脚本 `knowledge/tools/gen_name_docs.py`。",
        "",
        "## 实测与反例",
        "",
        "- 反例一：`junction` 的官方中文是「交叉器」，不是「路口」；「路由器」是另一个方块 `router`。按字面把 junction 叫成路口，会跟门、路类方块混在一起。",
        "- 反例二：`duct` 官方中文是「物品管道」，不是「管道」；`conveyor` 才是「传送带」。两者是不同层级（管道走大流量、传送带逐件），名字近似但不是同义词。",
        "- 反例二：`phase-conveyor` 是「相织布传送带桥」，`bridge-conduit` 是「导管桥」——都叫「桥」但一个是桥接传送带、一个是桥接液体导管。",
        "- 反例三：`mass-driver` 官方中文「质量驱动器」，与电机、推进器类「驱动器」无关，它是长距离物品投送方块（见 WORLD.PAYLOAD.001）。",
        "- 反例四：`unloader` 是「装卸器」而不是「卸载器」；`sorter` 是「分类器」而非「分拣器」。按常见译名搜会搜不到。",
        "- 反例五：`force-projector` 是「力墙投影」，也被叫「力场投影仪」；官方串里没有「仪」字。",
        "",
        "## 常见误解",
        "",
        "- 把 `router`（路由器）和 `sorter`（分类器）混为一谈：前者平均分流，后者按物品过滤，机制完全不同。",
        "- 以为「管道」和「传送带」同 id：`duct` 与 `conveyor` 是两条独立的物流线，吞吐口径也不同。",
        "- 以为 category 就是 group：`category` 是内部类归类（本文 %d 条全覆盖），`group` 只覆盖可建造方块的一部分，240 条为 `none`。" % total,
        "",
        "## 相关",
        "",
        "- WORLD.LOGISTICS.001（传送带吞吐口径与桥、交叉的排队）",
        "- WORLD.POWER.001（电力网络）",
        "- WORLD.LIQUIDS.001（液体与导管）",
        "- WORLD.STORAGE.001（容器、保险库、核心容量）",
        "- WORLD.PAYLOAD.001（载荷与质量驱动器）",
        "- WORLD.NAMES.001 / WORLD.NAMES.003（其余方块名）",
    ]
    return art, "02-world/W14-name-blocks-industry.md", L


def doc3():
    bl = cat_blocks(COMBAT_CATS)
    ids = [b["id"] for b in bl]
    hit, zh_only, total = coverage("block", ids)
    art = "WORLD.NAMES.003"
    L = fm(art, "方块名对照③：合成 / 炮塔 / 效果 / 单位方块 / 逻辑（%d 条）" % total,
           ["00-data/blocks.json"],
           ["WORLD.BLOCKS.001", "COMBAT.TURRET.001"],
           ["名词", "中文名", "英文名", "翻译", "对照表", "炮塔", "合成", "逻辑", "单位方块"])
    L += [
        "",
        "## 一句话",
        "",
        "合成厂、炮塔、特效块、单位建造方块与逻辑块的「中文名 ↔ 英文名 ↔ id」对照；炮塔名常是意象词，查数值前先确认是哪一张表。",
        "",
        "## 规则 / 公式",
        "",
        "- `category` 属于 {crafting, turret, effect, units, logic} 且不含地形类型的 %d 条方块。" % total,
        "- 表内先 crafting、再 turret、effect、units、logic，组内按 id 字母序。",
        "- 炮塔数值不在本文，见 `00-data/turrets.json` 与 COMBAT.TURRET.001；单位数值见 `00-data/units.json` 与 UNIT.MOVE.001。",
        "- 逻辑块（`logic-*`）的指令语义见 06-mlog 域，本文只给名字。",
        "",
        "## 数值",
        "",
        "本节只列名词，不含射程、DPS、装填等数值；这类数字统一在 COMBAT.TURRET.001 与 COMBAT.NUMBERS.001。",
        "",
    ]
    L += table(ids)
    L += [
        "",
        "## 源码锚点",
        "",
        "- `assets/bundles/bundle_zh_CN.properties`（zh:N）与 `bundle.properties`（en:N）。",
        "- `00-data/blocks.json`：`category` 分组；%d 条中 %d 条有中文名。" % (total, zh_only),
        "- 生成脚本 `knowledge/tools/gen_name_docs.py`。",
        "",
        "## 实测与反例",
        "",
        "- 反例一：炮塔中文名三种策略并存——`duo`=双管（意译）、`scatter`=分裂与 `hail`=冰雹（意象）、`lancer`=蓝瑟（纯音译）、`fuse`=雷光（造词）。按「散射」「长矛」「引信」直译都搜不到官方串。",
        "- 反例二：单位方块（`category=units`）是工厂本身，不是单位——陆军、空军、海军工厂与坦克、飞船、机甲制造厂都在方块表，单位记录只在 `00-data/units.json`；查 `dagger` 这类单位名到方块表里找必然落空。",
        "- 反例三：重构厂用非直译词——Additive→「数增级」、Multiplicative→「倍乘级」、Exponential→「多幂级」、Tetrative→「无量级」；按 add、multiply、exponential 直译找不到。",
        "- 反例四：`core-shard` 英文 “Core: Shard”，中文「初代核心」——不是直译（直译是「核心：碎片」），按英文逐词翻找不到中文名叫什么。",
        "- 反例五：`mender` 方块中文「修理器」，与单位能力里的 repair、mend 概念共享词根，但它是可建造方块（见 COMBAT.SUPPORT.001）。",
        "- 反例六：`overdrive` 作为状态是「过载」，作为方块 `overdrive-projector` 却是「超速投影」——英文同源、中文不同名，按「过载投影仪」搜不到。",
        "- 反例七：逻辑块 `logic-processor` 是「逻辑处理器」，`logic-display` 是「逻辑显示屏」；缩写 LP、LD 只在社区口头用，不是显示名。",
        "",
        "## 常见误解",
        "",
        "- 以为炮塔中文名带「炮」字：官方串里 `duo` 就叫「双管」、`ripple` 叫「涟漪」，没有「炮」字。",
        "- 把 `effect` 类当纯装饰：这类块有实际判定（如 `overdrive-projector` 超速投影），名字像装饰但机制在 COMBAT.STATUS.001。",
        "- 以为合成厂名与产物同名：`silicon-smelter` 是「硅冶炼厂」，产物是 `silicon`「硅」，名字不同。",
        "",
        "## 相关",
        "",
        "- COMBAT.TURRET.001（炮塔射程、装填、弹药）",
        "- COMBAT.DEFENSE.001（墙体、门、护盾、修理器）",
        "- COMBAT.STATUS.001（状态与过载）",
        "- WORLD.CRAFTING.001（配方与制造）",
        "- UNIT.PRODUCE.001（单位生产链与单位方块）",
        "- WORLD.NAMES.001 / WORLD.NAMES.002（其余方块名）",
    ]
    return art, "02-world/W15-name-blocks-combat.md", L


def doc4():
    items = [i["id"] for i in sorted(ITEMS, key=lambda r: r["id"])]
    liqs = [i["id"] for i in sorted(LIQUIDS, key=lambda r: r["id"])]
    sts = [i["id"] for i in sorted(STATUS, key=lambda r: r["id"])]
    art = "WORLD.NAMES.004"
    total = len(items) + len(liqs) + len(sts)
    zh_hit = sum(1 for kind, ids in (("item", items), ("liquid", liqs), ("status", sts))
                 for i in ids if names(kind, i)[2])
    st_zh = sum(1 for i in sts if names("status", i)[2])
    L = fm(art, "物品 / 液体 / 状态效果名对照（%d 条）" % total,
           ["00-data/items.json", "00-data/liquids.json", "00-data/status.json"],
           ["WORLD.CRAFTING.001", "COMBAT.STATUS.001"],
           ["名词", "中文名", "英文名", "翻译", "对照表", "物品", "液体", "状态"])
    L += [
        "",
        "## 一句话",
        "",
        "物品、液体、状态效果三类实体的显示名对照——这三类在界面上只有名字没有方块 id，是把配方表、状态图标、液体色块翻译回 id 的唯一入口。",
        "",
        "## 规则 / 公式",
        "",
        "- key 规则：`item.<id>.name` / `liquid.<id>.name` / `status.<id>.name`；三张表的记录见 00-data。",
        "- 顺序：物品 %d 条（`00-data/items.json`）→ 液体 %d 条（`liquids.json`）→ 状态 %d 条（`status.json`），组内按 id 字母序。" % (len(items), len(liqs), len(sts)),
        "- 状态里有 `none` / `invincible` / `dynamic` 三个「无名」项：它们不是玩家可获状态，语言包没有对应显示名，表内记「—」。",
        "- 物品名多为物质名（铜、铅、硅），液体名多为液体名（水、矿渣、石油），状态名多为形容词（缓慢、过载、缴械）。",
        "",
        "## 数值",
        "",
        "本节只列名词；硬度、造价、可燃性、倍率等数值见 `00-data/items.json` / `liquids.json` / `status.json`，口径见 COMBAT.STATUS.001。",
        "",
        "### 物品",
        "",
    ]
    L += table(items, "item")
    L += ["", "### 液体", ""]
    L += table(liqs, "liquid")
    L += ["", "### 状态效果", ""]
    L += table(sts, "status")
    L += [
        "",
        "## 源码锚点",
        "",
        "- `assets/bundles/bundle_zh_CN.properties`（zh:N）与 `bundle.properties`（en:N）。",
        "- `00-data/items.json`（%d 条）/ `liquids.json`（%d 条）/ `status.json`（%d 条）；三类共 %d 条，%d 条有中文名。"
        % (len(items), len(liqs), len(sts), total, zh_hit),
        "- 生成脚本 `knowledge/tools/gen_name_docs.py`。",
        "",
        "## 实测与反例",
        "",
        "- 反例一：`plastanium` 中文是「塑钢」，不是「塑料」；`phase-fabric` 是「相织布」而不是「相位布」——按英文词根直译会错。",
        "- 反例二：`pyratite` 官方中文「硫化物」，和 pyrite（黄铁矿）不是一回事；英文名形近但中文串完全不同。",
        "- 反例三：`surge-alloy` 是「巨浪合金」，不是「电涌合金」；`carbide` 是「碳化物」、`oxide` 是「氧化物」，与 `beryllium`「铍」同属合金体系但命名不统一。",
        "- 反例四：状态 `none` / `invincible` / `dynamic` 查不到中文名，若按「无状态」「无敌」去反查 id 会得到空结果；正确 id 就是字面那三个。",
        "- 反例五：液体 `neoplasm` 是「瘤液」、`arkycite` 是「芳油」、`gallium` 是「镓液」——三条中只有 gallium 保留了元素名的「液」后缀。",
        "",
        "## 常见误解",
        "",
        "- 以为状态名就是方块名：`overdrive` 既是状态也是方块 `overdrive-projector` 的产物，两个 id 不同名。",
        "- 以为液体名与物品名同表：`water` / `slag` 只在 liquids 表，`sand` / `coal` 只在 items 表；跨表按名字查会漏。",
        "- 以为每个状态都有中文名：%d 条里有 %d 条没有（三个特殊状态）。" % (len(sts), len(sts) - st_zh),
        "",
        "## 相关",
        "",
        "- WORLD.CRAFTING.001（配方与产物）",
        "- WORLD.LIQUIDS.001（液体属性与导管）",
        "- COMBAT.STATUS.001（状态倍率与叠加）",
        "- WORLD.NAMES.001 / WORLD.NAMES.002 / WORLD.NAMES.003（方块名）",
        "- UNIT.NAMES.001（单位名）",
    ]
    return art, "02-world/W16-name-items.md", L


def doc5():
    ids = [u["id"] for u in sorted(UNITS, key=lambda r: r["id"])]
    total = len(ids)
    zh_hit = sum(1 for i in ids if names("unit", i)[2])
    art = "UNIT.NAMES.001"
    L = fm(art, "单位名对照：%d 个单位的英文名与中文名（其中 %d 个有官方简中）" % (total, zh_hit),
           ["00-data/units.json"],
           ["UNIT.MOVE.001", "UNIT.PRODUCE.001"],
           ["名词", "中文名", "英文名", "翻译", "对照表", "单位"])
    L += [
        "",
        "## 一句话",
        "",
        "单位的中文名与 id 对照。单位在界面只显示名字、不显示 id，而蓝图、逻辑、波次表只认 id，所以这张表是两边唯一的桥。",
        "",
        "## 规则 / 公式",
        "",
        "- 显示名 key 是 `unit.<id>.name`；数值在 `00-data/units.json`（血量、护甲、速度、射程等）。",
        "- 共 %d 条，%d 条有官方简中名；缺名的 %d 条集中在导弹子单位与几个内部占位单位。" % (total, zh_hit, total - zh_hit),
        "- 缺名单位（表内「—」）：导弹类 `*-missile`、`scathe-missile-*`，以及内部占位 `block` / `dummy` / `turret-unit-build-tower`；它们在实战中以弹药或建造塔出现，不单独显示名字。",
        "- 单位按 id 字母序排列；档次（T1～T5）与生产链见 UNIT.PRODUCE.001，不在这张表里。",
        "",
        "## 数值",
        "",
        "本节只列名词，不含数值；速度单位、hitSize、护甲等见 UNIT.MOVE.001 与 `00-data/units.json`。",
        "",
    ]
    L += table(ids, "unit")
    L += [
        "",
        "## 源码锚点",
        "",
        "- `assets/bundles/bundle_zh_CN.properties`（zh:N）与 `bundle.properties`（en:N）。",
        "- `00-data/units.json`：%d 条单位记录，`id` 与 bundle key 一一对应。" % total,
        "- 生成脚本 `knowledge/tools/gen_name_docs.py`。",
        "",
        "## 实测与反例",
        "",
        "- 反例一：单位名是意象词而不是功能名——`dagger`=尖刀、`mace`=战锤、`fortress`=堡垒、`scepter`=权杖、`reign`=王座。按「匕首」「锤子」搜中文名对不上。",
        "- 反例二：同一张表里两种命名策略并存——`anthicus` 官方中文是「天灾」（意译造词，不是音译的「安提库斯」），而 `alpha` / `beta` / `gamma` 是纯音译（阿尔法、贝塔、伽马）。",
        "- 反例三：`crawler`=爬虫、`atrax`=毒蛛，英文名与中文名都是意象；而 `alpha` / `beta` / `gamma` 直接保留希腊字母音译（阿尔法、贝塔、伽马）。",
        "- 反例四：导弹子单位（如 `anthicus-missile`）无显示名，按「导弹」反查只能查到发射它的单位 `anthicus`，不是它本身。",
        "",
        "## 常见误解",
        "",
        "- 以为单位名带 T1、T2：档次不是名字的一部分，官方串里没有等级字样。",
        "- 以为英文名可直译成 id：`Fortress` → `fortress` 可以，但 `Core: Shard` 这类带冒号的名字只出现在方块表。",
        "- 以为缺名单位是数据遗漏：%d 个缺名单位都有记录、有数值，只是语言包不显示名字。" % (total - zh_hit),
        "",
        "## 相关",
        "",
        "- UNIT.MOVE.001（速度单位与地形）",
        "- UNIT.PRODUCE.001（生产链与单位上限）",
        "- UNIT.AI.001（单位 AI 与指令）",
        "- UNIT.ABILITY.001（16 类 Ability）",
        "- UNIT.PROGRESSION.001（档次与波次表）",
        "- COMBAT.UNITWEAPON.001（单位武器与 DPS）",
        "- WORLD.NAMES.001 / 002 / 003 / 004（方块与物品名）",
    ]
    return art, "04-units/U06-name-units.md", L


def main(argv):
    check_only = "--check" in argv
    docs = [doc1(), doc2(), doc3(), doc4(), doc5()]
    bad = 0
    for art, rel, lines in docs:
        text = "\n".join(lines).replace("`", chr(96)) + "\n"
        n = text.count("\n")
        flag = "  <== 超过 %d 行" % MAX_LINES if n > MAX_LINES else ""
        if n > MAX_LINES:
            bad += 1
        print("%-14s %-42s %4d 行  %6d B%s" % (art, rel, n, len(text.encode("utf-8")), flag))
        if not check_only:
            p = KB / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    bhit, bzh, btot = coverage("block", [b["id"] for b in BLOCKS])
    uhit, uzh, utot = coverage("unit", [u["id"] for u in UNITS])
    print("覆盖: blocks 中文名 %d/%d, units 中文名 %d/%d" % (bzh, btot, uzh, utot))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
