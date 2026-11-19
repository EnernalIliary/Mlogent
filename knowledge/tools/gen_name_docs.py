#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_name_docs.py — generate the five Chinese/English name-mapping articles from the en/zh
bundles plus 00-data (reads the bundles only; never edits the data tables).

Usage:
    python knowledge/tools/gen_name_docs.py            # write 02-world/W13..W16 and 04-units/U06
    python knowledge/tools/gen_name_docs.py --check    # diff against disk (exit 1 on drift), write nothing

Data sources:
    data/game/bundles/bundle.properties       English display names (in-repo, preferred)
    data/game/bundles/bundle_zh_CN.properties Chinese display names (in-repo, preferred)
    knowledge/00-data/{blocks,units,items,liquids,status}.json  (full id set and grouping)
    the bundle directory is looked for in $MLOG_BUNDLES, then this repo's data/game/bundles/,
    assetsraw/, and a sibling TextureMDT/ (the split-out game-asset tree) — the asset tree only
    overrides; line numbers must still match the in-repo copies.
Key rule: <kind>.<id>.name with kind in block/unit/item/liquid/status.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KB = HERE.parent
REPO = KB.parent


def _bundle_dirs():
    """Candidate bundle directories, most local first.

    `data/game/bundles/` wins so the generator runs in a clean checkout (CI
    included).  The extracted asset tree stays as an override: `MLOG_BUNDLES`
    for an explicit directory, then the sibling TextureMDT / assetsraw trees
    people keep outside the repo.  Line numbers baked into the generated docs
    ("zh:N" / "en:N") are line numbers *of these files*, so an override only
    stays honest while it is byte-identical to the vendored copy.
    """
    return [os.environ.get("MLOG_BUNDLES"),
            REPO / "data" / "game" / "bundles",
            REPO / "assetsraw" / "assets" / "bundles",
            REPO.parent / "TextureMDT" / "assets" / "bundles",
            REPO.parent / "Mindustry_assetsraw" / "assets" / "bundles",
            REPO.parent / "assetsraw" / "assets" / "bundles"]


def _bundle(name: str) -> Path:
    for d in _bundle_dirs():
        if not d:
            continue
        p = Path(d) / name
        if p.is_file():
            return p
    raise SystemExit("%s not found; looked in:\n  %s"
                     % (name, "\n  ".join(str(d) for d in _bundle_dirs() if d)))


B_EN = _bundle("bundle.properties")
B_ZH = _bundle("bundle_zh_CN.properties")
DATA = KB / "00-data"

KV_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*=\s*(.*)$")
# Mindustry 的颜色/标记形式，如 [lightgray]、[accent]、[#ff0000]
TAG_RE = re.compile(r"\[[a-zA-Z#][a-zA-Z0-9#_]{0,15}\]")
MAX_LINES = 250


def _dep(path: Path) -> str:
    """Path as written into front matter: repo-relative when it is in the repo.

    `MLOG_BUNDLES` may point at an asset checkout elsewhere (that is how you
    check line provenance against a freshly extracted tree), and front matter
    must not blow up on a path outside the repo.
    """
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return path.as_posix()


def _line_count(path: Path) -> int:
    """Lines in a bundle file -- the docs cite "zh:N", so the count must be real."""
    with path.open(encoding="utf-8-sig", errors="replace") as fh:
        return sum(1 for _ in fh)


def load_bundle(path: Path):
    out = {}
    with path.open(encoding="utf-8-sig", errors="replace") as fh:
        for i, raw in enumerate(fh, 1):
            m = KV_RE.match(raw.rstrip("\r\n"))
            if m:
                out[m.group(1)] = (m.group(2).strip(), i)
    return out


E = load_bundle(B_EN)
Z = load_bundle(B_ZH)


def clean(s: str) -> str:
    return TAG_RE.sub("", s).strip()


def names(kind: str, ident: str):
    """返回 (英文名, 英文行, 中文名, 中文行)，缺失为 None。"""
    key = kind + "." + ident + ".name"
    e = E.get(key)
    z = Z.get(key)
    return (clean(e[0]) if e else None, e[1] if e else None,
            clean(z[0]) if z else None, z[1] if z else None)


