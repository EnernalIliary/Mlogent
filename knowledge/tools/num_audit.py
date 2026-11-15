#!/usr/bin/env python3
"""num_audit.py - 数字审计：文章里的机制数值 vs 00-data 机读表，只出报告不改文章。

用法:
    python num_audit.py --root <知识库根> --out _report/num_audit.md
    python num_audit.py --root <知识库根> --json
    python check_kb.py --audit            # 等价（门禁跑完顺手出审计报告）

匹配规则（三条防假阳性，和 check_kb 的 E_NUM_CONFLICT 同款）:
  1. 实体名按词边界匹配，取行内最长命中（避免 production 里的 duct）；
  2. 实体必须先出现，标签在实体之后 40 字符内，数字紧跟标签 8 字符内；
  3. 表值哨兵 -1/None 跳过；turrets 只审计 range/reload/health/size（方块表里的
     armor 对炮塔无意义），units 只审计 health/armor/speed/range/itemCapacity。
判定: 偏差 = (文章-表值)/表值；|偏差| <= max(0.51, 2%) 或 |差| <= 0.51 → A_MATCH；
      tick 口径字段出现 60 倍关系 → A_SUSPECT；其余 A_MISMATCH。
输出: markdown（分组到文章，逐条 行/实体/字段/文章值/表值/偏差/判定/建议），末行 AUDIT_RESULT。
"""
import argparse
import json
import re
import sys
from pathlib import Path;

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import check_kb as CK  # noqa: E402

FENCE = chr(96) * 3
SKIP_PREFIX = ("|", "#", ">", "- [", FENCE, "* ", "  - ", "    -")
TABLE_FIELDS = {
    "blocks.json": ("health", "size", "armor", "itemCapacity"),
    "turrets.json": ("range", "reload", "health", "size"),
    "units.json": ("health", "armor", "speed", "range", "itemCapacity"),
}
# 同名字段在表中的优先级（炮塔的 range 只在 turrets.json；方块表优先给 size/health）
FIELD_PRIORITY = {
    "range": ("turrets.json", "units.json"),
    "reload": ("turrets.json",),
    "health": ("units.json", "turrets.json", "blocks.json"),
    "size": ("blocks.json", "turrets.json"),
    "armor": ("units.json", "blocks.json"),
    "speed": ("units.json",),
    "itemCapacity": ("units.json", "blocks.json"),
}
LABELS = {
    "health": ("血量", "生命值", "生命", "health", "HP"),
    "size": ("尺寸", "大小", "占地", "边长", "size"),
    "range": ("射程", "攻击距离", "range"),
    "reload": ("装填", "冷却", "射击间隔", "reload"),
    "armor": ("护甲", "装甲", "armor"),
    "speed": ("移速", "速度", "speed"),
    "itemCapacity": ("容量", "itemCapacity"),
}
TICK_FIELDS = {"reload"}
NUM_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])")
# 组件/能力类字段前缀：SuppressionField range 200、Weapon reload 等，不是单位/方块自身属性
COMPONENT_RE = re.compile(r"[A-Z][A-Za-z]*(?:Field|Ability|Mount|Weapon|Bullet|Cannon|Turret)\s*$", re.I)
SEP = " \t:=：为约*×xX（(／/~≈"

def _rel(path, root):
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")

def load_tables(root):
    """00-data 三表 -> {文件名: {实体名小写: 记录}}"""
    out = {}
    for name in TABLE_FIELDS:
        path = Path(root) / "00-data" / name
        if not path.is_file():
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            print("[warn] " + str(path) + " 解析失败: " + str(exc), file=sys.stderr)
            continue
        recs = doc.get("records") if isinstance(doc, dict) else doc
        if not isinstance(recs, list):
            continue
        index = {}
        for rec in recs:
            if not isinstance(rec, dict):
                continue
            for key in (rec.get("id"), rec.get("name")):
                key = str(key or "").strip().lower()
                if len(key) >= 2:
                    index.setdefault(key, rec)
        if index:
            out[name] = index
    return out

def find_entity(line_low, tables):
    """行内按词边界找最长实体名；返回 {表名: 记录}（同名实体可能在多表）。"""
    best_name = ""
    for index in tables.values():
        for name in index:
            if len(name) <= len(best_name):
                continue
            pos = line_low.find(name)
            while pos >= 0:
                end = pos + len(name)
                before = line_low[pos - 1] if pos else " "
                after = line_low[end] if end < len(line_low) else " "
                if before.isalnum() or before == "_" or after.isalnum() or after == "_":
                    pos = line_low.find(name, pos + 1)
                    continue
                best_name = name
                break
            if best_name == name:
                break
    if not best_name:
        return {}
    return {t: idx[best_name] for t, idx in tables.items() if best_name in idx}

