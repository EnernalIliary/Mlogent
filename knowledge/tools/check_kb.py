#!/usr/bin/env python3
"""check_kb.py — knowledge/ 静态门禁（零第三方依赖）。

用法:
    python knowledge/tools/check_kb.py                  # 默认检查 <knowledge>/ 自身
    python knowledge/tools/check_kb.py --root ../knowledge
    python knowledge/tools/check_kb.py --json           # 机器可读
    python knowledge/tools/check_kb.py --write-tokens   # 回填 frontmatter tokens

退出码: 0 = 无 error；1 = 有 error；2 = 环境问题（找不到根目录）。

检查项（task-12 的 1-6）:
  1 frontmatter 必填 8 字段齐全；id 唯一且匹配 DOMAIN.SUB.NNN（域码固定）
  2 七段模板小节齐全
  3 frontmatter data: 引用的 00-data 文件存在（#fragment 校验降级为 warning）
  4 数字声明行是否带来源标记（[src: / [实测 / [ver / [v1xx / 见 DATA / 00-data/）-> warning
  5 双版本字段合法（ver 必须是列表，元素属于 v159.3/v160.7/v159.3_src/v160.7_rt）
  6 相对链接可达、相关小节引用的 ID 存在
契约：knowledge/CONVENTIONS.md 与 VERSION.md（本脚本不自行放宽）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parent
FENCE = chr(96) * 3

DOMAINS = {
    "01-execution": ("EXEC", "执行模型", "处理器 / 指令预算 / 帧差 / 同步"),
    "02-world": ("WORLD", "世界与物流", "方块 / 传送带 / 电力 / 液体 / 热 / 钻探"),
    "03-combat": ("COMBAT", "战斗", "弹道 / 伤害 / 护甲 / 状态 / 炮塔"),
    "04-units": ("UNIT", "单位", "单位 / AI / 能力 / 生产"),
    "05-campaign": ("CAMP", "战役", "波次 / 规则 / 胜负"),
    "06-mlog": ("MLOG", "逻辑语言", "语法 / 指令 / 陷阱"),
    "07-patterns": ("PATTERN", "蓝图模式", "架构 / idiom / 反模式"),
    "08-evidence": ("EV", "证据", "claims / probes / bench"),
}

# CONVENTIONS 的 domain 用短名（与 ID 前缀一致）；目录名只用于路径校验
DOMAIN_SHORT = {
    "01-execution": "exec", "02-world": "world", "03-combat": "combat",
    "04-units": "unit", "05-campaign": "camp", "06-mlog": "mlog",
    "07-patterns": "pattern", "08-evidence": "evidence",
}
ALLOWED_DOMAINS = set(DOMAIN_SHORT.values()) | {"data"}

REQUIRED_FIELDS = ["id", "title", "domain", "status", "ver", "conf", "src", "data"]
STATUS_OK = {"active", "draft", "deprecated"}
CONF_OK = {"S", "E", "I", "U"}
VER_OK = {"v159.3", "v160.7", "v159.3_src", "v160.7_rt"}

ID_RE = re.compile(r"^(EXEC|WORLD|COMBAT|UNIT|CAMP|MLOG|PATTERN|DATA|EV)\.[A-Z][A-Z0-9_]*\.\d{3}$")
SECTIONS = [
    ("一句话", r"^##\s*一句话"),
    ("规则/公式", r"^##\s*规则\s*[/／]?\s*公式"),
    ("数值", r"^##\s*数值"),
    ("源码锚点", r"^##\s*源码锚点"),
    ("实测与反例", r"^##\s*实测与反例"),
    ("常见误解", r"^##\s*常见误解"),
    ("相关", r"^##\s*相关"),
]
SRC_MARKERS = ("[src:", "[实测", "[ver", "[v159", "[v160", "见 DATA", "见数据表",
               "00-data/", "DATA#", "src:", "ver:", "conf:")
NUM_CLAIM_RE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:/s|/tick|/秒|items?/s|%|格|秒|tick|帧|MB|KB|B)\b|\d+\.\d+")

def _split_inline_list(s: str) -> list:
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    out, cur, q = [], "", None
    for ch in s:
        if q:
            cur += ch
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
            cur += ch
        elif ch == ",":
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return [_unquote(x) for x in out if x.strip()]

def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s

def parse_frontmatter(text: str):
    """返回 (meta|None, body, body_start_line)。只解析本库用到的 YAML 子集。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text, 1
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, text, 1
    meta = {}
    key = None
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if re.match(r"^\s+-\s+", raw):
            val = _unquote(raw.strip()[1:].strip())
            if key is None:
                continue
            if not isinstance(meta.get(key), list):
                meta[key] = []
            meta[key].append(val)
        elif re.match(r"^\s+\S", raw):
            if key:
                meta.setdefault(key + "__raw", []).append(raw.strip())
        else:
            m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", raw)
            if not m:
                continue
            key, rest = m.group(1), m.group(2).strip()
            if rest == "":
                meta[key] = []
            elif rest.startswith("["):
                meta[key] = _split_inline_list(rest)
            else:
                meta[key] = _unquote(rest)
    body = "\n".join(lines[end + 1:])
    return meta, body, end + 2

