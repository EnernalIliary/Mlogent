# -*- coding: utf-8 -*-
"""scan_corpus.py -- 全量盘点 logic-corpus 下的 .msch 蓝图语料。

用途：MBO（Mindustry Blueprint Optimizer）第一阶段"蓝图层与语料"调研。
只读既有文件（tools/msch.py、data/game/blocks.json、logic-corpus/），
只写本目录下的 corpus_report.json。

运行：
    python -X utf8 MBO\\spikes\\bp\\scan_corpus.py

产出：
    MBO/spikes/bp/corpus_report.json   机器可读全量结果
    stdout                             摘要

分类启发式（详见产出文档 10-蓝图层与语料盘点.md）
------------------------------------------------
把每个方块按 data/game/blocks.json 的 category 归入 5 个桶：
    logic      -> category == "logic"           处理器/显示器/存储器/开关/消息
    prod       -> "production" | "crafting"     钻机/培养机/熔炉/混合机/制造机…
    logi       -> "distribution" | "liquid"     传送带/路由器/分拣器/管道/泵…
    power      -> "power"                       发电机/电池/电力节点
    other      -> "defense" | "turret" | "units" | "effect" | 未知名
factoryish = prod + logi + power（"工厂相关方块"）
factory_share = factoryish / tiles

    share == 0            -> "logic"   纯逻辑：只有处理器类（+少量墙体装饰）
    0 < share < 0.75      -> "hybrid"  混合：逻辑为主，夹带工厂方块
    share >= 0.75         -> "factory" 工厂型：主体是生产/物流/电力
无法解析的记为 "unparsed"。
"""

from __future__ import annotations

import json
import os
import struct
import sys
import time
import zlib
from collections import Counter, defaultdict
from dataclasses import dataclass

ROOT = r"F:\OneDrive\桌面\AtomicStates"
TOOLS = os.path.join(ROOT, "tools")
CORPUS = os.path.join(ROOT, "logic-corpus")
BLOCKS_JSON = os.path.join(ROOT, "data", "game", "blocks.json")
CONTENT_ID_SPACE: dict[str, set] = {}     # main() 里填充：v160.7 各 ContentType 的 id 集合
OUT_JSON = os.path.join(ROOT, "MBO", "spikes", "bp", "corpus_report.json")

sys.path.insert(0, TOOLS)
import msch  # noqa: E402  (已验证的解析器，禁止修改)

# ---------------------------------------------------------------- TypeIO 标签捕获
# msch 的 _read_object 把 list 类 config 一律返回成 Python list，丢掉了 TypeIO 标签
# （6=IntSeq / 8=Point2[] / 16=bool[] / 18=Vec2[] / 21=int[] / 22=Object[]），
# 而写回时必须知道原标签才能字节级还原。这里在运行期包装一层（不改 tools/msch.py）。
# 只有"顶层 config 是 list"时才记录；用 list 子类携带 tag，不破坏 isinstance 判断。


class TaggedList(list):
    __slots__ = ("tag",)

    def __init__(self, items=(), tag=None):
        super().__init__(items)
        self.tag = tag


class TaggedDouble(float):
    """T_DOUBLE(11) 与 T_FLOAT(3) 在 Python 里都读成 float，写回时会丢掉区别。"""
    __slots__ = ("tag",)

    def __new__(cls, value, tag=11):
        obj = float.__new__(cls, value)
        obj.tag = tag
        return obj


_orig_read_object = msch._read_object


def _tagged_read_object(r, depth=0):
    tag = r.data[r.pos] if r.pos < len(r.data) else None
    obj = _orig_read_object(r, depth)
    if depth == 0 and isinstance(obj, list) and not isinstance(obj, TaggedList):
        obj = TaggedList(obj, tag)
    elif depth == 0 and isinstance(obj, float) and not isinstance(obj, bool):
        if tag == 11:
            obj = TaggedDouble(obj, 11)
    return obj


msch._read_object = _tagged_read_object

# ---------------------------------------------------------------- 分类常量

BUCKET = {
    "logic": "logic",
    "production": "prod",
    "crafting": "prod",
    "distribution": "logi",
    "liquid": "logi",
    "power": "power",
}
OTHER_CATEGORIES = ("defense", "turret", "units", "effect")

FACTORY_SHARE_THRESHOLD = 0.75