def table_num(rec, field):
    v = CK._num(rec.get(field))
    if v is None or v <= -1:
        return None
    return v

def nearest_entity(low, pos, tables):
    """标签左侧 40 字符内、词边界成立的实体名；取"结束位置最近"的，其次取更长的。"""
    best = None  # (end, name)
    for idx in tables.values():
        for name in idx:
            start = max(0, pos - 40 - len(name))
            p = low.rfind(name, start, pos + 1)
            while p >= 0:
                end = p + len(name)
                before = low[p - 1] if p else " "
                after = low[end] if end < len(low) else " "
                if not (before.isalnum() or before == "_" or after.isalnum() or after == "_"):
                    if best is None or end > best[0] or (end == best[0] and len(name) > len(best[1])):
                        best = (end, name)
                    break
                p = low.rfind(name, start, p)
    return best[1] if best else None

def entity_after_number(low, end, tables):
    """匹配「armor 16 的 carbide-wall」这种 数字在前、实体在后的写法。"""
    head = low[end:end + 14]
    pos_of = head.find("的")  # 的
    if pos_of < 0:
        pos_of = head.find("of ")
        if pos_of < 0:
            return None
    rest = low[end + pos_of + 1:end + pos_of + 40]
    best = None
    for idx in tables.values():
        for name in idx:
            p = rest.find(name)
            if p < 0:
                continue
            end_n = p + len(name)
            before = rest[p - 1] if p else " "
            after = rest[end_n] if end_n < len(rest) else " "
            if before.isalnum() or before == "_" or after.isalnum() or after == "_":
                continue
            if best is None or p < best[0] or (p == best[0] and len(name) > len(best[1])):
                best = (p, name)
    return best[1] if best else None

def audit_line(line, tables):
    """返回 [(field, article_value, table, table_value)]；实体 = 标签左侧最近的词边界命中，
    或「标签 数字 的 实体」这种数字在前实体在后的写法。"""
    low = line.lower()
    out = []
    seen = set()
    for field, labels in LABELS.items():
        for lab in labels:
            pos = low.find(lab.lower())
            while pos >= 0:
                after = pos + len(lab)
                # 「container 声明 scaledHealth 55 ⇒ 220」是声明值 vs 结果值，不是属性值本身
                if re.search(r"scaledHealth|声明", low[max(0, pos - 40):pos]):
                    pos = low.find(lab.lower(), pos + 1)
                    continue
                # 源码锚点引用（world/Block.java:75 `public int itemCapacity = 10;`）不是实例属性
                if re.search(r"\.java:\d+", low[max(0, pos - 70):pos + 70]):
                    pos = low.find(lab.lower(), pos + 1)
                    continue
                # 「SuppressionField range 200」这类组件/能力字段不是单位属性，跳过
                if COMPONENT_RE.search(low[max(0, pos - 32):pos]):
                    pos = low.find(lab.lower(), pos + 1)
                    continue
                # speed 前 8 字符有「弹/bullet」时跳过：那是子弹速度不是单位速度
                if field == "speed" and ("弹" in low[max(0, pos - 8):pos] or "bullet" in low[max(0, pos - 12):pos]):
                    pos = low.find(lab.lower(), pos + 1)
                    continue
                name = nearest_entity(low, pos, tables)
                m = NUM_RE.search(line, after) if name else None
                if name and m and m.start() - after <= 8 and not line[after:m.start()].strip(SEP):
                    after_ent = entity_after_number(low, m.end(), tables)
                    if after_ent:
                        name = after_ent
                    cand = [t for t in FIELD_PRIORITY.get(field, ())
                            if name in tables.get(t, {}) and table_num(tables[t][name], field) is not None]
                    if cand and (pos, field) not in seen:
                        seen.add((pos, field))
                        out.append((field, float(m.group(1)), cand[0], table_num(tables[cand[0]][name], field)))
                pos = low.find(lab.lower(), pos + 1)
    return out