def rows(kind: str, idents):
    out = []
    for ident in idents:
        en, el, zh, zl = names(kind, ident)
        out.append((
            "`" + ident + "`",
            en or "—",
            zh or "—",
            ("zh:%d" % zl) if zl else "—",
            ("en:%d" % el) if el else "—",
        ))
    return out


def recs(name: str):
    obj = json.loads((DATA / name).read_text(encoding="utf-8-sig"))
    if isinstance(obj, dict):
        for k in ("records", "items", "entries", "rows", "data"):
            if isinstance(obj.get(k), list):
                return obj[k]
        return [v for v in obj.values() if isinstance(v, dict)]
    return obj


BLOCKS = recs("blocks.json")
UNITS = recs("units.json")
ITEMS = recs("items.json")
LIQUIDS = recs("liquids.json")
STATUS = recs("status.json")

TERRAIN_TYPES = {"floor", "wall", "ore"}
INDUSTRY_CATS = ["distribution", "power", "liquid", "production", "defense"]
COMBAT_CATS = ["crafting", "turret", "effect", "units", "logic"]


def is_terrain(b):
    return bool(set(b.get("types") or []) & TERRAIN_TYPES)


def terrain_blocks():
    return sorted((b for b in BLOCKS if is_terrain(b)),
                  key=lambda b: ((b.get("types") or [""])[0], b["id"]))


def cat_blocks(cats):
    return sorted((b for b in BLOCKS if b.get("category") in cats and not is_terrain(b)),
                  key=lambda b: (cats.index(b["category"]), b["id"]))


def coverage(kind, idents):
    hit = sum(1 for i in idents if names(kind, i)[2] or names(kind, i)[0])
    zh_only = sum(1 for i in idents if names(kind, i)[2])
    return hit, zh_only, len(idents)


def fm(art_id, title, data_refs, depends, tags, extra_src=()):
    src = [
        "%s:1-%d" % (_dep(B_ZH), _line_count(B_ZH)),
        "%s:1-%d" % (_dep(B_EN), _line_count(B_EN)),
    ] + list(extra_src)
    lines = ["---", "id: " + art_id, "title: " + title, "domain: " +
             ("world" if art_id.startswith("WORLD") else "unit"),
             "status: active", "ver: [v160.7_rt, v159.3_src]", "conf: S",
             "src:"]
    lines += ["  - \"" + s + "\"" for s in src]
    lines.append("data:")
    lines += ["  - \"" + d + "\"" for d in data_refs]
    lines.append("depends: [" + ", ".join(depends) + "]")
    lines.append("tags: [" + ", ".join(tags) + "]")
    lines.append("---")
    return lines


HDR = ("id", "English name", "Chinese name", "Chinese name source", "English name source")


def table(idents, kind="block"):
    lines = ["| " + " | ".join(HDR) + " |", "|" + "|".join(["---"] * len(HDR)) + "|"]
    for r in rows(kind, idents):
        lines.append("| " + " | ".join(r) + " |")
    return lines