def estimate_tokens(text: str) -> int:
    """粗略 token 估算（汉字 0.62 / 英文词 0.75），用于 index.json 与 frontmatter 回填。"""
    han = len(re.findall(r"[\u4e00-\u9fff]", text))
    words = len(re.findall(r"[A-Za-z0-9_.]{2,}", text))
    return max(1, int(round(han * 0.62 + words * 0.75)))

# ---------------------------------------------------------------- 报告容器
class Report:
    """收集 error/warning 与统计。记录同时保留给 --json 输出。"""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.errors = []
        self.warnings = []
        self.n_files = 0
        self.n_bytes = 0
        self.n_tokens = 0
        self.ids = {}
        self.domain_counts = {}
        self.data_tables = []

    def _rec(self, level, path, line, code, msg):
        try:
            rel = str(Path(path).resolve().relative_to(self.root.resolve())).replace("\\", "/")
        except Exception:
            rel = str(path).replace("\\", "/")
        rec = {"level": level, "path": rel, "line": int(line or 0), "code": code, "msg": msg}
        (self.errors if level == "error" else self.warnings).append(rec)
        return rec

    def err(self, path, line, code, msg):
        return self._rec("error", path, line, code, msg)

    def warn(self, path, line, code, msg):
        return self._rec("warning", path, line, code, msg)

    def as_dict(self):
        return {
            "root": str(self.root),
            "files": self.n_files,
            "bytes": self.n_bytes,
            "tokens": self.n_tokens,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "ids": len(self.ids),
            "domain_counts": self.domain_counts,
            "data_tables": self.data_tables,
            "error_list": self.errors,
            "warning_list": self.warnings,
        }

# ---------------------------------------------------------------- 文件发现
def article_files(root: Path, rep: Report):
    """只扫 01..08 域目录下的 md；根目录的契约文件（CONVENTIONS/VERSION/README）不参与。"""
    out = []
    for d in DOMAINS:
        dd = root / d
        if not dd.is_dir():
            rep.warn(root / d, 0, "W_DOMAIN_DIR_MISSING", "域目录缺失: " + d)
            continue
        # 任何以下划线开头的路径段（_report/、_probe_*）都不参与门禁
        files = sorted(p for p in dd.rglob("*.md")
                       if p.is_file() and not p.name.startswith("_")
                       and not any(seg.startswith("_")
                                   for seg in p.relative_to(root).parts[:-1])
                       and p.name.lower() != "readme.md")
        if not files:
            rep.warn(dd, 0, "W_DOMAIN_EMPTY", "域目录无文章: " + d)
        out.extend(files)
    return out

