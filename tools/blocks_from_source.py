"""Extract block behaviour from `Blocks.java` into `block_attrs.json`.

Why this exists: `mlog.py id` already knows every block's content id and size,
but writing logic also needs to know what a block *does*: what it accepts, what
it produces, how much it holds, how long it takes. Without this table every
logistics program re-derives the same facts by reading Java.

Captured per block (only what the source sets):
  size, itemCapacity, liquidCapacity, craftTime, hasPower, hasItems, hasLiquids,
  outputItem / outputItems, inputs (from `consumeItems(...)`),
  power (from `consumePower(...)`), liquids (from `consumeLiquid(...)`).

Run:  python tools/blocks_from_source.py [--check]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOCKS = ROOT / "Mindustry-Source/core/src/mindustry/content/Blocks.java"
OUT = pathlib.Path(__file__).resolve().parent / "block_attrs.json"

_START = re.compile(r'^(\s*)(\w+) = new (\w+)\("([a-z0-9-]+)"\)\{\{')
_NUM = r"(-?\d+(?:\.\d+)?)f?"


def entries(text: str) -> list[tuple[str, str, str, list[str]]]:
    """(field, class, content name, body lines) for every `new X("name"){{ }};`."""
    out: list[tuple[str, str, str, list[str]]] = []
    cur: tuple[str, str, str, list[str]] | None = None
    indent = 0
    for line in text.split("\n"):
        if cur is None:
            m = _START.match(line)
            if m:
                indent = len(m.group(1))
                cur = (m.group(2), m.group(3), m.group(4), [])
            continue
        if line.strip() in ("}};", "};") and len(line) - len(line.lstrip()) <= indent:
            out.append(cur)
            cur = None
            continue
        cur[3].append(line)
    return out


def _kebab(java_field: str) -> str:
    """`phaseFabric` -> `phase-fabric`. The JSON is read by the CLI, so names
    must be content names, not Java field names -- `phaseFabric` looks right and
    matches nothing."""
    return re.sub(r"(?<!^)(?=[A-Z])", "-", java_field).lower()


def _items(arg: str) -> list[str]:
    """`Items.copper, 30, Items.lead, 25` -> ['copper:30', 'lead:25']."""
    toks = [t.strip() for t in arg.split(",")]
    pairs: list[str] = []
    i = 0
    while i + 1 < len(toks):
        name = _kebab(toks[i].replace("Items.", "").strip())
        amount = toks[i + 1].strip()
        if name and re.fullmatch(r"-?\d+", amount):
            pairs.append(f"{name}:{amount}")
            i += 2
        else:
            i += 1
    return pairs


def body_facts(body: list[str]) -> dict:
    text = "\n".join(body)
    rec: dict = {}

    for field in ("size", "itemCapacity", "liquidCapacity", "craftTime"):
        m = re.search(r"^\s*" + field + r"\s*=\s*" + _NUM + r"\s*;", text, re.M)
        if m:
            rec[field] = m.group(1)

    for flag in ("hasPower", "hasItems", "hasLiquids", "update", "solid"):
        if re.search(r"^\s*" + flag + r"\s*=\s*true\s*;", text, re.M):
            rec[flag] = True

    m = re.search(r"^\s*outputItem\s*=\s*new ItemStack\(Items\.(\w+),\s*(\d+)\)", text, re.M)
    if m:
        rec["outputItem"] = f"{_kebab(m.group(1))}:{m.group(2)}"

    m = re.search(r"^\s*outputItems\s*=\s*new ItemStack\[\]\{(.*?)\}", text, re.S | re.M)
    if m:
        outs = re.findall(r"new ItemStack\(Items\.(\w+),\s*(\d+)\)", m.group(1))
        rec["outputItems"] = [f"{_kebab(a)}:{b}" for a, b in outs]

    m = re.search(r"consumeItems\(with\((.*?)\)\)", text, re.S)
    if m:
        rec["inputs"] = _items(m.group(1))
    else:
        # single-item crafters (graphite-press, silicon-arc-furnace, ...) use
        # `consumeItem`, which the first version missed -- 10 recipes instead of
        # the real number.
        one = re.search(r"consumeItem\(Items\.(\w+),\s*(\d+)\)", text)
        if one:
            rec["inputs"] = [f"{_kebab(one.group(1))}:{one.group(2)}"]

    m = re.search(r"^\s*consumePower\(" + _NUM + r"\)", text, re.M)
    if m:
        rec["power"] = m.group(1)

    m = re.search(r"consumeLiquids?\(with\((.*?)\)\)", text, re.S)
    if m:
        rec["liquids"] = _items(m.group(1))

    return rec


def build() -> dict:
    text = BLOCKS.read_text("utf-8", errors="replace")
    blocks: dict[str, dict] = {}
    classes: dict[str, str] = {}
    for _field, cls, name, body in entries(text):
        facts = body_facts(body)
        if not facts:
            continue
        blocks[name] = facts
        classes[name] = cls
    return {
        "_source": "Mindustry-Source/core/src/mindustry/content/Blocks.java",
        "_note": ("recipes and capacities as written in the source; a block "
                  "absent here sets none of the captured fields"),
        "count": len(blocks),
        "blocks": blocks,
        "classes": classes,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = build()
    text = json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if args.check:
        cur = OUT.read_text("utf-8") if OUT.exists() else ""
        same = cur == text
        print(("ok      " if same else "STALE   ") + f"{OUT.name}: {data['count']} blocks")
        return 0 if same else 1
    OUT.write_text(text, "utf-8")
    recipes = sum(1 for b in data["blocks"].values() if "inputs" in b and "outputItem" in b)
    print(f"wrote {OUT.name}: {data['count']} blocks, {recipes} with a full recipe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