def doc1():
    tb = terrain_blocks()
    ids = [b["id"] for b in tb]
    hit, zh_only, total = coverage("block", ids)
    art = "WORLD.NAMES.001"
    L = fm(art, "Block name mapping I - terrain / ore / walls (%d entries)" % total,
           ["00-data/blocks.json"],
           ["WORLD.BLOCKS.001", "WORLD.TERRAIN.001"],
           ["names", "chinese-name", "english-name", "translation", "mapping-table",
            "terrain", "ore", "walls"])
    L += [
        "",
        "## One line",
        "",
        "A Chinese name on screen is neither the id nor a literal translation of the English "
        "name; to cross-reference a map, the sandbox and a guide, use this table first to turn "
        "\"the name you saw\" into an id, then look up mechanics and numbers in the main "
        "articles.",
        "",
        "## Rules / formulas",
        "",
        "- The only source of a display name is the language bundle: `block.<id>.name` gives a "
        "block name and `<kind>.<id>.name` gives the remaining entities; this article only "
        "covers the terrain layer, `kind=block`.",
        "- Grouping follows the `types` field in 00-data: the %d entries containing `floor` / "
        "`wall` / `ore` are this article's scope, covering floors, ore layers, ore walls and "
        "editor-only terrain." % total,
        "- A \"—\" in the table means the bundle has no `.name` entry for that id; it does not "
        "mean the name is unknown, because such blocks normally show no name in the UI (editor "
        "placeholders, legacy leftovers, ore overlays).",
        "- A display string may carry colour markers (such as `[lightgray]`); the table strips "
        "the markers and keeps the text inside the parentheses.",
        "",
        "## Numbers",
        "",
        "This section lists names only and contains no numbers; health, size, armor and similar "
        "figures are in `00-data/blocks.json` and WORLD.BLOCKS.001.",
        "",
    ]
    L += table(ids)
    L += [
        "",
        "## Source anchors",
        "",
        "- `data/game/bundles/bundle_zh_CN.properties` - the Chinese display names; \"Chinese "
        "name source zh:N\" in the table is line N of that file.",
        "- `data/game/bundles/bundle.properties` - the English display names; \"English name "
        "source en:N\" is line N of that file.",
        "- `00-data/blocks.json` - the `id` / `types` / `category` fields; this article filters "
        "out %d entries by `types` (%d of which have a Chinese name)." % (total, zh_only),
        "- The generator script `knowledge/tools/gen_name_docs.py` (re-run it after a game "
        "version update; it does not modify 00-data).",
        "",
        "## Measurements and counter-examples",
        "",
        "- **Counter-example A** - `dacite` has the English name \"Dacite\" (geologically "
        "dacite), yet the official Chinese name is andesite (安山岩); and andesite's English "
        "name is \"Andesite\" as well. The Chinese and English names do not line up, so "
        "matching by geological name goes wrong.",
        "- **Counter-example B** - `char` has the English name \"Charred Stone\" and the Chinese "
        "name scorched earth (焦土) - neither a word-for-word translation nor a stone class (it "
        "is a floor).",
        "- **Counter-example C** - ore layer ids such as `ore-copper` / `ore-lead` / "
        "`ore-thorium` have no `.name` entry at all in the bundle; they appear in the sandbox "
        "menu as textures with no name shown. Searching ids for copper ore (铜矿) always comes "
        "up empty - you have to cross-reference the resource table in WORLD.DRILLING.001.",
        "- **Counter-example D** - the raw value of `block.launch-pad.name` is \"launch pad "
        "(发射台)[lightgray] (legacy version)\"; the colour marker is not part of the name, and "
        "copying it straight into a document drags `[lightgray]` along.",
        "- **Counter-example E** - `build1`–`build16`, `air`, `target-dummy` and `legacy-*` "
        "likewise have no `.name`; they are editor placeholders or legacy leftovers and are "
        "invisible in the player UI.",
        "",
        "## Common misconceptions",
        "",
        "- Using the Chinese name as an id: conveyor (传送带) is not an id, `conveyor` is; "
        "documents, blueprints and logic only accept ids.",
        "- Assuming the English name equals the id: `Titanium Conveyor` has spaces and capitals, "
        "while the id is `titanium-conveyor`.",
        "- Assuming the Chinese name is a literal translation of the English one: Duo (双管), "
        "Dagger (尖刀), Mender (修理器) are none of them word-for-word.",
        "- Assuming every block has a display name: %d of the %d entries here do not; a \"—\" "
        "means that block shows no name in the UI, not that the name is missing."
        % (total - zh_only, total),
        "",
        "## Related",
        "",
        "- WORLD.BLOCKS.001 (block model and multiblock anchors, the numeric conventions)",
        "- WORLD.TERRAIN.001 (terrain, the ore-layer and wall three-layer structure, movement "
        "multipliers)",
        "- WORLD.DRILLING.001 (ore layers and drill coverage, what ore-* is actually for)",
        "- WORLD.SANDBOX.001 (editor visibility and the build series placeholders)",
        "- WORLD.NAMES.002 / WORLD.NAMES.003 (the remaining block names)",
        "- EV.CHEAT.001 (cheat sheet)",
    ]
    return art, "02-world/W13-name-blocks-terrain.md", L