def bucket_of(block_name: str, blocks: dict[str, dict]) -> str:
    info = blocks.get(block_name)
    if info is None:
        return "other"
    cat = info["category"]
    if cat in BUCKET:
        return BUCKET[cat]
    if cat in OTHER_CATEGORIES:
        return "other"
    return "other"


# ---------------------------------------------------------------- 工具

def canon(obj):
    """把 config 值转成可比较 / 可 JSON 化的规范形式。"""
    if isinstance(obj, dict):
        return tuple(sorted((k, canon(v)) for k, v in obj.items()))
    if isinstance(obj, (list, tuple)):
        return tuple(canon(v) for v in obj)
    if isinstance(obj, (bytes, bytearray)):
        return ("bytes", len(obj), zlib.crc32(bytes(obj)))
    return obj


def config_kind(cfg) -> str:
    """给 config 归类，用于统计"每种方块用什么类型的 config"。"""
    if cfg is None:
        return "null"
    if isinstance(cfg, bool):
        return "bool"
    if isinstance(cfg, int):
        return "int"
    if isinstance(cfg, float):
        return "double" if getattr(cfg, "tag", None) == 11 else "float"
    if isinstance(cfg, str):
        return "string"
    if isinstance(cfg, (bytes, bytearray)):
        return "bytearray"
    if isinstance(cfg, dict):
        for key in ("__content__", "__point__", "__building__",
                    "__laccess__", "__vec2__", "__team__", "__unit__"):
            if key in cfg:
                return key.strip("_")
        return "dict"
    if isinstance(cfg, (list, tuple)):
        tag = getattr(cfg, "tag", None)
        return f"array/tag{tag}" if tag is not None else "array"
    return type(cfg).__name__


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 2) if d else 0.0


def hist(values, bins) -> dict[str, int]:
    """values -> 计数；bins 是 (lo, hi) 闭区间列表，最后一箱带 +∞ 用 None 表示。"""
    out = {}
    for lo, hi in bins:
        label = f"{lo}+" if hi is None else f"{lo}-{hi}"
        if hi is None:
            out[label] = sum(1 for v in values if v >= lo)
        else:
            out[label] = sum(1 for v in values if lo <= v <= hi)
    return out


# ---------------------------------------------------------------- 扫描