def scan(root):
    tables = load_tables(root)
    rows = []
    for path in CK.article_files(root, CK.Report(root)):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except Exception:
            continue
        meta, body, first = CK.parse_frontmatter(text)
        if meta is None:
            continue
        for i, line in enumerate(body.splitlines()):
            if len(line.strip()) < 4 or line.lstrip().startswith(SKIP_PREFIX):
                continue
            for field, av, table, tv in audit_line(line, tables):
                st, dev = classify(field, av, tv)
                rows.append({"file": _rel(path, root), "line": first + i, "field": field,
                             "article": av, "table_value": tv, "table_file": "00-data/" + table,
                             "state": st, "dev": dev})
    return rows, tables

def classify(field, av, tv):
    if tv == 0:
        return ("A_MATCH", 0.0) if not av else ("A_MISMATCH", 0.0)
    dev = (av - tv) / tv
    if field in TICK_FIELDS and abs(av / tv - 60) < 0.5:
        return ("A_SUSPECT", dev)
    if abs(av - tv) <= 0.51 or abs(dev) <= 0.02:
        return ("A_MATCH", dev)
    return ("A_MISMATCH", dev)

def fmt(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return ("%d" % f) if abs(f - round(f)) < 1e-9 else ("%.3f" % f).rstrip("0").rstrip(".")

def render(rows, root, tables):
    counts = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    out = ["# 数字审计报告（文章 vs 00-data）", "",
           "- 生成: num_audit.py  ·  知识库根: " + str(root),
           "- 可审计表: " + (", ".join("00-data/" + k for k in sorted(tables)) or "（无）"),
           "- 命中: %d 条，A_MATCH=%d  A_MISMATCH=%d  A_SUSPECT=%d" % (
               len(rows), counts.get("A_MATCH", 0), counts.get("A_MISMATCH", 0), counts.get("A_SUSPECT", 0)),
           ""]
    if not tables:
        out += ["> 00-data 无 blocks/turrets/units 表（canonical 未落地），本次无表可对拍。", "",
                "AUDIT_RESULT: NO_DATA"]
        return "\n".join(out)
    groups = {}
    for r in rows:
        groups.setdefault(r["file"], []).append(r)
    order = {"A_MISMATCH": 0, "A_SUSPECT": 1, "A_MATCH": 2}
    for path in sorted(groups):
        items = sorted(groups[path], key=lambda r: (order[r["state"]], r["line"]))
        bad = [r for r in items if r["state"] != "A_MATCH"]
        out += ["## " + path + "（%d 条，异常 %d）" % (len(items), len(bad)), "",
                "| 行 | 字段 | 文章值 | 表值 | 表 | 偏差 | 判定 | 建议 |",
                "|---:|---|---:|---:|---|---:|---|---|"]
        for r in items:
            sug = ""
            if r["state"] == "A_MISMATCH":
                sug = "改文章为 " + fmt(r["table_value"]) + "；若来自 v159.3 源码则双版本并列（v159.3=文章值 / v160.7=表值），若是换算值请补单位并标 [src:]"
            elif r["state"] == "A_SUSPECT":
                sug = "疑似 /tick 与 /s 混写，确认口径后归一"
            out.append("| %d | %s | %s | %s | %s | %s | %s | %s |" % (
                r["line"], r["field"], fmt(r["article"]), fmt(r["table_value"]), r["table_file"],
                ("%+.1f%%" % (r["dev"] * 100)) if r["table_value"] else "-", r["state"], sug))
        out.append("")
    out.append("AUDIT_RESULT: " + ("FAIL" if counts.get("A_MISMATCH") else "OK"))
    return "\n".join(out)

def default_out(root):
    return Path(root).resolve().parent / "_report" / "num_audit.md"

def run_audit(root, out=None, quiet=False):
    root = Path(root).resolve()
    rows, tables = scan(root)
    report = render(rows, root, tables)
    out = Path(out) if out else default_out(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report + "\n", encoding="utf-8")
    if not quiet:
        print("audit: " + str(out) + "  rows=" + str(len(rows)))
    return rows, out

def main(argv=None):
    ap = argparse.ArgumentParser(description="数字审计：文章数值 vs 00-data")
    ap.add_argument("--root", default=str(CK.DEFAULT_ROOT))
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    if args.json:
        rows, tables = scan(root)
        print(json.dumps({"root": str(root), "tables": sorted(tables), "rows": rows},
                         ensure_ascii=False, indent=1))
        return 0
    run_audit(root, args.out, quiet=args.quiet)
    return 0

if __name__ == "__main__":
    sys.exit(main())