def doc2():
    bl = cat_blocks(INDUSTRY_CATS)
    ids = [b["id"] for b in bl]
    hit, zh_only, total = coverage("block", ids)
    art = "WORLD.NAMES.002"
    L = fm(art, "Block name mapping II - logistics / power / liquids / production "
           "(%d entries)" % total,
           ["00-data/blocks.json"],
           ["WORLD.BLOCKS.001", "WORLD.LOGISTICS.001"],
           ["names", "chinese-name", "english-name", "translation", "mapping-table",
            "logistics", "power", "liquids", "production"])
    L += [
        "",
        "## One line",
        "",
        "The Chinese name ↔ English name ↔ id mapping for the four buildable block groups - "
        "logistics, power, liquids and production; grouped by `category`, alphabetical by id "
        "inside each group.",
        "",
        "## Rules / formulas",
        "",
        "- The %d blocks whose `category` is one of {distribution, power, liquid, production, "
        "defense} (terrain, ore and walls are excluded - see WORLD.NAMES.001)." % total,
        "- The order is the table order: distribution first (conveyors, routers, junctions, "
        "bridges, drivers), then power, liquid, production, defense.",
        "- Display names come from `block.<id>.name`; a \"—\" means the bundle has no such "
        "entry (a hidden or placeholder block).",
        "- `defense` has only a handful of entries in this group; the walls and doors that "
        "actually decide defensive numbers are in WORLD.NAMES.001 and COMBAT.DEFENSE.001.",
        "",
        "## Numbers",
        "",
        "This section lists names only; power draw, capacity, speed and similar numbers follow "
        "`00-data/blocks.json` (see the measurement sections of WORLD.LOGISTICS.001 / "
        "WORLD.POWER.001).",
        "",
    ]
    L += table(ids)
    L += [
        "",
        "## Source anchors",
        "",
        "- `data/game/bundles/bundle_zh_CN.properties` (Chinese names, zh:N is the line number) "
        "and `bundle.properties` (English names, en:N is the line number).",
        "- The `category` field of `00-data/blocks.json` is this article's grouping key; %d of "
        "the %d entries have a Chinese name." % (zh_only, total),
        "- Generator script `knowledge/tools/gen_name_docs.py`.",
        "",
        "## Measurements and counter-examples",
        "",
        "- **Counter-example A** - `junction` is officially junction (交叉器), not "
        "\"intersection\"; router (路由器) is a different block, `router`. Calling junction an "
        "intersection by the literal reading lumps it in with doors and road blocks.",
        "- **Counter-example B** - `duct` is officially item duct (物品管道), not just "
        "\"duct\"; conveyor (传送带) is what `conveyor` means. The two sit at different tiers "
        "(ducts move bulk volume, conveyors one item at a time), so the names are close but not "
        "synonyms.",
        "- **Counter-example B** - `phase-conveyor` is phase conveyor bridge (相织布传送带桥) "
        "and `bridge-conduit` is conduit bridge (导管桥); both are called a \"bridge\", but one "
        "bridges conveyors and the other bridges liquid conduits.",
        "- **Counter-example C** - `mass-driver` is officially mass driver (质量驱动器), "
        "unrelated to motor and thruster class \"drivers\"; it is a long-range item delivery "
        "block (see WORLD.PAYLOAD.001).",
        "- **Counter-example D** - `unloader` is officially unloader (装卸器), not the common "
        "unloader (卸载器); `sorter` is officially sorter (分类器), not the common sorter "
        "(分拣器). Searching with the usual translations finds nothing.",
        "- **Counter-example E** - `force-projector` is force projector (力墙投影), also called "
        "force field projector (力场投影仪); the official string has no instrument (仪) "
        "character in it.",
        "",
        "## Common misconceptions",
        "",
        "- Confusing `router` (路由器) with `sorter` (分类器): the first splits flow evenly, the "
        "second filters by item; the mechanics are entirely different.",
        "- Assuming duct (管道) and conveyor (传送带) share an id: `duct` and `conveyor` are two "
        "independent logistics lines with different throughput conventions.",
        "- Assuming category is group: `category` is the internal class grouping (it covers all "
        "%d entries here), while `group` covers only part of the buildable blocks, with 240 "
        "entries at `none`." % total,
        "",
        "## Related",
        "",
        "- WORLD.LOGISTICS.001 (conveyor throughput conventions, and bridge and junction "
        "queuing)",
        "- WORLD.POWER.001 (the power network)",
        "- WORLD.LIQUIDS.001 (liquids and conduits)",
        "- WORLD.STORAGE.001 (containers, vaults, core capacity)",
        "- WORLD.PAYLOAD.001 (payloads and the mass driver)",
        "- WORLD.NAMES.001 / WORLD.NAMES.003 (the remaining block names)",
    ]
    return art, "02-world/W14-name-blocks-industry.md", L


