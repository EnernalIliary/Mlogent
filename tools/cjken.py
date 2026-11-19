# -*- coding: utf-8 -*-
"""Bridge a Chinese question onto an English corpus.

The knowledge base is written in English; most people who ask it questions
write Chinese.  A word-matcher (``tools/kb_grep.py``) and an embedder
(``tools/kb.py``) both see the Chinese text and find nothing, not because the
answer is missing but because the question never mentions an English word.

This module is the bridge: it reads the name tables the repository already
keeps as its source of truth --

* ``knowledge/GLOSSARY.md`` hand-written table (jargon: 微处 -> micro-processor)
* ``knowledge/GLOSSARY.md`` generated tables (game entities, four columns)
* ``data/game/aliases.json`` (``id -> [official Chinese, legacy...]``)

-- and appends the English names of whatever Chinese terms the query mentions.
It never rewrites the query, it only adds terms, so an expansion that is wrong
costs one extra candidate word rather than a lost question.

    >>> expand("差扰是什么")[0]
    '差扰是什么 parallax'

Three properties worth keeping:

* longest match wins, no overlap -- ``逻辑处理器`` must not also fire ``处理器``;
* one Chinese term may produce several English ones (``core-shard`` and
  ``core shard``), because writers use both;
* the map is rebuilt from the文件 when ``--force`` is passed, but cached in
  memory otherwise: the tables are read on every query otherwise.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("MLOG_REPO", HERE.parent))
GLOSSARY = ROOT / "knowledge" / "GLOSSARY.md"
ALIASES = ROOT / "data" / "game" / "aliases.json"

CJK = re.compile(r"[\u3400-\u9fff]")
ROW = re.compile(r"^\|([^|]*)\|([^|]*)\|")

_CACHE: dict[str, dict[str, list[str]]] = {}


def _clean(text: str) -> str:
    return text.replace("`", "").replace("*", "").strip()


def _english_forms(text: str) -> list[str]:
    """``micro-processor`` -> ['micro-processor', 'micro processor']."""
    text = _clean(text)
    out = [text]
    if "-" in text:
        out.append(text.replace("-", " "))
    return [t.strip() for t in out if t.strip()]


def _add(table: dict[str, list[str]], chinese: str, english: str) -> None:
    chinese = _clean(chinese)
    english = _clean(english)
    if not chinese or not english:
        return
    for form in _english_forms(english):
        lst = table.setdefault(chinese, [])
        if form.lower() not in {x.lower() for x in lst}:
            lst.append(form)


def _from_glossary(table: dict[str, list[str]]) -> int:
    if not GLOSSARY.is_file():
        return 0
    rows = 0
    inside_auto = False
    for line in GLOSSARY.read_text(encoding="utf-8", errors="replace").splitlines():
        head = line.strip()
        if head.startswith("<!-- AUTO"):
            inside_auto = "BEGIN" in head
            continue
        m = ROW.match(head)
        if not m:
            continue
        left, mid = m.group(1).strip(), m.group(2).strip()
        # hand-written table: Chinese term | English | what it is | where
        # generated tables:    id | official English | official Chinese | legacy
        if inside_auto:
            # generated: col1 is the English id, col2 its English name,
            # col3 the official Chinese name, col4 the legacy names
            cells = [c.strip() for c in head.strip("|").split("|")]
            if (len(cells) >= 4 and left and not CJK.search(left)
                    and CJK.search(cells[2] + cells[3])):
                for zh in (cells[2] + " / " + cells[3]).split("/"):
                    for en in (cells[0], cells[1]):
                        _add(table, zh, en)
                rows += 1
            continue
        if not inside_auto and CJK.search(left) and mid and not CJK.search(mid):
            for zh in left.split("/"):
                _add(table, zh, mid)
            rows += 1
    return rows


def _from_aliases(table: dict[str, list[str]]) -> int:
    if not ALIASES.is_file():
        return 0
    try:
        data = json.loads(ALIASES.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return 0
    rows = 0
    for ident, names in data.items():
        if not isinstance(names, list):
            continue
        for zh in names:
            if CJK.search(zh or ""):
                _add(table, zh, ident)
                rows += 1
    return rows


def table(force: bool = False) -> dict[str, list[str]]:
    key = str(ROOT)
    if force or key not in _CACHE:
        t: dict[str, list[str]] = {}
        _from_glossary(t)
        _from_aliases(t)
        _CACHE[key] = t
    return _CACHE[key]


def matches(query: str) -> list[tuple[str, list[str]]]:
    """Longest-first, non-overlapping Chinese terms found in ``query``."""
    t = table()
    if not t or not CJK.search(query):
        return []
    keys = sorted(t, key=len, reverse=True)
    taken = [False] * len(query)
    found: list[tuple[str, list[str]]] = []
    for key in keys:
        start = 0
        while True:
            i = query.find(key, start)
            if i < 0:
                break
            end = i + len(key)
            if not any(taken[i:end]):
                for j in range(i, end):
                    taken[j] = True
                found.append((key, t[key]))
            start = i + 1
    found.sort(key=lambda p: query.find(p[0]))
    return found


def expand(query: str, limit: int = 8) -> tuple[str, list[tuple[str, list[str]]]]:
    """Return ``(query + english terms, matched)``; unchanged when nothing matches."""
    if os.environ.get("MLOG_NO_EXPAND"):
        return query, []
    hit = matches(query)
    if not hit:
        return query, []
    words: list[str] = []
    seen = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9_.-]*", query)}
    for _, english in hit:
        for w in english:
            if w.lower() not in seen:
                seen.add(w.lower())
                words.append(w)
    if not words:
        return query, hit
    return (query + " " + " ".join(words[:limit]), hit)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        t = table()
        print("%d Chinese terms, %d English forms"
              % (len(t), sum(len(v) for v in t.values())))
        return 0
    q = " ".join(args)
    out, hit = expand(q)
    for zh, en in hit:
        print("  %-12s -> %s" % (zh, ", ".join(en)))
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
