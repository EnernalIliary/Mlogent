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
import sys

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


# How a block treats incoming items. Derived from every `acceptItem` override in
# `core/src/mindustry` (v159.3) plus the inherited `BuildingComp` behaviour:
#
#   ACCEPT_ANY    -- overrides acceptItem to compare capacity only. Takes any
#                    item, no config involved.
#   ACCEPT_CUSTOM -- overrides acceptItem with a routing/state rule: takes items
#                    only under some condition (config, heat, ammo, empty
#                    buffer, team, an open output). "Does it accept X" is still
#                    yes; "will it accept X *now*" cannot be answered statically.
#   ACCEPT_NONE   -- `acceptItem` is literally `return false;`.
#   inherited     -- `block.consumesItem(item) && capacity`, and consumesItem is
#                    a bool array filled from the block's consumers, so RECIPE
#                    (only the inputs) or NONE (no item consumer at all).
ACCEPT_ANY = {"CoreBlock", "StorageBlock"}
ACCEPT_CUSTOM = {
    "Accelerator", "ArmoredConveyor", "BlockProducer", "Conveyor", "Duct",
    "DuctBridge", "DuctJunction", "DuctRouter", "Incinerator", "ItemBridge",
    "ItemIncinerator", "ItemTurret", "ItemVoid", "Junction", "LaunchPad",
    "MassDriver", "OverflowDuct", "OverflowGate", "PayloadLoader", "Router",
    "Sorter", "StackConveyor", "StackRouter", "UnitAssembler", "UnitCargoLoader",
    "UnitFactory",
}
ACCEPT_NONE = {
    "ContinuousLiquidTurret", "ItemSource", "LandingPad", "LiquidTurret",
    "PayloadUnloader",
}


def ammo_items(body: list[str]) -> list[str]:
    """Items listed in `ammo(...)` for an ItemTurret.

    Every ammo entry is `Items.<field>, new <BulletType>(...)` repeated, so the
    item fields are the only `Items.x` references at the argument level. Bullet
    types inside the list do not mention items, so a flat scan is safe here --
    and if that ever stops being true, the worst case is an extra name in a
    list that is shown, never acted on.
    """
    text = "\n".join(body)
    i = text.find("ammo(")
    if i < 0:
        return []
    depth = 0
    for j in range(i + 4, len(text)):
        c = text[j]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                span = text[i + 5:j]
                break
    else:
        return []
    out: list[str] = []
    for m in re.finditer(r"Items\.(\w+)", span):
        name = _kebab(m.group(1))
        if name not in out:
            out.append(name)
    return out


def accepts(cls: str, facts: dict) -> str:
    """One of: any | custom | none | recipe.

    `none` is not "unknown": `BuildingComp.acceptItem` is
    `block.consumesItem(item) && ...` and `consumesItem` is a bool array filled
    from the block's consumers, so a block with no item consumer really does
    refuse every item. Do not infer it from itemCapacity -- most crafters never
    write itemCapacity and still hold 10.
    """
    if cls in ACCEPT_NONE:
        return "none"
    if cls in ACCEPT_ANY:
        return "any"
    if cls in ACCEPT_CUSTOM:
        return "custom"
    return "recipe" if facts.get("inputs") else "none"


def unclassified() -> list[str]:
    """Classes that override acceptItem but are in none of the three sets.

    The sets are hand-derived from the source; this guard is what keeps them
    honest when the game adds a block class.
    """
    src = ROOT / "Mindustry-Source/core/src/mindustry"
    known = ACCEPT_ANY | ACCEPT_CUSTOM | ACCEPT_NONE
    out = []
    for p in src.rglob("*.java"):
        body = p.read_text("utf-8", errors="replace")
        if p.stem in ("BuildingComp", "Block"):
            continue                       # the inherited default, not a block
        if "public boolean acceptItem(" in body and p.stem not in known:
            out.append(p.stem)
    return sorted(out)


def build() -> dict:
    text = BLOCKS.read_text("utf-8", errors="replace")
    blocks: dict[str, dict] = {}
    classes: dict[str, str] = {}
    for _field, cls, name, body in entries(text):
        facts = body_facts(body)
        rule = accepts(cls, facts)
        if not facts and rule not in ("any", "custom"):
            continue                       # nothing interesting to say
        if cls == "ItemTurret":
            ammo = ammo_items(body)
            if ammo:
                facts["ammo"] = ammo
                rule = "ammo"
        facts["accepts"] = rule
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
    gap = unclassified()
    if gap:
        print("WARNING classes overriding acceptItem but unclassified: "
              + ", ".join(gap), file=sys.stderr)
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
