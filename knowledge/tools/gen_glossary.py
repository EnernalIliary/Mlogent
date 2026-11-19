"""Regenerate the entity tables inside knowledge/GLOSSARY.md.

The hand-written half (concepts, three layers of naming) is never touched; only
the region between the AUTO markers is rewritten, so the file stays reviewable
and a stale table is a diff instead of a mystery.

Usage:
  python knowledge/tools/gen_glossary.py            # check
  python knowledge/tools/gen_glossary.py --write    # rewrite the AUTO region
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BUNDLES = os.path.join(ROOT, "data", "game", "bundles")
ALIASES = os.path.join(ROOT, "data", "game", "aliases.json")
PAGE = os.path.join(ROOT, "knowledge", "GLOSSARY.md")

BEGIN = "<!-- AUTO:BEGIN"
END = "<!-- AUTO:END -->"

SECTION_TITLE = {
    "items": "物品（items）",
    "liquids": "液体（liquids）",
    "units": "单位（units）",
    "blocks": "方块（blocks）",
}
KEY_PREFIX = {"items": "item", "liquids": "liquid", "units": "unit", "blocks": "block"}


def _bundle(name: str) -> dict:
    path = os.path.join(BUNDLES, name)
    out: dict[str, str] = {}
    with io.open(path, encoding="utf-8", newline="") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip()
    return out


def _names(kind: str, bundles: tuple[dict, dict]) -> dict:
    """id -> (english, chinese) from <prefix>.<id>.name keys."""
    eng, chs = {}, {}
    prefix = KEY_PREFIX[kind] + "."
    for bundle, sink in ((bundles[0], eng), (bundles[1], chs)):
        for key, value in bundle.items():
            if key.startswith(prefix) and key.endswith(".name"):
                sink[key[len(prefix):-len(".name")]] = value
    return {i: (eng.get(i, ""), chs.get(i, "")) for i in eng.keys() | chs.keys()}


def _clean(text: str) -> str:
    """Drop bundle colour markup and collapse pipes so the row survives Markdown."""
    text = re.sub(r"\[[^\]]*\]", "", text)
    return text.replace("|", "\\|").strip()


def render() -> str:
    eng = _bundle("bundle.properties")
    chs = _bundle("bundle_zh_CN.properties")
    with io.open(ALIASES, encoding="utf-8") as fh:
        aliases = json.load(fh)

    blocks = []
    blocks.append("<!-- AUTO:BEGIN —— 以下由 knowledge/tools/gen_glossary.py 生成，勿手改 -->")
    blocks.append("")
    blocks.append("## 3. 实体名对照（生成）")
    blocks.append("")
    blocks.append("「旧译与口语」列来自 `data/game/aliases.json`：第一个别名恒为官方中文名，"
                  "其后是早年翻译与口语；与任何官方名撞车的会被生成器剔除。")
    blocks.append("")

    for kind in ("items", "liquids", "units", "blocks"):
        rows = []
        table = aliases.get(kind, {})
        named = _names(kind, (eng, chs))
        ids = sorted(set(table) | set(named))
        for ident in ids:
            names = table.get(ident) or []
            official_zh = names[0] if names else named.get(ident, ("", ""))[1]
            legacy = ", ".join(names[1:]) if len(names) > 1 else ""
            english = named.get(ident, ("", ""))[0] or ident
            if not official_zh:
                continue
            rows.append("| `%s` | %s | %s | %s |" % (
                ident, _clean(english), _clean(official_zh), _clean(legacy)))
        blocks.append("### %s %d 条" % (SECTION_TITLE[kind], len(rows)))
        blocks.append("")
        blocks.append("| id | 官方英文名 | 官方中文名 | 旧译与口语 |")
        blocks.append("|---|---|---|---|")
        blocks.extend(rows)
        blocks.append("")

    blocks.append("<!-- AUTO:END -->")
    return "\n".join(blocks).rstrip() + "\n"


def main(argv):
    write = "--write" in argv
    with io.open(PAGE, encoding="utf-8", newline="") as fh:
        page = fh.read()
    start = page.find(BEGIN)
    end = page.find(END)
    if start < 0 or end < 0:
        print("GLOSSARY.md is missing the AUTO markers", file=sys.stderr)
        return 2
    body = render()
    new = page[:start] + body + page[end + len(END):].lstrip("\n")
    if not write:
        if new == page:
            print("glossary: up to date")
            return 0
        print("glossary: stale -- run with --write", file=sys.stderr)
        return 1
    if new != page:
        with io.open(PAGE, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new)
    rows = sum(1 for ln in body.splitlines() if ln.startswith("| `"))
    print("glossary: wrote %d rows" % rows)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