def main() -> int:
    t0 = time.time()
    blocks_list = json.load(open(BLOCKS_JSON, encoding="utf-8"))
    blocks = {b["name"]: b for b in blocks_list}
    block_names = set(blocks)
    block_size = {b["name"]: b["size"] for b in blocks_list}

    # v160.7 各 ContentType 的合法 id 集合（用于检查 config 里的 Content id 是否越界）
    global CONTENT_ID_SPACE
    def _ids(fn: str) -> dict:
        p = os.path.join(ROOT, "data", "game", fn)
        if not os.path.exists(p):
            return {}
        return {c["id"]: c["name"] for c in json.load(open(p, encoding="utf-8"))}
    CONTENT_ID_SPACE = {
        "item": _ids("items.json"),
        "liquid": _ids("liquids.json"),
        "block": _ids("blocks.json"),
        "unit": _ids("units.json"),
    }

    # 找出所有 .msch
    files: list[str] = []
    for dirpath, _dirnames, filenames in os.walk(CORPUS):
        for fn in filenames:
            if fn.lower().endswith(".msch"):
                files.append(os.path.join(dirpath, fn))
    files.sort()

    per_file = []
    failures = []
    all_block_hist = Counter()
    factory_block_hist = Counter()
    logic_block_hist = Counter()
    missing_block_hist = Counter()          # 蓝图里出现、v160.7 blocks.json 里没有的名字
    missing_block_files = Counter()         # 含缺失方块的蓝图数（按方块名）
    config_kind_hist = Counter()            # 全语料 config 类型分布
    block_config_kinds: dict[str, Counter] = defaultdict(Counter)
    products = Counter()                    # 产品 -> 出现的蓝图数
    product_tiles = Counter()               # 产品 -> 生产该产物的方块数
    producer_blocks = Counter()             # 生产类方块 -> blueprint 数
    widths, heights, tile_counts, coverages = [], [], [], []
    files_with_missing = 0
    air_tiles_total = 0
    files_with_air = 0
    rt_ok = 0
    rt_fail: Counter = Counter()
    rt_fail_examples: list[dict] = []
    rt_ext_ok = 0
    rt_ext_fail: Counter = Counter()
    rt_ext_examples: list[dict] = []
    body_same = 0
    body_diff: list[dict] = []
    version_bytes = Counter()               # .msch 第 5 字节
    tag_keys = Counter()                    # 顶层 tag 键
    logic_ver = Counter()                   # 逻辑块内层 version 字节
    crafting_kinds = Counter()              # 每张图的"不同生产方块种数"
    crafted_blocks = {b["name"] for b in blocks_list
                      if b["category"] in ("production", "crafting")}
    pairs = Counter()                       # 同图共存的生产方块对（用于判断产线复杂度）
    tag_counts = Counter()
    content_cfg = Counter()                 # config 里的 Content 类型分布
    content_bad_ids = Counter()             # content id 在 v160.7 对应类型里越界
    content_ids: dict[tuple, list] = defaultdict(list)   # (ctype,id) -> 使用它的方块名
    oversized = []                          # 超出游戏 128x128 上限的蓝图
    unknown_categories = Counter()

    for path in files:
        rel = os.path.relpath(path, CORPUS).replace("\\", "/")
        pack = rel.split("/")[0]
        rec = {
            "path": rel,
            "pack": pack,
            "bytes": os.path.getsize(path),
        }
        try:
            sch = msch.parse_file(path)
        except Exception as exc:                      # noqa: BLE001
            reason = f"{type(exc).__name__}: {exc}"
            rec.update({"ok": False, "error": reason, "class": "unparsed"})
            per_file.append(rec)
            failures.append({"path": rel, "bytes": rec["bytes"], "error": reason[:300]})
            continue

        counts = sch.block_counts()
        total = len(sch.tiles)
        buckets = Counter()
        unknown_here = []
        for name, n in counts.items():
            if name not in block_names:
                unknown_here.append(name)
                missing_block_hist[name] += n
                missing_block_files[name] += 1
                b = "other"
            else:
                b = bucket_of(name, blocks)
            buckets[b] += n
            all_block_hist[name] += n
            if b == "logic":
                logic_block_hist[name] += n
            if b in ("prod", "logi", "power"):
                factory_block_hist[name] += n

        if unknown_here:
            files_with_missing += 1

        factoryish = buckets["prod"] + buckets["logi"] + buckets["power"]
        share = (factoryish / total) if total else 0.0
        if factoryish == 0:
            cls = "logic"
        elif share >= FACTORY_SHARE_THRESHOLD:
            cls = "factory"
        else:
            cls = "hybrid"

        # 产品线索
        prod_here = set()
        for name, n in counts.items():
            info = blocks.get(name)
            if not info:
                continue
            for out in info.get("outputs") or []:
                prod_here.add(out["name"])
                product_tiles[out["name"]] += n
            if info["category"] in ("production", "crafting"):
                producer_blocks[name] += 1
        for p in prod_here:
            products[p] += 1

        # 空间利用率代理：覆盖面积 / 包围盒面积
        cover = sum(block_size.get(n, 1) ** 2 * c for n, c in counts.items())
        box = max(1, sch.width * sch.height)

        # 逻辑块统计
        lg = sch.logic_tiles()
        stmts = sum(len(t.logic.statement_lines()) for t in lg if t.logic)
        links = sum(len(t.logic.links) for t in lg if t.logic)

        rec.update({
            "ok": True,
            "w": sch.width,
            "h": sch.height,
            "tiles": total,
            "class": cls,
            "factoryish_share": round(share, 4),
            "n_logic": buckets["logic"],
            "n_prod": buckets["prod"],
            "n_logi": buckets["logi"],
            "n_power": buckets["power"],
            "n_other": buckets["other"],
            "n_logic_tiles": len(lg),
            "logic_stmt_lines": stmts,
            "logic_links": links,
            "coverage": round(cover / box, 4),
            "tiles_per_area": round(total / box, 4),
            "missing_blocks": sorted(unknown_here),
            "products": sorted(prod_here),
            "blocks": counts,
            "tags": {k: (v[:120] if isinstance(v, str) else v) for k, v in sch.tags.items()},
            "labels": sch.labels,
        })

        per_file.append(rec)
        if sch.width > 128 or sch.height > 128:
            oversized.append({"path": rel, "w": sch.width, "h": sch.height, "tiles": total})
        widths.append(sch.width)
        heights.append(sch.height)
        tile_counts.append(total)
        version_bytes[str(sch.version)] += 1
        for k in sch.tags:
            tag_keys[k] += 1
        tag_counts[len(sch.tags)] += 1
        for t in lg:
            if t.logic is not None:
                logic_ver[f"v{t.logic.version}"] += 1
        ck = {n for n in counts if n in crafted_blocks}
        crafting_kinds[str(len(ck))] += 1
        for a in sorted(ck):
            pairs[a] += 1
        for name, c in counts.items():
            info = blocks.get(name)
            if info is None:
                unknown_categories["<unknown>"] += c
            else:
                unknown_categories[info["category"]] += c
        if "air" in counts:
            files_with_air += 1
            air_tiles_total += counts["air"]

        # config 类型统计（按方块）
        for t in sch.tiles:
            k = config_kind(t.config)
            config_kind_hist[k] += 1
            block_config_kinds[t.block][k] += 1
            if isinstance(t.config, dict) and "__content__" in t.config:
                ctype = t.config["__content__"]
                cid = t.config.get("id")
                content_cfg[ctype] += 1
                space = CONTENT_ID_SPACE.get(ctype)
                if space is not None and cid not in space:
                    content_bad_ids[ctype] += 1
                content_ids[(ctype, cid)].append(t.block)

        # 往返测试：解析 -> 写回 -> 再解析 -> 比对
        try:
            orig_body = zlib.decompress(open(path, "rb").read()[5:])
        except Exception:                             # noqa: BLE001
            orig_body = None
        rec_rt = roundtrip(sch, orig_body)
        rec["roundtrip"] = rec_rt
        if rec_rt["stock"]["ok"]:
            rt_ok += 1
        else:
            rt_fail[rec_rt["stock"]["reason"]] += 1
            if len(rt_fail_examples) < 12:
                rt_fail_examples.append({"path": rel, **rec_rt["stock"]})
        if rec_rt["ext"]["ok"]:
            rt_ext_ok += 1
        else:
            rt_ext_fail[rec_rt["ext"]["reason"]] += 1
            if len(rt_ext_examples) < 12:
                rt_ext_examples.append({"path": rel, **rec_rt["ext"]})
        if rec_rt.get("body_identical") is True:
            body_same += 1
        elif rec_rt.get("body_identical") is False and len(body_diff) < 10:
            body_diff.append({"path": rel,
                              "len_orig": rec_rt.get("body_len_orig"),
                              "len_mine": rec_rt.get("body_len_mine")})

    elapsed = time.time() - t0
    n = len(per_file)
    ok_n = sum(1 for r in per_file if r["ok"])
    parsed = [r for r in per_file if r["ok"]]
    by_class = Counter(r["class"] for r in per_file)
    factory = [r for r in parsed if r["class"] == "factory"]
    hybrid = [r for r in parsed if r["class"] == "hybrid"]
    logic_only = [r for r in parsed if r["class"] == "logic"]
    factory_prod = [r for r in factory if r["n_prod"] > 0]
    factory_pure_logistics = [r for r in factory if r["n_prod"] == 0]

    def med(vals):
        if not vals:
            return None
        s = sorted(vals)
        return s[len(s) // 2]

    report = {
        "meta": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "corpus_root": CORPUS,
            "blocks_json": BLOCKS_JSON,
            "blocks_json_count": len(blocks_list),
            "parser": os.path.join(TOOLS, "msch.py"),
            "classify_rule": {
                "buckets": {"logic": "category=logic",
                            "prod": "category in (production,crafting)",
                            "logi": "category in (distribution,liquid)",
                            "power": "category=power",
                            "other": "defense/turret/units/effect/unknown"},
                "factory": f"factoryish_share >= {FACTORY_SHARE_THRESHOLD}",
                "hybrid": "0 < factoryish_share < threshold",
                "logic": "factoryish_share == 0",
            },
            "elapsed_sec": round(elapsed, 2),
        },
        "summary": {
            "files_total": n,
            "parsed_ok": ok_n,
            "parse_failed": n - ok_n,
            "parse_ok_pct": pct(ok_n, n),
            "by_class": dict(by_class),
            "packs": dict(Counter(r["pack"] for r in per_file)),
            "total_tiles": sum(r.get("tiles", 0) for r in parsed),
            "width_range": [min(widths), max(widths)] if widths else None,
            "height_range": [min(heights), max(heights)] if heights else None,
            "width_hist": hist(widths, [(1, 8), (9, 16), (17, 32), (33, 64), (65, 128), (129, None)]),
            "height_hist": hist(heights, [(1, 8), (9, 16), (17, 32), (33, 64), (65, 128), (129, None)]),
            "tiles_hist": hist(tile_counts, [(1, 10), (11, 50), (51, 200), (201, 500),
                                             (501, 2000), (2001, None)]),
            "tiles_median": med(tile_counts),
            "tiles_max": max(tile_counts) if tile_counts else 0,
            "blueprints_with_logic": sum(1 for r in parsed if r["n_logic_tiles"] > 0),
            "blocks_with_logic_share_pct": pct(sum(1 for r in parsed if r["n_logic_tiles"] > 0), ok_n),
            "block_kinds_overall": len(all_block_hist),
            "block_kinds_factory": len(factory_block_hist),
            "block_kinds_logic": len(logic_block_hist),
            "factory_tiles_median": med([r["tiles"] for r in factory]),
            "factory_coverage_median": med([r["coverage"] for r in factory]),
            "factory_tiles_per_area_median": med([r["tiles_per_area"] for r in factory]),
            "factory_with_prod": len(factory_prod),
            "factory_pure_logistics": len(factory_pure_logistics),
            "factory_with_prod_no_logic": sum(1 for r in factory_prod if r["n_logic_tiles"] == 0),
            "factory_with_prod_coverage_ge_090": sum(1 for r in factory_prod
                                                     if r["coverage"] >= 0.90),
            "factory_with_prod_and_logic": sum(1 for r in factory_prod if r["n_logic_tiles"] > 0),
            "hybrid_tiles_median": med([r["tiles"] for r in hybrid]),
            "logic_tiles_median": med([r["tiles"] for r in logic_only]),
            "factory_tiles_sum": sum(r["tiles"] for r in factory),
            "factory_products": dict(sorted(products.items(), key=lambda kv: -kv[1])),
            "factory_product_kinds": len(products),
            "files_with_missing_blocks": files_with_missing,
            "files_with_missing_blocks_pct": pct(files_with_missing, ok_n),
            "missing_block_kinds": len(missing_block_hist),
            "missing_block_affects_factory": sum(
                1 for r in factory if r["missing_blocks"]),
            "files_with_air_tiles": files_with_air,
            "air_tiles_total": air_tiles_total,
            "roundtrip_ok": rt_ok,
            "roundtrip_ok_pct": pct(rt_ok, ok_n),
            "roundtrip_fail_reasons": dict(rt_fail),
            "roundtrip_ext_ok": rt_ext_ok,
            "roundtrip_ext_ok_pct": pct(rt_ext_ok, ok_n),
            "roundtrip_ext_fail_reasons": dict(rt_ext_fail),
            "body_identical": body_same,
            "body_identical_pct": pct(body_same, ok_n),
            "oversized_over_128": [{"path": o["path"], "w": o["w"], "h": o["h"], "tiles": o["tiles"]}
                                   for o in oversized],
            "content_config_types": dict(content_cfg.most_common()),
            "content_id_out_of_range": dict(content_bad_ids),
            "content_ids_top": [
                {"type": t, "id": i, "name": CONTENT_ID_SPACE.get(t, {}).get(i),
                 "count": len(bs), "blocks": sorted(set(bs))[:4]}
                for (t, i), bs in sorted(content_ids.items(), key=lambda kv: -len(kv[1]))[:20]
            ],
            "msch_version_bytes": dict(version_bytes),
            "tag_keys": dict(tag_keys.most_common()),
            "tag_counts": dict(sorted(tag_counts.items())),
            "logic_payload_versions": dict(logic_ver.most_common()),
            "crafting_kinds_per_blueprint": dict(sorted(crafting_kinds.items(), key=lambda kv: int(kv[0]))),
        },
        "largest_blueprints": [
            {"path": r["path"], "w": r["w"], "h": r["h"], "tiles": r["tiles"],
             "class": r["class"], "products": r["products"]}
            for r in sorted(parsed, key=lambda x: -x["tiles"])[:8]
        ],
        "factory_by_pack": dict(Counter(r["pack"] for r in factory).most_common()),
        "prod_block_blueprint_counts": dict(producer_blocks.most_common()),
        "body_diff_examples": body_diff,
        "roundtrip_fail_examples": rt_fail_examples,
        "roundtrip_ext_fail_examples": rt_ext_examples,
        "failures": failures,
        "categories_tiles": dict(unknown_categories.most_common()),
        "config_kind_hist": dict(config_kind_hist.most_common()),
        "block_config_kinds": {
            b: dict(c.most_common()) for b, c in
            sorted(block_config_kinds.items(), key=lambda kv: -sum(kv[1].values()))
        },
        "block_hist_all_top50": dict(all_block_hist.most_common(50)),
        "block_hist_factory_top50": dict(factory_block_hist.most_common(50)),
        "block_hist_logic": dict(logic_block_hist.most_common(30)),
        "producer_blocks": dict(producer_blocks.most_common()),
        "missing_blocks": dict(missing_block_hist.most_common()),
        "missing_block_files": dict(missing_block_files.most_common()),
        "files": per_file,
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)

    print_summary(report)
    print(f"\n[written] {OUT_JSON}")
    return 0


