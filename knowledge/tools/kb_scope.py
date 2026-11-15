#!/usr/bin/env python3
"""kb_scope: 受限检索实验版（基线 = kb-stage/tools/kb.py md5 1FB23F2A，不改仓库版）.

与基线一致的保留项：混合检索（dense bge-small-zh + FTS5 trigram BM25 + RRF k=60）、
索引排除路径段以 _ 开头的文件、查询期路径权重 knowledge x1.25 / tools|tests x0.8。

实验开关：
  A hard-scope : build 时语料只含 knowledge/**（文章 md + 00-data 摘要），
                 库外文档（tools/ docs/ mindustry-blueprint/ MBO/ ...）不入索引。
  B dedupe     : 结果按「文件」去重，k 数文件不数 chunk；同文件合并 top 块（<=3 段，
                 正文 <=1200 字符），文件得分 = 该文件最高分块的 RRF 分 x 路径权重。
  C ascii-boost: 查询含 ASCII 标识符（.java/.json/:/_/驼峰）时，FTS 通道加权 x2
                 （并追加一条「标识符 OR」查询），dense 权重 x0.7；RRF k=60 不变。

DB 由 KB_SCOPE_DB 指定（默认 kb-stage/out/_kb_scope/kb.sqlite3），从不写仓库 out/。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
REPO_DEFAULT = Path(r"<repo>")
ROOT = Path(os.environ.get("KB_ROOT", REPO_DEFAULT))
KNOWLEDGE_DIR = Path(os.environ.get("KB_KNOWLEDGE", ROOT / "knowledge"))
DATA_DIR = KNOWLEDGE_DIR / "00-data"
KNOWLEDGE_TOOLS_DIR = KNOWLEDGE_DIR / "tools"
DB_PATH = Path(os.environ.get("KB_SCOPE_DB",
                              HERE.parent / "out" / "_kb_scope" / "kb.sqlite3"))
_LIBS_DEFAULT = ROOT / "out" / ("_kblibs311" if sys.version_info < (3, 12) else "_kblibs")
LIBS = Path(os.environ.get("KB_LIBS", _LIBS_DEFAULT))
MODELS = Path(os.environ.get("KB_MODELS", ROOT / "out" / "_kbmodels"))
EMB_MODEL = os.environ.get("KB_EMB_MODEL", "BAAI/bge-small-zh-v1.5")
CORPUS_MODE = os.environ.get("KB_SCOPE_MODE", "knowledge")
KNOWLEDGE_BOOST = float(os.environ.get("KB_KNOWLEDGE_BOOST", "1.25"))
CODE_PENALTY = float(os.environ.get("KB_CODE_PENALTY", "0.8"))

DOC_FILES = [
    "README.md", "Logic/逻辑代码规范.md", "mindustry-blueprint/SKILL.md",
    "mindustry-blueprint/REFERENCE.md", "mindustry-blueprint/EMULATOR-CROSSCHECK.md",
    "tools/README.md", "dsh-preset-mlog/README.md", "rules/README.md",
    "docs/断言表.md", "docs/验证记录.md",
    "knowledge/KB.md", "knowledge/CONVENTIONS.md",
    "knowledge/VERSION.md",
]
CODE_GLOBS = ["tools/*.py", "tests/run_tests.py"]
DOC_GLOBS = ["docs/游戏速查/*.md"]
EXCLUDE_DIRS = {"__pycache__", "out", ".git", "assetsraw", "Mindustry-Source", "Arc-Source"}

_EMB = None

def _path_weight(path: str) -> float:
    if path.startswith("knowledge/"):
        return KNOWLEDGE_BOOST
    if path.startswith("tools/") or path.startswith("tests/"):
        return CODE_PENALTY
    return 1.0

def _ensure_libs() -> None:
    if LIBS.is_dir() and str(LIBS) not in sys.path:
        sys.path.insert(0, str(LIBS))

def _embedder():
    global _EMB
    if _EMB is None:
        _ensure_libs()
        from fastembed import TextEmbedding
        _EMB = TextEmbedding(model_name=EMB_MODEL, cache_dir=str(MODELS))
    return _EMB

def _split_long(body: str, start: int, limit: int):
    if len(body) <= limit:
        return [(body, start, start + body.count("\n"))]
    chunks, cur, cur_start = [], [], start
    for line in body.splitlines():
        cur.append(line)
        if sum(len(x) + 1 for x in cur) >= limit:
            chunks.append(("\n".join(cur), cur_start, cur_start + len(cur) - 1))
            cur_start += len(cur)
            cur = []
    if cur:
        chunks.append(("\n".join(cur), cur_start, cur_start + len(cur) - 1))
    return chunks

def _section_chunks(text: str, path: str, kind: str):
    out = []
    if kind == "code":
        lines = text.splitlines()
        starts = [i for i, l in enumerate(lines, 1) if re.match(r"^(?:def |class |@)", l)]
        if not starts or starts[0] != 1:
            starts = [1] + starts
        bounds = list(zip(starts, starts[1:] + [len(lines) + 1]))
        for s, e in bounds:
            body = "\n".join(lines[s - 1:e - 1])
            for piece, ps, pe in _split_long(body, s, 120):
                out.append({"path": path, "start": ps, "end": pe, "kind": kind,
                            "heading": "", "text": piece})
        return out
    lines = text.splitlines()
    heading = ""
    cur = []
    cur_start = 1

    def flush(end_line: int):
        nonlocal cur, cur_start
        body = "\n".join(cur).strip()
        if body:
            bl = body.splitlines()
            if bl and re.match(r"^#{1,4} ", bl[0]):
                body = "\n".join(bl[1:]).strip()
            prefix = "# " + heading + "\n" if heading else ""
            if body:
                for piece, ps, pe in _split_long(prefix + body, cur_start, 1400):
                    out.append({"path": path, "start": ps, "end": pe, "kind": kind,
                                "heading": heading, "text": piece})
        cur = []

    for i, line in enumerate(lines, 1):
        if re.match(r"^#{1,4} ", line):
            flush(i)
            heading = line.lstrip("# ").strip()
            cur_start = i
        cur.append(line)
    flush(len(lines) + 1)
    return out

def _rel(p: Path) -> str:
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        try:
            return "knowledge/" + p.relative_to(KNOWLEDGE_DIR).as_posix()
        except ValueError:
            return p.name

def _knowledge_files():
    if not KNOWLEDGE_DIR.is_dir():
        return []
    out = []
    for p in sorted(KNOWLEDGE_DIR.rglob("*.md")):
        if not p.is_file():
            continue
        try:
            parts = p.relative_to(KNOWLEDGE_DIR).parts
        except ValueError:
            parts = (p.name,)
        if any(part.startswith("_") for part in parts):
            continue
        if any(part in EXCLUDE_DIRS for part in parts):
            continue
        if KNOWLEDGE_TOOLS_DIR in p.parents or DATA_DIR in p.parents:
            continue
        out.append(p)
    return out

def _fmt_val(v) -> str:
    if isinstance(v, dict):
        if "v" in v:
            u = v.get("unit") or ""
            return str(v.get("v")) + u
        return json.dumps(v, ensure_ascii=False)[:60]
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False)[:60]

def _data_summaries():
    out = []
    if not DATA_DIR.is_dir():
        return out
    for p in sorted(DATA_DIR.glob("*.json")):
        try:
            obj = json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
        except Exception:
            continue
        recs = []
        if isinstance(obj, dict):
            for k in ("records", "items", "entries", "rows", "data"):
                if isinstance(obj.get(k), list):
                    recs = obj[k]
                    break
            if not recs:
                recs = [dict(v, id=k) for k, v in obj.items() if isinstance(v, dict)]
        elif isinstance(obj, list):
            recs = obj
        lines = ["## 00-data/" + p.name + "（" + str(len(recs)) + " 条）"]
        if isinstance(obj, dict) and isinstance(obj.get("meta"), dict):
            lines.append("- meta: " + ", ".join(
                k + "=" + _fmt_val(v) for k, v in list(obj["meta"].items())[:12]))
        for r in recs[:400]:
            if not isinstance(r, dict):
                continue
            rid = r.get("id") or r.get("name") or "?"
            name = r.get("name") or ""
            kv = [k + "=" + _fmt_val(v) for k, v in r.items()
                  if k not in ("id", "name", "src", "ver", "tags", "notes", "meta")]
            line = "- " + str(rid) + " " + str(name) + ": " + ", ".join(kv[:8])
            if r.get("src"):
                line += " [src: " + str(r.get("src")) + "]"
            if r.get("ver"):
                line += " ver=" + str(r.get("ver"))
            lines.append(line)
        if len(recs) > 400:
            lines.append("- … 其余 " + str(len(recs) - 400) + " 条略")
        out.append(("00-data/" + p.name, "\n".join(lines)))
    return out

def _corpus():
    """A: knowledge 模式只收 knowledge/**；full 模式与基线 kb.py 同一份语料。"""
    if CORPUS_MODE == "knowledge":
        return [(p, "doc") for p in _knowledge_files()]
    files = []
    for rel in DOC_FILES:
        p = ROOT / rel
        if p.is_file():
            files.append((p, "doc"))
    for pattern in CODE_GLOBS:
        for p in sorted(ROOT.glob(pattern)):
            if p.is_file() and not any(part in EXCLUDE_DIRS for part in p.parts):
                files.append((p, "code"))
    for pattern in DOC_GLOBS:
        for p in sorted(ROOT.glob(pattern)):
            if p.is_file() and not any(part in EXCLUDE_DIRS for part in p.parts):
                files.append((p, "doc"))
    for p in _knowledge_files():
        files.append((p, "doc"))
    return files

def build(quiet: bool = False) -> dict:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """CREATE TABLE chunks(
               id INTEGER PRIMARY KEY, path TEXT, start INTEGER, end INTEGER,
               kind TEXT, heading TEXT, text TEXT, vec BLOB);
           CREATE VIRTUAL TABLE fts USING fts5(
               text, heading, path, content='chunks', content_rowid='id',
               tokenize='trigram');"""
    )
    rows = []
    seen = set()
    data_summaries = _data_summaries()
    for path, kind in _corpus():
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        rel = _rel(path)
        for ch in _section_chunks(text, rel, kind):
            norm = re.sub(r"\s+", "", ch["text"])
            if len(norm) < 24 or norm in seen:
                continue
            seen.add(norm)
            rows.append((ch["path"], ch["start"], ch["end"], ch["kind"],
                         ch["heading"], ch["text"]))
    for rel, text in data_summaries:
        for ch in _section_chunks(text, rel, "data"):
            norm = re.sub(r"\s+", "", ch["text"])
            if len(norm) < 24 or norm in seen:
                continue
            seen.add(norm)
            rows.append((ch["path"], ch["start"], ch["end"], "data",
                         ch["heading"], ch["text"]))
    if not rows:
        raise SystemExit("no corpus files found")
    model = _embedder()
    vecs = []
    B = 32
    for i in range(0, len(rows), B):
        vecs.extend(model.embed([r[5] for r in rows[i:i + B]]))
    import numpy as np
    conn.executemany(
        "INSERT INTO chunks(path,start,end,kind,heading,text,vec) VALUES (?,?,?,?,?,?,?)",
        [(r[0], r[1], r[2], r[3], r[4], r[5],
          np.asarray(v, dtype="float32").tobytes()) for r, v in zip(rows, vecs)])
    conn.execute("INSERT INTO fts(rowid,text,heading,path) SELECT id,text,heading,path FROM chunks")
    conn.commit()
    n = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
    conn.close()
    stats = {"mode": CORPUS_MODE, "chunks": n, "files": len({r[0] for r in rows}),
             "data_tables": len(data_summaries), "db": str(DB_PATH)}
    if not quiet:
        print(json.dumps(stats, ensure_ascii=False))
    return stats

def _open(db=None):
    p = Path(db) if db else DB_PATH
    if not p.exists():
        raise SystemExit("no index yet: " + str(p))
    return sqlite3.connect(p)

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*(?::\d+(?:-\d+)?)?")

def ident_terms(q: str):
    out = []
    for m in _IDENT.finditer(q):
        t = m.group(0)
        if len(t) < 3 or not (t[0].isalpha() or t[0] == "_"):
            continue
        if ("." in t) or (":" in t) or ("_" in t) or re.search(r"[a-z][A-Z]", t) or t[0].isupper():
            out.append(t)
    seen, res = set(), []
    for t in out:
        if t.lower() not in seen:
            seen.add(t.lower())
            res.append(t)
    return res[:6]

def _fts_query(q: str) -> str:
    q = q.strip()
    if len(q) < 3:
        return ""
    return '"' + q.replace('"', '""') + '"'

def _sparse(conn, query: str, candidates: int, boost: bool):
    got = {}
    fq = _fts_query(query)
    if fq:
        try:
            for rid, s in conn.execute(
                    "SELECT rowid, bm25(fts) FROM fts WHERE fts MATCH ? ORDER BY bm25(fts) LIMIT ?",
                    (fq, candidates)):
                got[rid] = (1.0, float(s))
        except sqlite3.OperationalError:
            pass
    if boost:
        ids = ident_terms(query)
        if ids:
            sub = " OR ".join('"' + t.replace('"', '""') + '"' for t in ids)
            try:
                for rid, s in conn.execute(
                        "SELECT rowid, bm25(fts) FROM fts WHERE fts MATCH ? ORDER BY bm25(fts) LIMIT ?",
                        (sub, candidates)):
                    if rid in got:
                        got[rid] = (2.0, min(got[rid][1], float(s)))
                    else:
                        got[rid] = (2.0, float(s))
            except sqlite3.OperationalError:
                pass
    best = {}
    weights = {}
    for rid, (w, s) in got.items():
        sc = w * s
        if rid not in best or sc < best[rid]:
            best[rid] = sc
            weights[rid] = w
    ordered = sorted(best, key=lambda r: best[r])[:candidates]
    return [(rid, weights[rid], best[rid]) for rid in ordered]

def _fuse(conn, query, candidates, ascii_boost):
    import numpy as np
    rows = conn.execute("SELECT id,path,start,end,kind,heading,text,vec FROM chunks").fetchall()
    if not rows:
        return {}, {}
    qv = np.asarray(next(iter(_embedder().embed([query]))), dtype="float32")
    mat = np.frombuffer(b"".join(r[7] for r in rows), dtype="float32").reshape(len(rows), -1)
    sims = mat @ qv / (np.linalg.norm(mat, axis=1) * np.linalg.norm(qv) + 1e-9)
    dense = list(np.argsort(-sims)[:candidates])
    sparse = _sparse(conn, query, candidates, ascii_boost)
    by_id = {r[0]: r for r in rows}
    wd = 0.7 if ascii_boost else 1.0
    fused = {}
    for rank, i in enumerate(dense):
        cid = rows[i][0]
        fused[cid] = fused.get(cid, 0.0) + wd / (60 + rank)
    for rank, (cid, w, _s) in enumerate(sparse):
        if cid in by_id:
            fused[cid] = fused.get(cid, 0.0) + w / (60 + rank)
    return fused, by_id

def search(query: str, k: int = 6, kind: str | None = None, dedupe: bool = False,
           ascii_boost: bool = False, candidates: int = 40, db=None) -> list[dict]:
    conn = _open(db)
    fused, by_id = _fuse(conn, query, candidates, ascii_boost)
    conn.close()
    if not fused:
        return []
    if not dedupe:
        ordered = sorted(fused, key=lambda c: -fused[c] * _path_weight(by_id[c][1]))[:k]
        return [{"path": by_id[c][1], "start": by_id[c][2], "end": by_id[c][3],
                 "kind": by_id[c][4], "heading": by_id[c][5], "text": by_id[c][6],
                 "score": round(fused[c] * _path_weight(by_id[c][1]), 4)} for c in ordered]
    per_file = {}
    for cid, sc in fused.items():
        per_file.setdefault(by_id[cid][1], []).append((sc * _path_weight(by_id[cid][1]), cid))
    ranked = []
    for path, lst in per_file.items():
        lst.sort(key=lambda x: -x[0])
        ranked.append((lst[0][0], path, lst))
    ranked.sort(key=lambda x: -x[0])
    res = []
    for sc, path, lst in ranked[:k]:
        parts, starts, ends = [], [], []
        for _s, cid in lst[:3]:
            r = by_id[cid]
            parts.append(r[6].strip())
            starts.append(r[2])
            ends.append(r[3])
        text = "\n\n".join(parts)
        if len(text) > 1200:
            text = text[:1200] + "…"
        res.append({"path": path, "start": min(starts), "end": max(ends),
                    "kind": by_id[lst[0][1]][4], "heading": by_id[lst[0][1]][5] or "",
                    "text": text, "score": round(sc, 4), "n_chunks": len(parts)})
    return res

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    sp = sub.add_parser("search")
    sp.add_argument("query")
    sp.add_argument("-k", type=int, default=6)
    sp.add_argument("--dedupe", action="store_true")
    sp.add_argument("--ascii-boost", action="store_true")
    sp.add_argument("--candidates", type=int, default=40)
    sp.add_argument("--db", default=None)
    sub.add_parser("stats")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        build()
        return 0
    if a.cmd == "stats":
        with _open() as cx:
            n = cx.execute("select count(*) from chunks").fetchone()[0]
            files = cx.execute("select count(distinct path) from chunks").fetchone()[0]
            kinds = dict(cx.execute("select kind, count(*) from chunks group by kind").fetchall())
        print(json.dumps({"chunks": n, "files": files, "kinds": kinds}, ensure_ascii=False))
        return 0
    res = search(a.query, a.k, dedupe=a.dedupe, ascii_boost=a.ascii_boost,
                 candidates=a.candidates, db=a.db)
    print(json.dumps(res, ensure_ascii=False, indent=1)[:4000])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
