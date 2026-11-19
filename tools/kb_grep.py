"""Keyword retrieval over `knowledge/` with no third-party packages and no index.

Why this exists next to `kb.py`
-------------------------------
`kb.py` is the good retriever: bge-small-zh embeddings + trigram BM25, fused and
optionally reranked.  It is also three dependencies deep (`fastembed`,
`onnxruntime`, cached ONNX models) and needs a build step, so a *deployed* MCP
server cannot assume it: a server that answers `mlog_check` should also be able
to answer "what is `core-shard` called in Chinese" without downloading a model.

This module is the fallback that always works: pure stdlib, reads the Markdown
straight off disk, BM25 over heading-delimited sections.  Worse ranking than
`kb.py` (no semantics, no Chinese segmentation beyond character bigrams), but
zero setup, and 130 files scan in well under a second.

Tokenisation is deliberately blunt:

* ASCII identifiers (`mlog_check`, `core-shard`, `ucontrol`) become one term,
  lowercased, split on `-`/`_`/`.` as well so `core-shard` also matches "core";
* CJK runs become character bigrams (no dictionary, so no OOV problem) plus the
  run itself when it is short enough to be a word.

That is enough to rank "链接名 读档 重算" onto `E05-链接与@常量.md` and
"mindcode then 内联" onto `M10-Mindcode-Syntax.md`, which is the job.
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_KNOWLEDGE = os.path.join(ROOT, "knowledge")

try:                          # Chinese question -> its English names
    import cjken
except Exception:             # used as a single file, outside the repo
    cjken = None

_MEMO: dict[tuple, list[dict]] = {}
_INDEX: dict[tuple, tuple] = {}

HEAD_RE = re.compile(r"^(#{1,4})\s+(.*)$")
ASCII_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.\-]*")
CJK_RE = re.compile(r"[\u3400-\u9fff]+")
K1, B = 1.2, 0.75

# Where a hit came from decides how much it counts: facts live in `knowledge/`,
# one-off evidence lives in `docs/`, and a tool's own comments are a last resort.
PATH_WEIGHT = (("knowledge/", 1.0), ("data/", 1.0), ("docs/", 0.75),
               ("tools/", 0.5))


def _weight(path: str) -> float:
    for prefix, w in PATH_WEIGHT:
        if path.startswith(prefix):
            return w
    return 0.5


def terms(text: str) -> list[str]:
    """ASCII identifiers (also split on separators) + CJK bigrams."""
    out: list[str] = []
    for m in ASCII_RE.findall(text):
        low = m.lower()
        out.append(low)
        if re.search(r"[-_.]", low):
            out.extend(p for p in re.split(r"[-_.]", low) if p)
    for run in CJK_RE.findall(text):
        if len(run) == 1:
            out.append(run)
        else:
            out.extend(run[i:i + 2] for i in range(len(run) - 1))
        if 2 <= len(run) <= 4:
            out.append(run)
    # a term must carry information; single ASCII letters and pure digits do not
    return [t for t in out if len(t) > 1 or not t.isascii()]


def _sections(path: str, text: str) -> list[dict]:
    """Split one Markdown file at heading boundaries, keeping line numbers."""
    lines = text.splitlines()
    out: list[dict] = []
    head, start = os.path.basename(path), 1
    buf: list[str] = []
    for i, line in enumerate(lines, 1):
        m = HEAD_RE.match(line)
        if m and buf:
            out.append({"path": path, "heading": head, "start": start,
                        "end": i - 1, "text": "\n".join(buf)})
            buf, start = [], i
            head = m.group(2).strip()
        elif m:
            start, head = i, m.group(2).strip()
        else:
            buf.append(line)
    if buf:
        out.append({"path": path, "heading": head, "start": start,
                    "end": len(lines), "text": "\n".join(buf)})
    return out


def load(root: str = DEFAULT_KNOWLEDGE, *, include_docs: bool = False) -> list[dict]:
    """Every section of every tracked Markdown file under `root`."""
    stamp = _stamp(root, include_docs)
    hit = _MEMO.get((root, include_docs, stamp))
    if hit is not None:
        return hit
    docs: list[dict] = []
    roots = [(root, "knowledge/")]
    if include_docs:
        roots.append((os.path.join(ROOT, "docs"), "docs/"))
    for base, prefix in roots:
        if not os.path.isdir(base):
            continue
        for dirpath, dirs, names in os.walk(base):
            dirs[:] = sorted(d for d in dirs if not d.startswith(("_", ".")))
            for name in sorted(names):
                if not name.endswith(".md"):
                    continue
                full = os.path.join(dirpath, name)
                rel = prefix + os.path.relpath(full, base).replace("\\", "/")
                text = open(full, encoding="utf-8", errors="replace").read()
                for sec in _sections(rel, text):
                    docs.append(sec)
    _MEMO[(root, include_docs, stamp)] = docs
    return docs


def _stamp(root: str, include_docs: bool) -> tuple:
    """Cheap invalidation: file count plus the newest mtime.

    A long-lived MCP process should not re-read 6 MB per question, and a caller
    who edits an article should not have to restart the server.
    """
    newest, count = 0.0, 0
    bases = [root] + ([os.path.join(ROOT, "docs")] if include_docs else [])
    for base in bases:
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, names in os.walk(base):
            for name in names:
                if not name.endswith(".md"):
                    continue
                try:
                    newest = max(newest, os.path.getmtime(os.path.join(dirpath, name)))
                    count += 1
                except OSError:
                    pass
    return (count, round(newest, 3))


def _index(root: str, include_docs: bool) -> tuple:
    """Sections plus their term bags, df and average length — built once."""
    stamp = _stamp(root, include_docs)
    key = (root, include_docs, stamp)
    hit = _INDEX.get(key)
    if hit is not None:
        return hit
    docs = load(root, include_docs=include_docs)
    df: dict[str, int] = {}
    bags: list[dict[str, int]] = []
    for d in docs:
        bag: dict[str, int] = {}
        for t in terms(d["heading"]) * 2 + terms(d["text"]):
            bag[t] = bag.get(t, 0) + 1
        bags.append(bag)
        for t in set(bag):
            df[t] = df.get(t, 0) + 1
    avg = sum(sum(b.values()) for b in bags) / max(len(docs), 1)
    value = (docs, bags, df, avg)
    _INDEX[key] = value
    return value


def search(query: str, k: int = 6, *, root: str = DEFAULT_KNOWLEDGE,
           include_docs: bool = False) -> list[dict]:
    if cjken is not None:
        query = cjken.expand(query)[0]
    q = terms(query)
    if not q:
        return []
    docs, bags, df, avg = _index(root, include_docs)
    if not docs:
        return []
    n = len(docs)
    scored: list[tuple[float, int]] = []
    for i, bag in enumerate(bags):
        length = sum(bag.values()) or 1
        s = 0.0
        for t in q:
            tf = bag.get(t, 0)
            if not tf:
                continue
            # The classic ratio, clipped below: a term present in every section
            # (「的」 bigrams and friends) must not outvote a rare identifier.
            idf = max(0.05, (n - df.get(t, 0) + 0.5) / (df.get(t, 0) + 0.5))
            s += idf * tf * (K1 + 1) / (tf + K1 * (1 - B + B * length / avg))
        if s > 0:
            scored.append((s * _weight(docs[i]["path"]), i))
    scored.sort(key=lambda x: (-x[0], docs[x[1]]["path"]))
    out = []
    for score, i in scored[:k]:
        d = docs[i]
        out.append({"path": d["path"], "heading": d["heading"],
                    "start": d["start"], "end": d["end"],
                    "score": round(score, 3), "snippet": _snippet(d["text"], q)})
    return out


def _snippet(text: str, q: list[str], width: int = 360) -> str:
    """The window around the earliest hit, so the reader sees why it matched."""
    low = text.lower()
    best = -1
    for t in q:
        i = low.find(t.lower())
        if i >= 0 and (best < 0 or i < best):
            best = i
    if best < 0:
        return text.strip()[:width]
    start = max(0, best - width // 3)
    body = text[start:start + width].strip()
    return ("…" if start else "") + body + ("…" if start + width < len(text) else "")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: kb_grep.py search <query> [-k N] [--docs] [--json]\n"
              "       kb_grep.py selftest")
        return 0
    cmd = argv.pop(0)
    if cmd == "selftest":
        return selftest()
    if cmd != "search":
        print("unknown command: " + cmd, file=sys.stderr)
        return 2
    k = 6
    include_docs = False
    as_json = False
    query: list[str] = []
    while argv:
        a = argv.pop(0)
        if a == "-k":
            k = int(argv.pop(0))
        elif a == "--docs":
            include_docs = True
        elif a == "--json":
            as_json = True
        else:
            query.append(a)
    hits = search(" ".join(query), k=k, include_docs=include_docs)
    if as_json:
        import json
        print(json.dumps(hits, ensure_ascii=False, indent=1))
        return 0 if hits else 1
    if not hits:
        print("no hit", file=sys.stderr)
        return 1
    for h in hits:
        print("%-46s %-38s %6.2f  L%d-%d"
              % (h["path"], h["heading"][:38], h["score"], h["start"], h["end"]))
    return 0


def selftest() -> int:
    checks = []
    q = terms("core-shard 读档")
    checks.append(("ascii id kept whole", "core-shard" in q))
    checks.append(("ascii split too", "core" in q and "shard" in q))
    checks.append(("cjk bigrams", "读档" in q))
    few = search("Mindcode 内联 then", k=3)
    checks.append(("mindcode ranks first",
                   bool(few) and few[0]["path"].endswith("M10-Mindcode-Syntax.md")))
    link = search("链接名 读档 重算", k=3)
    checks.append(("link naming article found",
                   bool(link) and "E05" in link[0]["path"]))
    empty = search("", k=3)
    checks.append(("empty query is empty", empty == []))
    junk = search("zzzzznotathing", k=3)
    checks.append(("junk finds nothing", junk == []))
    for name, ok in checks:
        print("%-28s %s" % (name, "ok" if ok else "FAIL"))
    bad = [n for n, ok in checks if not ok]
    print("%d/%d checks passed" % (len(checks) - len(bad), len(checks)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