def _write_object_ext(out: bytearray, obj) -> None:
    """TypeIO.writeObject 的完整版：补上 msch._write_object 缺的 list/dict 分支。

    分支依据 Mindustry-Source core/src/mindustry/io/TypeIO.java:42-155。
    """
    if obj is None:
        out.append(0)
    elif isinstance(obj, bool):
        out.append(10)
        out.append(1 if obj else 0)
    elif isinstance(obj, int):
        out.append(1)
        out += struct.pack(">i", obj)
    elif isinstance(obj, float):
        if getattr(obj, "tag", None) == 11:
            out.append(11)
            out += struct.pack(">d", float(obj))
        else:
            out.append(3)
            out += struct.pack(">f", float(obj))
    elif isinstance(obj, str):
        out.append(4)
        out.append(1)
        sb = obj.encode("utf-8")
        out += struct.pack(">H", len(sb)) + sb
    elif isinstance(obj, (bytes, bytearray)):
        out.append(14)
        out += struct.pack(">i", len(obj)) + bytes(obj)
    elif isinstance(obj, dict) and "__content__" in obj:
        out.append(5)
        out.append(msch.CONTENT_TYPES.index(obj["__content__"]))
        out += struct.pack(">h", obj["id"])
    elif isinstance(obj, dict) and "__point__" in obj:
        out.append(7)
        out += struct.pack(">ii", *obj["__point__"])
    elif isinstance(obj, dict) and "__technode__" in obj:
        ctype, cid = obj["__technode__"]
        out.append(9)
        out.append(ctype)
        out += struct.pack(">h", cid)
    elif isinstance(obj, dict) and "__building__" in obj:
        out.append(12)
        out += struct.pack(">i", obj["__building__"])
    elif isinstance(obj, dict) and "__laccess__" in obj:
        out.append(13)
        out += struct.pack(">h", obj["__laccess__"])
    elif isinstance(obj, dict) and "__unit__" in obj:
        out.append(17)
        out += struct.pack(">i", obj["__unit__"])
    elif isinstance(obj, dict) and "__vec2__" in obj:
        out.append(19)
        out += struct.pack(">ff", *obj["__vec2__"])
    elif isinstance(obj, dict) and "__team__" in obj:
        out.append(20)
        out.append(obj["__team__"] & 0xFF)
    elif isinstance(obj, dict) and "__unitcommand__" in obj:
        out.append(23)
        out += struct.pack(">H", obj["__unitcommand__"])
    elif isinstance(obj, (list, tuple)):
        tag = getattr(obj, "tag", None) or 6
        if tag in (6, 21):                     # IntSeq / int[] 都是 short 长度 + int[]
            out.append(tag)
            out += struct.pack(">h", len(obj))
            for v in obj:
                out += struct.pack(">i", v)
        elif tag == 8:                          # Point2[]（byte 长度，元素是 packed int）
            out.append(8)
            out.append(len(obj) & 0xFF)
            for v in obj:
                if isinstance(v, dict) and "__point__" in v:
                    vx, vy = v["__point__"]
                elif isinstance(v, (tuple, list)) and len(v) == 2:
                    vx, vy = v
                else:
                    out += struct.pack(">i", v)
                    continue
                out += struct.pack(">I", (((vx & 0xFFFF) << 16) | (vy & 0xFFFF)) & 0xFFFFFFFF)
        elif tag == 16:                         # boolean[]（int 长度）
            out.append(16)
            out += struct.pack(">i", len(obj))
            for v in obj:
                out.append(1 if v else 0)
        elif tag == 18:                         # Vec2[]（short 长度，两 float）
            out.append(18)
            out += struct.pack(">h", len(obj))
            for v in obj:
                vx, vy = v["__vec2__"] if isinstance(v, dict) else v
                out += struct.pack(">ff", vx, vy)
        elif tag == 22:                         # Object[]（int 长度，递归）
            out.append(22)
            out += struct.pack(">i", len(obj))
            for v in obj:
                _write_object_ext(out, v)
        else:
            raise msch.MschError(f"unsupported array tag {tag}")
    else:
        raise msch.MschError(f"cannot serialize config of type {type(obj).__name__}")


