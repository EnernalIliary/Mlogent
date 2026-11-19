#!/usr/bin/env python3
"""build_index.py — 生成 knowledge/index.json（全库总目录）。

    python knowledge/tools/build_index.py                 # 写 <knowledge>/index.json
    python knowledge/tools/build_index.py --root ../knowledge --out ../knowledge/index.json
    python knowledge/tools/build_index.py --check          # 只比对，不同步则退出码 1

index.json 的契约（AI 首读文件）:
    version   目录格式版本（字符串）
    generated 生成时间（本地时间 ISO8601）
    domains[] {id,title,desc,articles[{id,path,title,tokens,conf,ver,status}]}
    data[]    {path,records,bytes,keys[]}         00-data 机读表
    evidence[]{path,kind,bytes,lines|entries}     08-evidence 证据层
    docs[]    {path,bytes,tokens}                 KB.md / CONVENTIONS.md / VERSION.md 等通读文档
    counts    {articles,by_domain,data_tables,data_records,evidence_files,tokens_total}
字段只增不改；tokens 为估算值（汉字 0.62 / 英文词 0.75），非真实 tokenizer 计数。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_kb import DOMAINS, estimate_tokens, parse_frontmatter  # noqa: E402

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

INDEX_VERSION = "1"
CONTRACT_DOCS = ["KB.md", "CONVENTIONS.md", "VERSION.md", "README.md"]
EVIDENCE_KINDS = {"claims": "re-runnable claims", "probes": "probe scripts",
                  "bench": "benchmark questions"}
DATA_KEYS = ("records", "items", "entries", "rows", "data")


def _rel(root: Path, p: Path) -> str:
    try:
        return p.relative_to(root).as_posix()
    except ValueError:
        return p.as_posix()


def _records_of(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for k in DATA_KEYS:
            if isinstance(obj.get(k), list):
                return obj[k]
        return [v for v in obj.values() if isinstance(v, dict)]
    return []


def scan_articles(root: Path):
    out = []
    for dom in sorted(DOMAINS):
        dd = root / dom
        if not dd.is_dir():
            continue
        for p in sorted(dd.rglob("*.md")):
            if not p.is_file() or p.name.startswith("_") or p.name.lower() == "readme.md":
                continue
            text = p.read_text(encoding="utf-8-sig", errors="replace")
            meta, body, _ = parse_frontmatter(text)
            meta = meta if isinstance(meta, dict) else {}
            tok = meta.get("tokens")
            tok_i = None
            if isinstance(tok, str) and tok.strip().isdigit():
                tok_i = int(tok.strip())
            elif isinstance(tok, list) and tok and str(tok[0]).strip().isdigit():
                tok_i = int(str(tok[0]).strip())
            out.append({
                "id": str(meta.get("id") or ""),
                "path": "knowledge/" + _rel(root, p),
                "title": str(meta.get("title") or p.stem),
                "tokens": tok_i if tok_i is not None else estimate_tokens(body),
                "tokens_est": tok_i is None,
                "conf": str(meta.get("conf") or ""),
                "ver": meta.get("ver") if isinstance(meta.get("ver"), list) else [str(meta.get("ver") or "")],
                "status": str(meta.get("status") or ""),
                "domain": str(meta.get("domain") or dom),
                "lines": text.count("\n") + 1,
            })
    return out


def scan_data(root: Path):
    out = []
    dd = root / "00-data"
    if not dd.is_dir():
        return out
    for p in sorted(dd.glob("*.json")):
        raw = p.name.startswith("rt_") or p.name.endswith("_raw.json")
        entry = {"path": "knowledge/00-data/" + p.name, "kind": "raw" if raw else "canonical",
                 "records": 0, "bytes": p.stat().st_size, "keys": []}
        try:
            obj = json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
            recs = _records_of(obj)
            entry["records"] = len(recs)
            keys = set()
            for r in recs[:2000]:
                if isinstance(r, dict):
                    keys.update(r.keys())
            entry["keys"] = sorted(keys)[:40]
        except Exception as e:
            entry["error"] = str(e)[:120]
        out.append(entry)
    return out


def scan_evidence(root: Path):
    out = []
    ed = root / "08-evidence"
    if not ed.is_dir():
        return out
    for p in sorted(ed.rglob("*")):
        if not p.is_file():
            continue
        kind = p.relative_to(ed).parts[0] if len(p.relative_to(ed).parts) > 1 else "top"
        e = {"path": "knowledge/08-evidence/" + _rel(ed, p), "kind": kind,
             "bytes": p.stat().st_size, "desc": EVIDENCE_KINDS.get(kind.rstrip("/"), kind)}
        if p.suffix == ".jsonl":
            try:
                e["lines"] = sum(1 for ln in p.read_text(encoding="utf-8-sig", errors="replace").splitlines() if ln.strip())
            except Exception:
                pass
        elif p.suffix == ".json":
            try:
                e["entries"] = len(_records_of(json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))))
            except Exception:
                pass
        out.append(e)
    return out


def scan_docs(root: Path):
    out = []
    for name in CONTRACT_DOCS:
        p = root / name
        if p.is_file():
            t = p.read_text(encoding="utf-8-sig", errors="replace")
            out.append({"path": "knowledge/" + name, "bytes": p.stat().st_size, "tokens": estimate_tokens(t)})
    return out


def build(root: Path) -> dict:
    root = root.resolve()
    arts = scan_articles(root)
    data = scan_data(root)
    ev = scan_evidence(root)
    docs = scan_docs(root)
    domains = []
    for dom in sorted(DOMAINS):
        code, title, desc = DOMAINS[dom]
        mine = [a for a in arts if a["domain"] == dom or a["path"].startswith("knowledge/" + dom + "/")]
        domains.append({
            "id": dom, "code": code, "title": title, "desc": desc,
            "articles": sorted(mine, key=lambda a: (a["id"] or "zzz", a["path"])),
        })
    by_domain = {d["id"]: len(d["articles"]) for d in domains}
    canon = [d for d in data if d.get("kind") == "canonical"]
    ev_kinds = {}
    for e in ev:
        ev_kinds[e["kind"]] = ev_kinds.get(e["kind"], 0) + 1
    ev_dirs = []
    ed = root / "08-evidence"
    if ed.is_dir():
        for sub in sorted(x for x in ed.iterdir() if x.is_dir() and not x.name.startswith("_")):
            files = [x for x in sub.rglob("*") if x.is_file() and not x.name.startswith("_")]
            ev_dirs.append({"path": "knowledge/08-evidence/" + sub.name + "/",
                            "kind": sub.name, "desc": EVIDENCE_KINDS.get(sub.name, sub.name),
                            "files": len(files),
                            "bytes": sum(x.stat().st_size for x in files)})
    return {
        "version": INDEX_VERSION,
        "generated": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "root": "knowledge",
        "read_order": ["index.json", "KB.md", "CONVENTIONS.md", "VERSION.md",
                       "00-data/*.json", "domain articles", "08-evidence/claims.jsonl"],
        "domains": domains,
        "data": data,
        "evidence": ev,
        "evidence_dirs": ev_dirs,
        "docs": docs,
        "counts": {
            "articles": len(arts),
            "by_domain": by_domain,
            "data_tables": len(canon),
            "data_records": sum(d["records"] for d in canon),
            "data_raw_tables": len(data) - len(canon),
            "evidence_files": len(ev),
            "evidence_by_kind": ev_kinds,
            "evidence_dirs": len(ev_dirs),
            "tokens_total": sum(d["tokens"] for d in docs) + sum(a["tokens"] for a in arts),
            "empty": len(arts) == 0,
        },
        "notes": [
            "tokens are estimated (0.62 per CJK char, 0.75 per English word), not a real tokenizer count.",
            "data[].records counts entries; kind=canonical feeds counts, rt_*/raw are listed but not summed.",
            "evidence_dirs[] aggregates the 08-evidence subdirectories (claims/probes/bench); empty ones appear too.",
            "an article without front matter gets empty id/conf/status; it is still listed so the gate can complain.",
            "generator: knowledge/tools/build_index.py; checker: knowledge/tools/check_kb.py.",
        ],
    }


def render(idx: dict) -> str:
    return json.dumps(idx, ensure_ascii=False, indent=1) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="生成 knowledge/index.json")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true", help="只比对现有 index.json，不一致则退出码 1")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root)
    if not root.is_dir():
        print("build_index: 根目录不存在: " + str(root), file=sys.stderr)
        return 2
    out = Path(a.out) if a.out else (root / "index.json")
    text = render(build(root))
    if a.check:
        cur = out.read_text(encoding="utf-8-sig") if out.exists() else ""
        # generated 时间戳每次不同，比对时剔除，否则永远"过期"
        def _norm(s: str) -> dict:
            try:
                d = json.loads(s)
            except Exception:
                return {}
            if isinstance(d, dict):
                d.pop("generated", None)
            return d
        if cur.strip() and _norm(cur) == _norm(text):
            if not a.quiet:
                print("index.json 与库一致: " + str(out))
            return 0
        print("index.json 已过期，重跑 build_index.py: " + str(out))
        return 1
    out.write_text(text, encoding="utf-8", newline="\n")
    if not a.quiet:
        idx = json.loads(text)
        c = idx["counts"]
        print("wrote %s  (%d bytes)" % (out, len(text.encode("utf-8"))))
        print("articles=%d  domains=%d  data_tables=%d  data_records=%d  evidence_files=%d  tokens~%d"
              % (c["articles"], len(idx["domains"]), c["data_tables"], c["data_records"],
                 c["evidence_files"], c["tokens_total"]))
        if c["empty"]:
            print("提示: 库中暂无文章，index.json 只含目录骨架与契约文档。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