def doc3():
    bl = cat_blocks(COMBAT_CATS)
    ids = [b["id"] for b in bl]
    hit, zh_only, total = coverage("block", ids)
    art = "WORLD.NAMES.003"
    L = fm(art, "Block name mapping III - crafting / turrets / effects / unit blocks / "
           "logic (%d entries)" % total,
           ["00-data/blocks.json"],
           ["WORLD.BLOCKS.001", "COMBAT.TURRET.001"],
           ["names", "chinese-name", "english-name", "translation", "mapping-table",
            "turret", "crafting", "logic", "unit-block"])
    L += [
        "",
        "## One line",
        "",
        "The Chinese name ↔ English name ↔ id mapping for fabricators, turrets, effect blocks, "
        "unit-building blocks and logic blocks; turret names are often imagery words, so "
        "confirm which table you are in before looking up numbers.",
        "",
        "## Rules / formulas",
        "",
        "- The %d blocks whose `category` is one of {crafting, turret, effect, units, logic} "
        "and which carry no terrain type." % total,
        "- The table runs crafting first, then turret, effect, units and logic, alphabetical by "
        "id inside each group.",
        "- Turret numbers are not in this article - see `00-data/turrets.json` and "
        "COMBAT.TURRET.001; unit numbers are in `00-data/units.json` and UNIT.MOVE.001.",
        "- The instruction semantics of the logic blocks (`logic-*`) belong to the 06-mlog "
        "domain; this article gives names only.",
        "",
        "## Numbers",
        "",
        "This section lists names only and carries no range, DPS or reload numbers; those "
        "figures live uniformly in COMBAT.TURRET.001 and COMBAT.NUMBERS.001.",
        "",
    ]
    L += table(ids)
    L += [
        "",
        "## Source anchors",
        "",
        "- `data/game/bundles/bundle_zh_CN.properties` (zh:N) and `bundle.properties` (en:N).",
        "- `00-data/blocks.json`: the `category` grouping; %d of the %d entries have a Chinese "
        "name." % (zh_only, total),
        "- Generator script `knowledge/tools/gen_name_docs.py`.",
        "",
        "## Measurements and counter-examples",
        "",
        "- **Counter-example A** - three naming strategies coexist in the turret Chinese names: "
        "`duo` = twin-barrel (双管) (a free translation), `scatter` = scatter (分裂) and `hail` "
        "= hail (冰雹) (imagery), `lancer` = Lancer (蓝瑟) (pure transliteration), `fuse` = "
        "thunder-light (雷光) (a coined word). Literal readings as scattering, lance and fuse "
        "never match the official strings.",
        "- **Counter-example B** - unit blocks (`category=units`) are the factories themselves, "
        "not units: the ground, air and naval factories and the tank, ship and mech fabricators "
        "all sit in the block table, while unit records live only in `00-data/units.json`; "
        "looking for a unit name such as `dagger` in the block table always comes up empty.",
        "- **Counter-example C** - the refabricators use non-literal terms: Additive → quantity "
        "tier (数增级), Multiplicative → multiplier tier (倍乘级), Exponential → power tier "
        "(多幂级), Tetrative → boundless tier (无量级); literal add, multiply and exponential "
        "readings find nothing.",
        "- **Counter-example D** - `core-shard` is \"Core: Shard\" in English and "
        "first-generation core (初代核心) in Chinese - not a literal translation (a literal one "
        "would be core: shard (核心：碎片)), so translating the English word by word never "
        "yields the Chinese name.",
        "- **Counter-example E** - the block `mender` is repairer (修理器); it shares the root "
        "of the repair and mend concepts in unit abilities, but it is a buildable block (see "
        "COMBAT.SUPPORT.001).",
        "- **Counter-example F** - `overdrive` as a status is overload (过载), yet as the block "
        "`overdrive-projector` it is overdrive projector (超速投影): same English root, "
        "different Chinese name, so overload projector (过载投影仪) finds nothing.",
        "- **Counter-example G** - the logic block `logic-processor` is logic processor "
        "(逻辑处理器) and `logic-display` is logic display (逻辑显示屏); the abbreviations LP and "
        "LD are community shorthand only, not display names.",
        "",
        "## Common misconceptions",
        "",
        "- Assuming turret Chinese names contain the character for \"cannon\": in the official "
        "strings `duo` is simply twin-barrel (双管) and `ripple` is ripple (涟漪), with no "
        "cannon (炮) character at all.",
        "- Treating the `effect` class as pure decoration: these blocks have real mechanics "
        "(such as `overdrive-projector`, overdrive projector (超速投影)); the name looks "
        "decorative but the mechanics are in COMBAT.STATUS.001.",
        "- Assuming a fabricator is named after its product: `silicon-smelter` is silicon "
        "smelter (硅冶炼厂) while the product is `silicon`, silicon (硅); the names differ.",
        "",
        "## Related",
        "",
        "- COMBAT.TURRET.001 (turret range, reload, ammo)",
        "- COMBAT.DEFENSE.001 (walls, doors, shields, the repairer)",
        "- COMBAT.STATUS.001 (statuses and overload)",
        "- WORLD.CRAFTING.001 (recipes and manufacturing)",
        "- UNIT.PRODUCE.001 (the unit production chain and unit blocks)",
        "- WORLD.NAMES.001 / WORLD.NAMES.002 (the remaining block names)",
    ]
    return art, "02-world/W15-name-blocks-combat.md", L