def build_schematic_ext(sch) -> bytes:
    """msch.build_schematic 的完整写回版（同一 wire 格式，仅补全 config 类型）。"""
    body = bytearray()
    body += struct.pack(">hh", sch.width, sch.height)
    tags = sch.tags
    body.append(len(tags) & 0xFF)
    for k, v in tags.items():
        for s in (k, v):
            sb = str(s).encode("utf-8")
            body += struct.pack(">H", len(sb)) + sb

    names: list[str] = []
    for t in sch.tiles:
        if t.block not in names:
            names.append(t.block)
    body.append(len(names) & 0xFF)
    for n in names:
        nb = n.encode("utf-8")
        body += struct.pack(">H", len(nb)) + nb

    body += struct.pack(">i", len(sch.tiles))
    for t in sch.tiles:
        body.append(names.index(t.block) & 0xFF)
        body += struct.pack(">i", ((t.x & 0xFFFF) << 16) | (t.y & 0xFFFF))
        _write_object_ext(body, t.config)
        body.append(t.rotation & 0xFF)

    return msch.MAGIC + bytes([msch.CURRENT_VERSION]) + zlib.compress(bytes(body), 9)


def roundtrip(sch, orig_body: bytes | None = None) -> dict:
    """解析 -> 写回 -> 再解析，比对 tile 集合与 config。

    返回两个结果：
      stock : 用 tools/msch.build_schematic（只覆盖 7 种 config 类型）
      ext   : 用本脚本的完整写回器（覆盖语料里出现的全部 TypeIO 类型）
      body_identical : 写回后未压缩 body 是否与文件原始 body 逐字节相同
                       （最强的保真度证据；None = 未测）
    """
    want = sorted((t.block, t.x, t.y, t.rotation, canon(t.config)) for t in sch.tiles
                  if t.block != "air")
    out = {}

    for label, builder in (("stock", msch.build_schematic),
                           ("ext", build_schematic_ext)):
        try:
            if label == "stock":
                data = builder(sch.width, sch.height, sch.tags, sch.tiles)
            else:
                data = builder(sch)
        except Exception as exc:                      # noqa: BLE001
            out[label] = {"ok": False, "reason": f"serialize: {type(exc).__name__}: {exc}"[:160]}
            continue
        try:
            back = msch.parse_bytes(data)
        except Exception as exc:                      # noqa: BLE001
            out[label] = {"ok": False, "reason": f"reparse: {type(exc).__name__}: {exc}"[:160]}
            continue
        if (back.width, back.height) != (sch.width, sch.height):
            out[label] = {"ok": False, "reason": "dims mismatch"}
            continue
        got = sorted((t.block, t.x, t.y, t.rotation, canon(t.config)) for t in back.tiles)
        if got == want:
            out[label] = {"ok": True, "bytes": len(data)}
        else:
            out[label] = {"ok": False, "reason": "tile/config mismatch"}
        if label == "ext" and orig_body is not None:
            try:
                mine = zlib.decompress(data[5:])
                out["body_identical"] = mine == orig_body
                if mine != orig_body:
                    out["body_len_orig"] = len(orig_body)
                    out["body_len_mine"] = len(mine)
            except Exception:                         # noqa: BLE001
                out["body_identical"] = None

    out["ok"] = out["stock"]["ok"]        # 兼容旧字段
    out["reason"] = out["stock"].get("reason", "")
    return out