# ---------------------------------------------------------------- 数值冲突
NUM_LABELS = {
    "health": ("血量", "health", "生命值"),
    "size": ("尺寸", "size"),
    "range": ("射程", "range"),
}
_STAT_CACHE = {}

def _num(v):
    if isinstance(v, dict):
        v = v.get("v")
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def stat_tables(root: Path) -> dict:
    """00-data/{blocks,turrets}.json → {文件名: {name_lower: record}}（进程内缓存）。"""
    key = str(root)
    if key in _STAT_CACHE:
        return _STAT_CACHE[key]
    out = {}
    for fn in ("blocks.json", "turrets.json"):
        p = root / "00-data" / fn
        if not p.is_file():
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
        except Exception:
            continue
        recs = obj
        if isinstance(obj, dict):
            for k in ("records", "items", "entries", "rows", "data"):
                if isinstance(obj.get(k), list):
                    recs = obj[k]
                    break
            else:
                recs = []
        m = {}
        for r in recs:
            if isinstance(r, dict):
                nm = r.get("name") or r.get("id")
                if nm:
                    m[str(nm).lower()] = r
        if m:
            out[fn] = m
    _STAT_CACHE[key] = out
    return out

def check_num_conflicts(path, body, first_line, tables, rep) -> int:
    """粗查：同一行出现「实体名 + 血量/尺寸/射程 标签」且数字与 00-data 冲突 → E_NUM_CONFLICT。

    覆盖范围：00-data/blocks.json 与 turrets.json 的 health/size/range 三个字段。
    要求实体名与标签相距 <40 字符，避免散文数字误判；相对误差容忍 max(0.51, 2%)。
    """
    hits = 0
    if not tables:
        return 0
    for lineno, ln, in_fence in _iter_body_lines(body, first_line):
        if in_fence or len(ln) < 8:
            continue
        low = ln.lower()
        for field, labels in NUM_LABELS.items():
            hit_label = None
            for lab in labels:
                # ASCII 标签必须独立成词（避免 synthesizer 里的 size 之类假阳性）
                if lab.isascii():
                    m_lab = re.search(r"(?<![A-Za-z0-9_-])" + re.escape(lab) + r"(?![A-Za-z0-9_-])", low)
                    li = m_lab.start() if m_lab else -1
                else:
                    li = ln.find(lab)
                if li >= 0:
                    hit_label = (lab, li)
                    break
            if not hit_label:
                continue
            lab, li = hit_label
            for tbl, recs in tables.items():
                for name, rec in recs.items():
                    if len(name) < 3:
                        continue
                    # 实体名必须独立成词（避免 production 里命中 duct 之类的假阳性）
                    nm = re.search(r"(?<![A-Za-z0-9_-])" + re.escape(name) + r"(?![A-Za-z0-9_-])", low)
                    if not nm:
                        continue
                    ni = nm.start()
                    if abs(ni - li) > 40:
                        continue
                    want = _num(rec.get(field))
                    if want is None:
                        continue
                    # 数字必须紧跟标签、且标签在实体名之后（"duo: health 250" / "duo 血量 250"）
                    tail = ln[max(ni, li):]
                    m = re.search(re.escape(lab) + r"[^0-9\n]{0,14}(-?\d+(?:\.\d+)?)", tail)
                    if not m:
                        continue
                    got = float(m.group(1))
                    if abs(got - want) > max(0.51, abs(want) * 0.02):
                        rep.err(path, lineno, "E_NUM_CONFLICT",
                                "%s 的 %s：文章写 %g，00-data/%s 为 %g" % (name, field, got, tbl, want))
                        hits += 1
                    break
    return hits