def doc4():
    items = [i["id"] for i in sorted(ITEMS, key=lambda r: r["id"])]
    liqs = [i["id"] for i in sorted(LIQUIDS, key=lambda r: r["id"])]
    sts = [i["id"] for i in sorted(STATUS, key=lambda r: r["id"])]
    art = "WORLD.NAMES.004"
    total = len(items) + len(liqs) + len(sts)
    zh_hit = sum(1 for kind, ids in (("item", items), ("liquid", liqs), ("status", sts))
                 for i in ids if names(kind, i)[2])
    st_zh = sum(1 for i in sts if names("status", i)[2])
    L = fm(art, "Item / liquid / status effect name mapping (%d entries)" % total,
           ["00-data/items.json", "00-data/liquids.json", "00-data/status.json"],
           ["WORLD.CRAFTING.001", "COMBAT.STATUS.001"],
           ["names", "chinese-name", "english-name", "translation", "mapping-table",
            "item", "liquid", "status"])
    L += [
        "",
        "## One line",
        "",
        "The display-name mapping for the three entity classes - items, liquids and status "
        "effects - which show only a name in the UI and have no block id; it is the only way "
        "back from a recipe table, a status icon or a liquid swatch to an id.",
        "",
        "## Rules / formulas",
        "",
        "- Key rule: `item.<id>.name` / `liquid.<id>.name` / `status.<id>.name`; the records "
        "behind the three tables are in 00-data.",
        "- Order: %d items (`00-data/items.json`) → %d liquids (`liquids.json`) → %d statuses "
        "(`status.json`), alphabetical by id inside each group."
        % (len(items), len(liqs), len(sts)),
        "- Three statuses are \"nameless\" entries: `none` / `invincible` / `dynamic`; they are "
        "not player-obtainable statuses and the bundle has no display name for them, so the "
        "table records a \"—\".",
        "- Item names are mostly substance names (copper, lead, silicon), liquid names are "
        "mostly liquid names (water, slag, oil), and status names are mostly adjectives (slow, "
        "overload, disarmed).",
        "",
        "## Numbers",
        "",
        "This section lists names only; hardness, cost, flammability, multipliers and similar "
        "numbers are in `00-data/items.json` / `liquids.json` / `status.json`, with conventions "
        "in COMBAT.STATUS.001.",
        "",
        "### Items",
        "",
    ]
    L += table(items, "item")
    L += ["", "### Liquids", ""]
    L += table(liqs, "liquid")
    L += ["", "### Status effects", ""]
    L += table(sts, "status")
    L += [
        "",
        "## Source anchors",
        "",
        "- `data/game/bundles/bundle_zh_CN.properties` (zh:N) and `bundle.properties` (en:N).",
        "- `00-data/items.json` (%d entries) / `liquids.json` (%d entries) / `status.json` "
        "(%d entries); %d entries across the three classes, %d of them with a Chinese name."
        % (len(items), len(liqs), len(sts), total, zh_hit),
        "- Generator script `knowledge/tools/gen_name_docs.py`.",
        "",
        "## Measurements and counter-examples",
        "",
        "- **Counter-example A** - `plastanium` is plastic-steel (塑钢), not plastic (塑料); "
        "`phase-fabric` is phase fabric (相织布), not phase cloth (相位布) - literal readings by "
        "English root go wrong.",
        "- **Counter-example B** - `pyratite` is officially sulfide (硫化物), which is not the "
        "same thing as pyrite (黄铁矿); the English names look alike but the Chinese strings are "
        "completely different.",
        "- **Counter-example C** - `surge-alloy` is officially surge alloy (巨浪合金), not surge "
        "alloy (电涌合金); `carbide` is carbide (碳化物) and `oxide` is oxide (氧化物), which "
        "belong to the same alloy family as `beryllium`, beryllium (铍), yet the naming is not "
        "uniform.",
        "- **Counter-example D** - the statuses `none` / `invincible` / `dynamic` have no "
        "Chinese name, so reverse-looking up an id from \"no status\" or \"invincible\" returns "
        "nothing; the correct ids are literally those three.",
        "- **Counter-example E** - the liquid `neoplasm` is tumor fluid (瘤液), `arkycite` is "
        "arkycite (芳油) and `gallium` is gallium liquid (镓液); of the three, only gallium "
        "keeps the liquid (液) suffix of an element name.",
        "",
        "## Common misconceptions",
        "",
        "- Assuming a status name is a block name: `overdrive` is both a status and the product "
        "of the block `overdrive-projector`; the two ids are named differently.",
        "- Assuming liquid names and item names share a table: `water` / `slag` are only in the "
        "liquids table and `sand` / `coal` only in the items table, so a name lookup across "
        "tables misses.",
        "- Assuming every status has a Chinese name: %d of the %d do not (the three special "
        "statuses)." % (len(sts) - st_zh, len(sts)),
        "",
        "## Related",
        "",
        "- WORLD.CRAFTING.001 (recipes and products)",
        "- WORLD.LIQUIDS.001 (liquid properties and conduits)",
        "- COMBAT.STATUS.001 (status multipliers and stacking)",
        "- WORLD.NAMES.001 / WORLD.NAMES.002 / WORLD.NAMES.003 (block names)",
        "- UNIT.NAMES.001 (unit names)",
    ]
    return art, "02-world/W16-name-items.md", L