def print_summary(r: dict) -> None:
    s = r["summary"]
    print("=" * 72)
    print("MBO 蓝图层语料盘点（logic-corpus/*.msch）")
    print("=" * 72)
    print(f"文件总数       : {s['files_total']}")
    print(f"解析成功       : {s['parsed_ok']} ({s['parse_ok_pct']}%)  "
          f"失败 {s['parse_failed']}")
    for f in r["failures"]:
        print(f"  ! {f['path']}  [{f['bytes']} B]  {f['error'][:100]}")
    print(f"分类           : {s['by_class']}")
    print(f"tile 总数      : {s['total_tiles']}  (median {s['tiles_median']}, max {s['tiles_max']})")
    print(f"尺寸范围       : 宽 {s['width_range']}  高 {s['height_range']}")
    print(f"宽直方图       : {s['width_hist']}")
    print(f"高直方图       : {s['height_hist']}")
    print(f"tile 直方图    : {s['tiles_hist']}")
    print(f"含逻辑块蓝图   : {s['blueprints_with_logic']} ({s['blocks_with_logic_share_pct']}%)")
    print(f"方块种类(全体) : {s['block_kinds_overall']}  "
          f"(工厂型 {s['block_kinds_factory']} / 逻辑型 {s['block_kinds_logic']})")
    print(f"工厂型 tile 中位: {s['factory_tiles_median']}  "
          f"覆盖率中位 {s['factory_coverage_median']}  "
          f"tile/面积中位 {s['factory_tiles_per_area_median']}")
    print(f"工厂型细分     : 含生产方块 {s['factory_with_prod']} / "
          f"纯物流电力 {s['factory_pure_logistics']} / "
          f"其中有生产且无逻辑 {s['factory_with_prod_no_logic']} / "
          f"覆盖率>=0.90 {s['factory_with_prod_coverage_ge_090']}")
    print(f"混合型 tile 中位: {s['hybrid_tiles_median']}  "
          f"逻辑型 tile 中位: {s['logic_tiles_median']}")
    print(f"\n-- 工厂型产物线索（产品 -> 蓝图数）--")
    print(json.dumps(s["factory_products"], ensure_ascii=False))
    print(f"\n-- 工厂型方块 TOP20 --")
    for k, v in list(r["block_hist_factory_top50"].items())[:20]:
        print(f"  {v:6d} {k}")
    print(f"\n-- 逻辑型方块 --")
    print(json.dumps(r["block_hist_logic"], ensure_ascii=False))
    print(f"\n-- 缺失方块（v160.7 blocks.json 中不存在）--")
    print(f"受影响蓝图 {s['files_with_missing_blocks']} 张 "
          f"({s['files_with_missing_blocks_pct']}%)，缺失名 {s['missing_block_kinds']} 种")
    print(json.dumps(r["missing_blocks"], ensure_ascii=False)[:1200])
    print(f"\n-- config 类型分布 --")
    print(json.dumps(r["config_kind_hist"], ensure_ascii=False))
    print(f"\n-- 往返测试 --")
    print(f"stock build_schematic : {s['roundtrip_ok']}/{s['parsed_ok']} "
          f"({s['roundtrip_ok_pct']}%)")
    print(json.dumps(s["roundtrip_fail_reasons"], ensure_ascii=False)[:800])
    print(f"完整写回器(本脚本)    : {s['roundtrip_ext_ok']}/{s['parsed_ok']} "
          f"({s['roundtrip_ext_ok_pct']}%)")
    print(json.dumps(s["roundtrip_ext_fail_reasons"], ensure_ascii=False)[:800])
    print(f"未压缩 body 逐字节相同 : {s['body_identical']}/{s['parsed_ok']} "
          f"({s['body_identical_pct']}%)")
    for d in r["body_diff_examples"][:5]:
        print(f"  ~ {d['path']}  len {d['len_orig']} -> {d['len_mine']}")
    for e in r["roundtrip_fail_examples"][:6]:
        print(f"  ! stock {e['path']}: {e['reason']}")
    for e in r["roundtrip_ext_fail_examples"][:6]:
        print(f"  ! ext   {e['path']}: {e['reason']}")
    print(f"\n-- 格式 --")
    print(f".msch 版本字节 : {s['msch_version_bytes']}   tag 数分布: {s['tag_counts']}")
    print(f"tag 键出现次数 : {s['tag_keys']}")
    print(f"逻辑内层版本   : {s['logic_payload_versions']}")
    print(f"Content config 类型: {s['content_config_types']}   越界 id: {s['content_id_out_of_range']}")
    print(f"超出游戏 128x128 上限: {len(s['oversized_over_128'])} 张")
    for o in s["oversized_over_128"]:
        print(f"  ! {o['w']}x{o['h']} tiles={o['tiles']} {o['path']}")
    print(f"每图生产方块种数: {s['crafting_kinds_per_blueprint']}")
    print(f"\n-- 各 pack --")
    print(json.dumps(s["packs"], ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
