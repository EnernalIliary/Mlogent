"""Generate knowledge/INDEX.en.md — the English door into the knowledge base.

Chinese stays the source of truth (see knowledge/README.md and CONVENTIONS.md);
this index exists so an English-only reader (or model) can find the right
article without guessing at Chinese titles. Titles and one-line summaries come
from knowledge/00-data/en_titles.json; the routing prose below is hand-written.

Usage:
  python knowledge/tools/gen_index_en.py            # check
  python knowledge/tools/gen_index_en.py --write    # rewrite INDEX.en.md
"""
from __future__ import annotations

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
KB = os.path.join(ROOT, "knowledge")
DATA = os.path.join(KB, "00-data", "en_titles.json")
OUT = os.path.join(KB, "INDEX.en.md")

HEAD = """# Knowledge base — English index

The source of truth is Chinese: `knowledge/README.md` (how the library is
organised) and `knowledge/CONVENTIONS.md` (what a claim must look like). This
file is the English door: same articles, English titles, one sentence each.

Two rules that survive translation:

- **`null` is not `pass`.** Any field that says "not measured" must not be read
  as "fine" — that convention runs through every article here.
- **Names come from the game bundle.** `parallax` is 差扰, not 牵引塔. The
  three-layer name table (official / legacy / colloquial) is in
  [GLOSSARY.md](GLOSSARY.md).

## Where to start

| You want | Read |
|---|---|
| the execution model: tick, instruction budget, accumulator | `01-execution/E01` |
| why a statement silently does nothing | `01-execution/E02` |
| variable, object and memory-cell limits | `01-execution/E03` |
| link names and `@`-variables, and why a rename breaks them | `01-execution/E05` |
| a pattern that already works (bus, counters, multicontrol) | `07-patterns/P03`, `P07`, `P08` |
| Mindcode: compiling `.mnd`, syntax, source maps | `06-mlog/M09`, `M10` |
| what a verification result looks like | `04` in `docs/实施记录.md` |
| a number with a source anchor | `02-world/W1x`, or `00-data/*.json` |

## Articles
"""


def load():
    with io.open(DATA, encoding="utf-8") as fh:
        return json.load(fh)


def article_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(KB):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("_") and d != "tools")
        for fn in sorted(filenames):
            if fn.endswith(".md") and len(fn) > 3 and fn[0].isupper() and fn[1:3].isdigit():
                out.append(os.path.relpath(os.path.join(dirpath, fn), ROOT).replace("\\", "/"))
    return sorted(out)


def render():
    titles = load()
    files = article_files()
    missing = [f for f in files if f not in titles]
    groups: dict[str, list[str]] = {}
    for path in files:
        groups.setdefault(path.split("/")[1], []).append(path)

    order = ["01-execution", "02-world", "03-combat", "04-units", "05-campaign",
             "06-mlog", "07-patterns", "08-evidence"]
    lines = [HEAD]
    for group in order + sorted(set(groups) - set(order)):
        if group not in groups:
            continue
        lines.append("### `%s/` — %d articles" % (group, len(groups[group])))
        lines.append("")
        lines.append("| Article | Title | What it says |")
        lines.append("|---|---|---|")
        for path in groups[group]:
            meta = titles.get(path, {})
            title = meta.get("en_title", "_(missing — add it to 00-data/en_titles.json)_")
            summary = meta.get("en_summary", "")
            name = os.path.basename(path)[:-3]
            lines.append("| [`%s`](%s) | %s | %s |" % (name, path[len("knowledge/"):], title, summary))
        lines.append("")

    if missing:
        lines.append("## Missing English titles")
        lines.append("")
        for path in missing:
            lines.append("- `%s`" % path)
        lines.append("")

    extra = sorted(set(titles) - set(files))
    if extra:
        lines.append("## Stale entries (file no longer exists)")
        lines.append("")
        for path in extra:
            lines.append("- `%s`" % path)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n", missing, extra


def main(argv):
    text, missing, extra = render()
    if "--write" in argv:
        with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("index_en: wrote %d articles, %d missing, %d stale"
              % (len(article_files()) - len(missing), len(missing), len(extra)))
        return 0
    current = io.open(OUT, encoding="utf-8", newline="").read() if os.path.exists(OUT) else ""
    if missing:
        print("index_en: %d article(s) without an English title: %s"
              % (len(missing), ", ".join(os.path.basename(m) for m in missing)), file=sys.stderr)
        return 1
    if extra:
        print("index_en: %d stale title(s): %s"
              % (len(extra), ", ".join(os.path.basename(m) for m in extra)), file=sys.stderr)
        return 1
    if current != text:
        print("index_en: stale -- run with --write", file=sys.stderr)
        return 1
    print("index_en: up to date (%d articles)" % len(article_files()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
