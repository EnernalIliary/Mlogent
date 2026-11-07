#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Three-way comparison of the Mindustry game-fact sources used by MBO.

    gamedata.json          -- fresh v160.7 dump from the server jar (this spike)
    data/game/blocks.json  -- legacy v160.7 dump produced by out/_dump_game.py
    docs/游戏速查/方块配方.md -- hand/script generated v160.7 recipe cheat sheet

Every number printed here is derived at runtime from the three files -- run

    python MBO/spikes/data/compare_data.py

and paste the output into MBO/docs/11-游戏数据层.md.  Writes compare_report.json.
"""

from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GAMEDATA = os.path.join(HERE, "gamedata.json")
LEGACY = os.path.join(ROOT, "data", "game", "blocks.json")
MD = os.path.join(ROOT, "docs", "游戏速查", "方块配方.md")
REPORT = os.path.join(HERE, "compare_report.json")

ITEM_RE = re.compile(r"([a-z0-9][a-z0-9\-]*)\s*[×xX*]\s*([0-9]+(?:\.[0-9]+)?)")
ELEC_RE = re.compile(r"电\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*s")
SIZE_RE = re.compile(r"(\d+)\s*[×x]\s*(\d+)")
POWER_CELL_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*/\s*s")


def pct(a: int, b: int) -> float:
    return round(100.0 * a / b, 1) if b else 0.0


# ------------------------------------------------------------------ markdown


def parse_markdown() -> list[dict]:
    rows = []
    with open(MD, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith("|") or set(line) <= set("|-: "):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 5 or cells[0] in ("方块",):
                continue
            raw_name = cells[0]
            name = re.split(r"[（(]", raw_name)[0].strip()
            m = SIZE_RE.search(cells[1])
            size = int(m.group(1)) if m else None
            power = None
            if cells[2] not in ("—", "-", ""):
                pm = POWER_CELL_RE.search(cells[2])
                power = float(pm.group(1)) if pm else None
            inputs = [{"name": n, "amount": float(a)} for n, a in ITEM_RE.findall(cells[3])]
            inputs_power = [float(x) for x in ELEC_RE.findall(cells[3])]
            outputs = [{"name": n, "amount": float(a)} for n, a in ITEM_RE.findall(cells[4])]
            rows.append({
                "raw": raw_name, "name": name, "size": size,
                "powerCell": power,
                "inputItems": inputs,
                "inputPower": inputs_power,
                "outputItems": outputs,
                "outputRaw": cells[4],
            })
    return rows


# ------------------------------------------------------------------ helpers


def stacks(names_amounts) -> dict[str, float]:
    out: dict[str, float] = {}
    for s in names_amounts:
        out[s["name"]] = round(out.get(s["name"], 0.0) + float(s["amount"]), 4)
    return out


def legacy_stacks(lst) -> dict[str, float]:
    out: dict[str, float] = {}
    for s in lst or []:
        nm = s.get("name") or s.get("item") or s.get("liquid")
        if not nm:
            continue
        out[nm] = round(out.get(nm, 0.0) + float(s.get("amount", 0)), 4)
    return out


def recipe_inputs(block: dict) -> dict[str, float]:
    r = block.get("recipe")
    if not r:
        return {}
    total: dict[str, float] = {}
    for c in r["inputs"]:
        for s in c.get("items", []) + c.get("liquids", []):
            total[s["name"]] = round(total.get(s["name"], 0.0) + float(s["amount"]), 4)
    return total


def recipe_outputs(block: dict) -> dict[str, float]:
    r = block.get("recipe")
    if not r:
        return {}
    total: dict[str, float] = {}
    for s in r.get("outputItems", []) + r.get("outputLiquids", []):
        total[s["name"]] = round(total.get(s["name"], 0.0) + float(s["amount"]), 4)
    for s in r.get("results", []):
        total[s["name"]] = round(total.get(s["name"], 0.0) + float(s["amount"]), 4)
    return total


def close(a: float, b: float, rel: float = 0.02, abs_: float = 0.02) -> bool:
    return abs(a - b) <= max(abs_, rel * max(abs(a), abs(b)))


# ------------------------------------------------------------------ main


def main() -> int:
    with open(GAMEDATA, encoding="utf-8") as fh:
        gd = json.load(fh)
    with open(LEGACY, encoding="utf-8") as fh:
        legacy = json.load(fh)
    md_rows = parse_markdown()

    gblocks = {b["name"]: b for b in gd["blocks"]}
    lblocks = {}
    for i, b in enumerate(legacy):
        lblocks[b["name"]] = dict(b, legacyIndex=i)

    report: dict = {"inputs": {"gamedata": os.path.relpath(GAMEDATA, ROOT),
                               "legacy": os.path.relpath(LEGACY, ROOT),
                               "markdown": os.path.relpath(MD, ROOT)}}

    # ---------------- 1. gamedata vs legacy blocks.json -------------------
    both = sorted(set(gblocks) & set(lblocks))
    g_only = sorted(set(gblocks) - set(lblocks))
    l_only = sorted(set(lblocks) - set(gblocks))

    def cmp_field(fn) -> int:
        return sum(1 for n in both if fn(gblocks[n], lblocks[n]))

    size_eq = cmp_field(lambda g, l: g["size"] == l.get("size"))
    cat_eq = cmp_field(lambda g, l: g["category"] == l.get("category"))
    power_eq = cmp_field(lambda g, l: bool(g["power"]["consumesPower"]) == bool(l.get("hasPower")))
    req_eq = cmp_field(lambda g, l: stacks(g["requirements"]) == legacy_stacks(l.get("requirements")))
    legacy_with_io = sum(1 for b in legacy if b.get("consumers") or b.get("outputs"))
    new_with_io = sum(1 for b in gd["blocks"] if b["recipe"] and (b["recipe"]["inputs"] or
                                                                  b["recipe"]["outputItems"] or
                                                                  b["recipe"].get("results")))
    legacy_craft_neg1 = sum(1 for b in legacy if float(b.get("craftTime", -1)) == -1.0)
    legacy_has_power = sum(1 for b in legacy if b.get("hasPower"))
    new_consumes = sum(1 for b in gd["blocks"] if b["power"]["consumesPower"])

    report["gamedata_vs_legacy"] = {
        "legacyCount": len(legacy), "gamedataCount": len(gd["blocks"]),
        "matched": len(both), "onlyGamedata": g_only, "onlyLegacy": l_only,
        "sizeEqual": size_eq, "sizeRate": pct(size_eq, len(both)),
        "categoryEqual": cat_eq, "categoryRate": pct(cat_eq, len(both)),
        "hasPowerEqual": power_eq, "hasPowerRate": pct(power_eq, len(both)),
        "requirementsEqual": req_eq, "requirementsRate": pct(req_eq, len(both)),
        "legacyCraftTimeMinusOne": legacy_craft_neg1,
        "legacyBlocksWithConsumersOrOutputs": legacy_with_io,
        "gamedataBlocksWithRecipeIO": new_with_io,
        "legacyHasPower": legacy_has_power,
        "gamedataActuallyConsumesPower": new_consumes,
        "idIsListIndexInLegacy": all(b.get("legacyIndex") == b.get("id") for b in lblocks.values()),
        "contentIdMatchesPosition": sum(1 for b in gd["blocks"] if b["id"] == gd["blocks"].index(b)),
    }

    # ---------------- 2. gamedata vs markdown -----------------------------
    md_by = {r["name"]: r for r in md_rows}
    md_names = set(md_by)
    md_both = sorted(md_names & set(gblocks))
    md_only = sorted(md_names - set(gblocks))
    gd_only_md = sorted(set(gblocks) - md_names)

    md_size_eq = sum(1 for n in md_both if md_by[n]["size"] == gblocks[n]["size"])
    md_power_rows = [n for n in md_both if md_by[n]["powerCell"] is not None]
    def power_ok(n, mult):
        g = gblocks[n]
        u = g["power"]["usage"]
        if md_by[n]["powerCell"] is None:
            return False
        return u is not None and close(md_by[n]["powerCell"], float(u) * mult)
    md_power_tick = sum(1 for n in md_power_rows if power_ok(n, 1.0))
    md_power_sec = sum(1 for n in md_power_rows if power_ok(n, 60.0))
    md_power_sec_literal = sum(1 for n in md_power_rows
                               if power_ok(n, 60.0) and not power_ok(n, 1.0))

    md_in_rows = [n for n in md_both if md_by[n]["inputItems"]]
    md_in_eq = sum(1 for n in md_in_rows
                   if stacks(md_by[n]["inputItems"]) == recipe_inputs(gblocks[n]))
    md_out_rows = [n for n in md_both if md_by[n]["outputItems"]]
    md_out_eq = sum(1 for n in md_out_rows
                    if stacks(md_by[n]["outputItems"]) == recipe_outputs(gblocks[n]))

    # per-output ratio: markdown says amount per craft; gamedata outputItems amount per craft
    ratios = []
    for n in md_out_rows:
        mo = stacks(md_by[n]["outputItems"])
        go = recipe_outputs(gblocks[n])
        if set(mo) == set(go) and go:
            for k in mo:
                if go[k]:
                    ratios.append(mo[k] / go[k])
    ratio_hist: dict[str, int] = {}
    for r in ratios:
        ratio_hist[f"{r:.1f}"] = ratio_hist.get(f"{r:.1f}", 0) + 1

    # rows the markdown shows as "nothing produced" but the game does produce
    md_dash_rows = [n for n in md_both if not md_by[n]["outputItems"]]
    md_dash_but_produces = [n for n in md_dash_rows if recipe_outputs(gblocks[n])]

    report["gamedata_vs_markdown"] = {
        "markdownRows": len(md_rows), "markdownUniqueNames": len(md_names),
        "matched": len(md_both), "onlyMarkdown": md_only,
        "blocksNotInMarkdown": len(gd_only_md),
        "sizeEqual": md_size_eq, "sizeRate": pct(md_size_eq, len(md_both)),
        "powerRowsWithNumber": len(md_power_rows),
        "powerEqualAsPerTick": md_power_tick,
        "powerEqualAsPerSecond": md_power_sec,
        "powerMatchesOnlyWithX60": md_power_sec_literal,
        "powerDeltaFactor": 60,
        "inputRowsWithItems": len(md_in_rows), "inputItemsEqual": md_in_eq,
        "inputRate": pct(md_in_eq, len(md_in_rows)),
        "outputRowsWithItems": len(md_out_rows), "outputItemsEqual": md_out_eq,
        "outputRate": pct(md_out_eq, len(md_out_rows)),
        "outputAmountRatioHistogram": dict(sorted(ratio_hist.items())),
        "mdRowsShowingNoOutput": len(md_dash_rows),
        "mdRowsShowingNoOutputButGameProduces": len(md_dash_but_produces),
        "mdNoOutputExamples": md_dash_but_produces[:15],
    }

    # ---------------- 3. coverage of the new dump -------------------------
    cov = gd.get("meta", {}).get("coverage") or {}
    blocks = gd["blocks"]
    report["gamedata_coverage"] = {
        "blocks": len(blocks),
        "withRealFormulaRecipe": cov.get("fullRecipe"),
        "withCraftTime": cov.get("withCraftTime"),
        "withInputsOnly": cov.get("withInputs"),
        "withOutputsOnly": cov.get("withOutputs"),
        "powerConsumers": cov.get("consumesPower"),
        "powerGenerators": cov.get("powerProductionValue"),
        "drills": cov.get("drills"),
        "conveyorsAndDucts": cov.get("conveyors"),
        "conveyorsWithItemsPerSecond": cov.get("conveyorsWithRate"),
        "rotatable": cov.get("rotatable"),
        "withRequirements": cov.get("withRequirements"),
        "oreBlocks": len(gd["environment"]["oreBlocks"]),
        "liquidBlocks": len(gd["environment"]["liquidBlocks"]),
        "familyCounts": cov.get("familyCounts"),
        "items": len(gd["items"]), "liquids": len(gd["liquids"]),
    }

    # ---------------- 4. sanity: field presence per block -----------------
    field_presence = {}
    for b in blocks:
        for k in b["raw"]:
            field_presence[k] = field_presence.get(k, 0) + 1
    report["topFields"] = dict(sorted(field_presence.items(), key=lambda kv: -kv[1])[:25])

    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"\nwrote {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