def doc5():
    ids = [u["id"] for u in sorted(UNITS, key=lambda r: r["id"])]
    total = len(ids)
    zh_hit = sum(1 for i in ids if names("unit", i)[2])
    art = "UNIT.NAMES.001"
    L = fm(art, "Unit name table — English and Chinese names for all %d units "
           "(%d have an official Simplified Chinese name)" % (total, zh_hit),
           ["00-data/units.json"],
           ["UNIT.MOVE.001", "UNIT.PRODUCE.001"],
           ["names", "Chinese name", "English name", "translation", "lookup table", "unit"])
    L += [
        "",
        "## One line",
        "",
        "The Chinese names of the units against their ids. In the interface a unit shows only "
        "its name and never its id, while blueprints, logic and wave tables only know ids, so "
        "this table is the only bridge between the two.",
        "",
        "## Rules / formulas",
        "",
        "- The display-name key is `unit.<id>.name`; the numbers live in `00-data/units.json` "
        "(health, armor, speed, range and so on).",
        "- There are %d entries and %d have an official Simplified Chinese name; the %d that "
        "lack one are missile sub-units and a few internal placeholders."
        % (total, zh_hit, total - zh_hit),
        "- Units with no name (shown as \"—\" in the table): the missile types `*-missile`, "
        "`scathe-missile-*`, and the internal placeholders `block` / `dummy` / "
        "`turret-unit-build-tower`; in play they appear as ammunition or as build towers and "
        "never display a name.",
        "- Units are sorted alphabetically by id; tiers (T1–T5) and the production chain are in "
        "UNIT.PRODUCE.001 and are not part of this table.",
        "",
        "## Numbers",
        "",
        "This section lists names only, no numbers; for speed units, hitSize, armor and the "
        "rest see UNIT.MOVE.001 and `00-data/units.json`.",
        "",
    ]
    L += table(ids, "unit")
    L += [
        "",
        "## Source anchors",
        "",
        "- `data/game/bundles/bundle_zh_CN.properties` (zh:N) and `bundle.properties` (en:N).",
        "- `00-data/units.json`: %d unit records, with `id` mapping one-to-one onto the bundle "
        "key." % total,
        "- The generator script `knowledge/tools/gen_name_docs.py`.",
        "",
        "## Measurements and counter-examples",
        "",
        "- Counterexample 1: unit names are imagery, not function names — `dagger` (尖刀, a "
        "blade), `mace` (战锤, a warhammer), `fortress` (堡垒), `scepter` (权杖), `reign` "
        "(王座). Searching the Chinese names for \"dagger\" or \"hammer\" turns up nothing.",
        "- Counterexample 2: two naming strategies coexist in one table — the official Chinese "
        "name of `anthicus` is a semantic coinage (天灾, \"disaster\") rather than a "
        "transliteration (安提库斯), while `alpha` / `beta` / `gamma` are pure transliterations "
        "(阿尔法, 贝塔, 伽马).",
        "- Counterexample 3: `crawler` (爬虫) and `atrax` (毒蛛) are imagery in both languages, "
        "while `alpha` / `beta` / `gamma` keep the Greek letters as transliterations (阿尔法, "
        "贝塔, 伽马).",
        "- Counterexample 4: missile sub-units (such as `anthicus-missile`) have no display "
        "name, so searching the Chinese word for \"missile\" finds only the unit that fires "
        "them, `anthicus`, never the sub-unit itself.",
        "",
        "## Common misconceptions",
        "",
        "- Thinking unit names carry T1, T2: tier is not part of the name, and the official "
        "strings contain no level wording.",
        "- Thinking the English name translates straight into an id: `Fortress` → `fortress` "
        "works, but colon-bearing names such as `Core: Shard` appear only in the block table.",
        "- Thinking nameless units are a data gap: all %d have records and numbers, the "
        "language bundle simply does not display a name for them." % (total - zh_hit),
        "",
        "## Related",
        "",
        "- UNIT.MOVE.001 (speed units and terrain)",
        "- UNIT.PRODUCE.001 (production chain and unit cap)",
        "- UNIT.AI.001 (unit AI and commands)",
        "- UNIT.ABILITY.001 (the 16 Ability classes)",
        "- UNIT.PROGRESSION.001 (tiers and the wave table)",
        "- COMBAT.UNITWEAPON.001 (unit weapons and DPS)",
        "- WORLD.NAMES.001 / 002 / 003 / 004 (block and item names)",
    ]
    return art, "04-units/U06-name-units.md", L


def main(argv):
    check_only = "--check" in argv
    docs = [doc1(), doc2(), doc3(), doc4(), doc5()]
    bad = 0
    drift = 0
    for art, rel, lines in docs:
        text = "\n".join(lines).replace("`", chr(96)) + "\n"
        n = text.count("\n")
        flag = ""
        if n > MAX_LINES:
            bad += 1
            flag = "  <== 超过 %d 行" % MAX_LINES
        p = KB / rel
        if check_only:
            have = p.read_text(encoding="utf-8") if p.is_file() else ""
            if have != text:
                drift += 1
                flag += "  <== 与磁盘不一致"
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        print("%-14s %-42s %4d 行  %6d B%s" % (art, rel, n, len(text.encode("utf-8")), flag))
    bhit, bzh, btot = coverage("block", [b["id"] for b in BLOCKS])
    uhit, uzh, utot = coverage("unit", [u["id"] for u in UNITS])
    print("覆盖: blocks 中文名 %d/%d, units 中文名 %d/%d" % (bzh, btot, uzh, utot))
    if check_only and drift:
        print("%d 篇与磁盘不一致：跑一遍不带 --check 重新生成" % drift)
    return 1 if (bad or drift) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
