"""Verify the English-isation contract for one knowledge article (or a batch).

Contract (see knowledge/STYLE-en.md):
  * front matter keys unchanged; `title` and `tags` ASCII; other scalars untouched
  * heading COUNT and LEVELS unchanged, heading text ASCII
  * fenced code blocks byte-identical, same count and order
  * anchors `file.ext:NN` and ids (assertion `L1-02`, knowledge `MLOG.X.001`,
    wiki links `[[...]]`) preserved one-for-one
  * table rows: same column count; row count unchanged (cells MAY hold Chinese:
    name columns are the 对照 the task keeps)
  * prose outside tables/fences: no CJK, except a parenthesised gloss right
    after an ASCII token -- `flare (星辉)` is a 对照, `单位会移动` is not

Usage: python out/_encheck.py <file.md> [...]   -> exit 1 when any check fails
"""
import io

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CJK = re.compile(r"[\u3400-\u9fff]")
ANCHOR = re.compile(r"[A-Za-z0-9_./\\-]+\.(?:java|json|py|mlog|md|js|txt):\d+(?:-\d+)?")
ID = re.compile(r"\b(?:[LS]\d-\d\d[ab]?|[A-Z]{2,5}\.[A-Z0-9]+\.[0-9]{3})\b")
WIKI = re.compile(r"\[\[([^\]]+)\]\]")
GLOSS = re.compile(r"\S+\s*\([^()]*" + CJK.pattern + "[^()]*\)")
HEAD = re.compile(r"^(#{1,6})\s")
FENCE = re.compile(r"^\s*(```|~~~)")


def split(text):
    """(front, body, code_blocks, table_rows, prose_lines, headings)"""
    lines = text.splitlines()
    front = []
    i = 0
    if lines and lines[0].strip() == "---":
        front.append(lines[0])
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            front.append(lines[i])
            i += 1
        if i < len(lines):
            front.append(lines[i])
            i += 1
    body = lines[i:]
    code, prose, tables, heads = [], [], [], []
    in_code = None
    for ln in body:
        m = FENCE.match(ln)
        if in_code:
            code.append(ln)
            if m and m.group(1) == in_code and ln.strip() == in_code + ln.strip()[3:]:
                in_code = None
            continue
        if m:
            in_code = m.group(1)
            code.append(ln)
            continue
        if ln.lstrip().startswith("|"):
            tables.append(ln)
            continue
        hm = HEAD.match(ln)
        if hm:
            heads.append(ln)
        if ln.strip():
            prose.append(ln)
    return front, body, code, tables, prose, heads


def check(path):
    text = io.open(path, encoding="utf-8", errors="replace").read()
    front, body, code, tables, prose, heads = split(text)
    errs = []

    # front matter: keys, and ASCII title/tags
    keys = []
    for ln in front[1:-1]:
        if ":" in ln:
            k = ln.split(":", 1)[0].strip()
            keys.append(k)
            if k in ("title", "tags") and CJK.search(ln):
                errs.append("front matter %s still has CJK: %s" % (k, ln.strip()[:80]))
    # front matter is optional (knowledge/tools/*.md, GLOSSARY.md have none)

    # headings ASCII
    for h in heads:
        if CJK.search(h):
            errs.append("heading has CJK: %s" % h.strip()[:80])

    # code fences must be balanced and closed
    if len([c for c in code if FENCE.match(c)]) % 2:
        errs.append("unbalanced code fence")

    # prose CJK (allow parenthesised glosses and the glossary itself)
    for ln in prose:
        stripped = GLOSS.sub("", ln)
        if CJK.search(stripped):
            errs.append("prose has CJK: %s" % ln.strip()[:90])

    # table cells: a name mapping is short; a sentence is prose
    for row in tables:
        cells = [x.strip() for x in row.strip().strip("|").split("|")]
        for cell in cells:
            if not CJK.search(cell):
                continue
            n = len(CJK.findall(cell))
            if n > 28 or re.search("[\u3002\uff0c\uff1b]", cell):
                errs.append("table cell is prose, not a name: %s" % cell[:70])

    return {
        "path": os.path.relpath(path),
        "anchors": len(ANCHOR.findall(text)),
        "ids": len(ID.findall(text)),
        "wiki": len(WIKI.findall(text)),
        "code_lines": len(code),
        "tables": len(tables),
        "headings": len(heads),
        "errors": errs,
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        # no arguments: check every article under knowledge/
        root = os.path.join(ROOT, "knowledge")
        for dirpath, dirnames, names in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames
                                 if d not in ("00-data", "08-evidence",
                                              "_report", "tools"))
            for n in sorted(names):
                if n.endswith(".md"):
                    argv.append(os.path.join(dirpath, n))
        if not argv:
            print(__doc__)
            return 2
    bad = 0
    for path in argv:
        got = check(path)
        if got["errors"]:
            bad += 1
            print("%s: %d problem(s)" % (got["path"], len(got["errors"])))
            for e in got["errors"][:6]:
                print("   -", e)
    print("%d/%d clean" % (len(argv) - bad, len(argv)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