# ---------------------------------------------------------------- 单篇校验
LINK_RE = re.compile(r"(?<!\!)\[(?:[^\]\n]{0,120})\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
TOKENS_LINE_RE = re.compile(r"^tokens\s*:\s*(.*)$", re.M)

def _iter_body_lines(body: str, first_line: int):
    """产出 (行号, 行文本, 是否在围栏代码块内)。"""
    in_fence = False
    for i, ln in enumerate(body.splitlines()):
        s = ln.strip()
        if s.startswith(FENCE):
            in_fence = not in_fence
            yield first_line + i, ln, True
            continue
        yield first_line + i, ln, in_fence

# data-dump 的正式表名；rt_* 抽查文件不算「数据层已落地」
CANONICAL_DATA_TABLES = ("blocks.json", "turrets.json", "units.json", "items.json",
                         "liquids.json", "bullets.json", "status.json", "rules.json")

def data_layer_ready(root: Path) -> bool:
    """00-data 数据层是否已落地：canonical 表存在且带非空 records 列表。"""
    dd = root / "00-data"
    if not dd.is_dir():
        return False
    for name in CANONICAL_DATA_TABLES:
        p = dd / name
        if not p.is_file():
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
        except Exception:
            continue
        recs = obj.get("records") if isinstance(obj, dict) else obj
        if isinstance(recs, list) and recs:
            return True
    return False

def check_article(path: Path, root: Path, rep: Report, pending_refs: list, write_tokens: bool,
                  strict: bool = False, data_ready: bool = False):
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    raw = path.read_bytes()
    rep.n_files += 1
    rep.n_bytes += len(raw)

    meta, body, first_line = parse_frontmatter(text)
    if meta is None:
        rep.err(path, 1, "E_NO_FRONTMATTER", "缺少 frontmatter（首行必须是 ---）")
        return

    # 1 必填字段（data/depends/tags 允许空列表：表示"本文不引用数据表"）
    empty_ok = {"data", "depends", "tags"}
    for f in REQUIRED_FIELDS:
        v = meta.get(f)
        if v is None or (isinstance(v, str) and not v.strip()) or (
                isinstance(v, list) and not v and f not in empty_ok):
            rep.err(path, 1, "E_MISSING_FIELD", "frontmatter 缺必填字段: " + f)

    art_id = meta.get("id")
    if isinstance(art_id, str) and art_id.strip():
        art_id = art_id.strip()
        if not ID_RE.match(art_id):
            rep.err(path, 1, "E_ID_FORMAT", "id 格式非法: " + art_id + "（应为 DOMAIN.SUB.NNN，域码固定）")
        if art_id in rep.ids:
            rep.err(path, 1, "E_ID_DUP", "id 重复: " + art_id + "（已被 " + rep.ids[art_id] + " 使用）")
        else:
            rep.ids[art_id] = str(path.name)

    dom = meta.get("domain")
    dom_dir = path.parent.name
    if isinstance(dom, str) and dom.strip():
        dom = dom.strip()
        if dom not in ALLOWED_DOMAINS:
            rep.err(path, 1, "E_DOMAIN", "domain 非法: " + dom + "（允许短名: " + ", ".join(sorted(ALLOWED_DOMAINS)) + "）")
        else:
            want = DOMAIN_SHORT.get(dom_dir)
            if want and dom != want:
                rep.err(path, 1, "E_DOMAIN_DIR", "domain=" + dom + " 与所在目录 " + dom_dir + " 的短名 " + want + " 不一致")
        rep.domain_counts[dom_dir] = rep.domain_counts.get(dom_dir, 0) + 1

    st = meta.get("status")
    if isinstance(st, str) and st not in STATUS_OK:
        rep.err(path, 1, "E_STATUS", "status 非法: " + st + "（active|draft|deprecated）")
    cf = meta.get("conf")
    if isinstance(cf, str) and cf not in CONF_OK:
        rep.err(path, 1, "E_CONF", "conf 非法: " + cf + "（S|E|I|U）")

    # 5 双版本字段
    ver = meta.get("ver")
    if isinstance(ver, str):
        if ver.strip() and ver.strip() not in VER_OK:
            rep.err(path, 1, "E_VER_VALUE", "ver 取值非法: " + ver)
        elif ver.strip():
            rep.warn(path, 1, "W_VER_SINGLE", "ver 是单值字符串，契约要求列表（如 [v160.7_rt, v159.3_src]）")
    elif isinstance(ver, list):
        if len(ver) > 2:
            rep.warn(path, 1, "W_VER_MANY", "ver 超过 2 个版本: " + ", ".join(map(str, ver)))
        for v in ver:
            if v not in VER_OK:
                rep.err(path, 1, "E_VER_VALUE", "ver 取值非法: " + str(v) + "（允许 v160.7_rt/v159.3_src/v160.7/v159.3）")

    # src 形态
    src = meta.get("src")
    if isinstance(src, list):
        for s in src:
            if not (re.match(r"^[\w./\\\-]+:\d+", s) or s.startswith("jar:") or s.startswith("src:")
                    or re.match(r"^[^:]+:\d+(-\d+)?$", s)):
                rep.warn(path, 1, "W_SRC_FORMAT", "src 条目不像 路径:行号 / jar: 形式: " + s)

    # 3 data 引用
    data = meta.get("data")
    if isinstance(data, list):
        for d in data:
            p = d.split("#", 1)[0].strip()
            if not p:
                continue
            cand = root / p
            if not cand.exists():
                if (path.parent / p).exists():
                    continue
                # 00-data 数据层未落地 → warn；已落地（00-data 有任一 .json）说明是错路径 → error
                if strict or data_ready:
                    why = "（--strict）" if strict and not data_ready else "（00-data 已落地，疑似路径写错）"
                    rep.err(path, 1, "E_DATA_FILE", "data 引用的 00-data 文件不存在: " + p + why)
                else:
                    rep.warn(path, 1, "W_DATA_FILE_MISSING",
                             "data 引用的 00-data 文件尚未生成: " + p + "（--strict 或 00-data 落地后自动转 error）")
                continue
            frag = d.split("#", 1)[1].strip() if "#" in d else ""
            if frag and cand.suffix.lower() == ".json":
                try:
                    obj = json.loads(cand.read_text(encoding="utf-8-sig", errors="replace"))
                    if frag.startswith("id="):  # 00-data/blocks.json#id=duo
                        want = frag[3:].strip()
                        recs = obj
                        if isinstance(obj, dict):
                            for k in ("records", "items", "entries", "rows", "data"):
                                if isinstance(obj.get(k), list):
                                    recs = obj[k]
                                    break
                            else:
                                recs = []
                        ids = {str(r.get("id")) for r in recs if isinstance(r, dict)}
                        if recs and want not in ids:
                            rep.warn(path, 1, "W_DATA_FRAGMENT",
                                     "data 片段 id=" + want + " 不在 " + p + " 的记录中")
                    elif isinstance(obj, dict) and frag.split(".")[0] not in obj:
                        rep.warn(path, 1, "W_DATA_FRAGMENT", "data 片段 " + frag + " 不在 " + p + " 的顶层键中")
                except Exception as e:
                    rep.warn(path, 1, "W_DATA_JSON", p + " 解析失败: " + str(e)[:80])

    # 2 七段模板
    for name, pat in SECTIONS:
        if not re.search(pat, body, re.M):
            rep.err(path, 1, "E_SECTION_MISSING", "缺模板小节: " + name)

    # 4 数字声明来源标记
    check_num_conflicts(path, body, first_line, stat_tables(root), rep)
    total_num = 0
    bad_num = 0
    last_marker = 0
    prev_is_row = False
    table_has_src_col = False
    SRC_COL_KEYS = ("来源", "源", "src", "Src", "SRC", "出处")
    for lineno, ln, in_fence in _iter_body_lines(body, first_line):
        if in_fence or not ln.strip():
            prev_is_row = False
            continue
        is_row = ln.lstrip().startswith("|")
        if is_row and not prev_is_row:  # 表格第一行 = 表头
            table_has_src_col = any(k in ln for k in SRC_COL_KEYS)
        prev_is_row = is_row
        if is_row and table_has_src_col:
            continue  # 表自带来源列，行内数字不再逐格要求标记
        if not NUM_CLAIM_RE.search(ln):
            continue
        total_num += 1
        if any(m in ln for m in SRC_MARKERS):
            last_marker = lineno
            continue
        # 表格/多行块：紧邻上文已有来源标记时视为整块覆盖（表格行放宽到 20 行）
        window = 20 if ln.lstrip().startswith("|") else 6
        if last_marker and 0 <= lineno - last_marker <= window:
            continue
        bad_num += 1
        if bad_num <= 5:
            rep.warn(path, lineno, "W_NUM_NO_SOURCE", "数字声明缺来源标记: " + ln.strip()[:80])
    if bad_num > 5:
        rep.warn(path, 0, "W_NUM_NO_SOURCE", "另有 %d 行数字缺来源标记（同 E/W 略）" % (bad_num - 5))

    # 6 链接
    for m in LINK_RE.finditer(body):
        tgt = m.group(1).strip()
        if not tgt or tgt.startswith(("http://", "https://", "mailto:", "#", "tel:")):
            continue
        rel_target = tgt.split("#", 1)[0].strip()
        if not rel_target:
            continue
        cands = [(path.parent / rel_target), (root / rel_target)]
        if not any(c.exists() for c in cands):
            lineno = first_line + body[:m.start()].count("\n")
            rep.err(path, lineno, "E_LINK_DEAD", "相对链接不可达: " + tgt)

    # 相关 小节内的 ID 引用（第二遍统一校验）
    sm = re.search(r"^##\s*相关\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S)
    if sm:
        seg = sm.group(1)
        base = first_line + body[:sm.start()].count("\n")
        for m in re.finditer(r"\b([A-Z]{2,8}\.[A-Z][A-Z0-9_]*\.\d{3})\b", seg):
            pending_refs.append((path, base + seg[:m.start()].count("\n"), m.group(1)))

    # 反例存在性（骨架检查）
    ce = re.search(r"^##\s*实测与反例\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S)
    mi = re.search(r"^##\s*常见误解\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S)
    ce_txt = (ce.group(1) if ce else "") + (mi.group(1) if mi else "")
    if len(re.findall(r"[\u4e00-\u9fff]", ce_txt)) < 20:
        rep.warn(path, 1, "W_NO_COUNTEREXAMPLE", "实测与反例 / 常见误解 两节实质内容过少（契约要求每篇至少一个反例）")

    # 长度上限
    n_lines = text.count("\n") + 1
    if n_lines > 250:
        rep.err(path, 1, "E_TOO_LONG", "文章 %d 行 > 250 行上限，应拆分" % n_lines)

    # tokens 回填
    tok = estimate_tokens(body)
    rep.n_tokens += tok
    cur = meta.get("tokens")
    cur_i = None
    if isinstance(cur, str) and cur.strip().isdigit():
        cur_i = int(cur.strip())
    elif isinstance(cur, list) and cur and str(cur[0]).strip().isdigit():
        cur_i = int(str(cur[0]).strip())
    if write_tokens:
        if cur_i != tok:
            if TOKENS_LINE_RE.search(text):
                text = TOKENS_LINE_RE.sub("tokens: %d" % tok, text, count=1)
            else:
                text = re.sub(r"^---\n", "---\ntokens: %d\n" % tok, text, count=1)
            path.write_text(text, encoding="utf-8", newline="\n")
    elif cur_i is None:
        rep.warn(path, 1, "W_TOKENS_MISSING", "frontmatter 缺 tokens（跑 --write-tokens 回填）")
    elif abs(cur_i - tok) > max(20, tok // 5):
        rep.warn(path, 1, "W_TOKENS_STALE", "tokens=%d 与当前估算 %d 偏差过大，跑 --write-tokens 更新" % (cur_i, tok))

# ---------------------------------------------------------------- 00-data 表
def check_data_tables(root: Path, rep: Report):
    dd = root / "00-data"
    if not dd.is_dir():
        rep.warn(root, 0, "W_DATA_DIR_MISSING", "00-data/ 不存在")
        return
    # 反射转储（rt_list_* / rt_values_raw / src_anchors）是「类字段名→常量」形态，不是记录表，
    # 不参与 records 校验；它们由 00-data/README.md 说明口径。
    SKIP_STEMS = ("rt_list_", "rt_values_raw", "src_anchors", "formula_anchors", "constants_")
    for p in sorted(dd.glob("*.json")):
        if p.name.startswith(SKIP_STEMS):
            rep.data_tables.append({"path": "00-data/" + p.name, "records": 0, "bad": 0,
                                    "note": "反射转储/辅助，跳过 records 校验"})
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
        except Exception as e:
            rep.err(p, 1, "E_DATA_JSON", "JSON 解析失败: " + str(e)[:120])
            continue
        recs = []
        if isinstance(obj, dict):
            for k in ("records", "items", "entries", "blocks", "data", "rows"):
                if isinstance(obj.get(k), list):
                    recs = obj[k]
                    break
            if not recs:
                recs = [v for v in obj.values() if isinstance(v, dict)]
        elif isinstance(obj, list):
            recs = obj
        bad = [r for r in recs if not isinstance(r, dict) or not (r.get("id") and r.get("src") and r.get("ver"))]
        rep.data_tables.append({"path": "00-data/" + p.name, "records": len(recs), "bad": len(bad),
                                "bytes": p.stat().st_size})
        if bad:
            sample = str(bad[0])[:120]
            rep.warn(p, 1, "W_DATA_RECORD", "%d/%d 条记录缺 id/src/ver 之一，例: %s" % (len(bad), len(recs), sample))
    if not (dd / "README.md").exists():
        rep.warn(dd, 0, "W_DATA_README", "00-data/README.md 缺失（须说明单位口径/生成脚本/时间/条数）")

def scan_duplicate_titles(files, rep: Report):
    seen = {}
    for p in files:
        meta, _, _ = parse_frontmatter(p.read_text(encoding="utf-8-sig", errors="replace"))
        if not isinstance(meta, dict):
            continue
        t = meta.get("title")
        if not isinstance(t, str) or not t.strip():
            continue
        key = re.sub(r"\s+", "", t)
        if key in seen and seen[key] != p.name:
            rep.warn(p, 1, "W_TITLE_DUP", "标题与 " + seen[key] + " 重复: " + t)
        else:
            seen[key] = p.name

# ---------------------------------------------------------------- 主流程
def run(root: Path, write_tokens=False, strict=False):
    root = Path(root).resolve()
    dr = data_layer_ready(root)
    rep = Report(root)
    if not root.is_dir():
        print("check_kb: 根目录不存在: " + str(root), file=sys.stderr)
        return 2, None
    files = article_files(root, rep)
    pending = []
    for p in files:
        try:
            check_article(p, root, rep, pending, write_tokens, strict=strict, data_ready=dr)
        except Exception as e:
            rep.err(p, 1, "E_CRASH", "检查脚本异常: %r" % (str(e)[:150],))
    known = set(rep.ids)
    # 00-data 里的记录 id（如 DATA.FORMULA.001）也是合法引用目标
    dd = root / "00-data"
    if dd.is_dir():
        for jp in dd.glob("*.json"):
            try:
                obj = json.loads(jp.read_text(encoding="utf-8-sig", errors="replace"))
            except Exception:
                continue
            recs = []
            if isinstance(obj, dict):
                for k in ("records", "items", "entries", "blocks", "data", "rows"):
                    if isinstance(obj.get(k), list):
                        recs = obj[k]
                        break
            elif isinstance(obj, list):
                recs = obj
            for rec in recs:
                if isinstance(rec, dict) and isinstance(rec.get("id"), str):
                    known.add(rec["id"])
    for path, lineno, ref in pending:
        if ref not in known:
            rep.warn(path, lineno, "W_REF_UNKNOWN", "相关 引用的 ID 在库中不存在: " + ref)
    check_data_tables(root, rep)
    scan_duplicate_titles(files, rep)
    rep.ids = known
    return (1 if rep.errors else 0), rep

def print_report(rep: Report, show_all=False):
    print("== check_kb @ " + str(rep.root) + " ==")
    print("files=%d  bytes=%d  tokens~%d  ids=%d  errors=%d  warnings=%d"
          % (rep.n_files, rep.n_bytes, rep.n_tokens, len(rep.ids), len(rep.errors), len(rep.warnings)))
    if rep.domain_counts:
        print("per-domain: " + "  ".join("%s=%d" % (k, rep.domain_counts[k]) for k in sorted(rep.domain_counts)))
    if rep.data_tables:
        print("data tables: " + "  ".join("%s(%d rec/%d bad)" % (t["path"], t["records"], t["bad"]) for t in rep.data_tables))
    for rec in rep.errors:
        print("[E] %s:%d  %s  %s" % (rec["path"], rec["line"], rec["code"], rec["msg"]))
    lim = len(rep.warnings) if show_all else 40
    for rec in rep.warnings[:lim]:
        print("[W] %s:%d  %s  %s" % (rec["path"], rec["line"], rec["code"], rec["msg"]))
    if len(rep.warnings) > lim:
        print("... 另有 %d 条 warning（--all 查看）" % (len(rep.warnings) - lim))
    if not rep.n_files:
        print("提示: 库里还没有文章，friend 门禁只能在空库上验证退出码与报告格式。")
    print("RESULT: " + ("FAIL (errors>0)" if rep.errors else "PASS"))

def main(argv=None):
    ap = argparse.ArgumentParser(description="knowledge/ 静态门禁")
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="knowledge 根目录（默认脚本上级）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--write-tokens", action="store_true", help="回填 frontmatter tokens")
    ap.add_argument("--strict", action="store_true",
                    help="data 引用的 00-data 文件缺失时升级为 error（半成品库阶段不要开）")
    ap.add_argument("--all", action="store_true", help="打印全部 warning")
    ap.add_argument("--audit", action="store_true",
                    help="额外跑数字审计（文章 vs 00-data），不影响门禁退出码")
    ap.add_argument("--audit-out", default=None,
                    help="数字审计报告路径（默认 <root 父目录>/_report/num_audit.md）")
    a = ap.parse_args(argv)
    code, rep = run(Path(a.root), write_tokens=a.write_tokens, strict=a.strict)
    if rep is None:
        return 2
    if a.json:
        print(json.dumps(rep.as_dict(), ensure_ascii=False, indent=2))
    else:
        print_report(rep, show_all=a.all)
    if a.audit and code != 2:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import num_audit  # 同目录；缺脚本时不影响门禁
            res = num_audit.run_audit(Path(a.root), out=a.audit_out)
            rows, outp = res if isinstance(res, tuple) else (res, a.audit_out)
            bad = sum(1 for r in rows if r.get("state") != "A_MATCH")
            print("audit: %d 行命中 / %d 行异常 -> %s" % (len(rows), bad, outp))
        except Exception as e:
            print("audit: 跳过（%r），可加 --audit-out 指定可写路径" % (str(e)[:120],), file=sys.stderr)
    return code

if __name__ == "__main__":
    sys.exit(main())
