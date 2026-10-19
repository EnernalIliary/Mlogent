#!/usr/bin/env python
"""
_sweep_pack.py -- how common is the packed-config idiom in the real corpus,
and when it appears, what does the capacity check say?

Same shape as _sweep_values.py / _sweep_deadstores.py: exclude the
emulator blueprints by name, then count by file so we can eyeball the
worst offenders instead of trusting a mean.

    python tools/_sweep_pack.py [--limit N] [--verbose]
"""
from __future__ import annotations

import argparse
import collections
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "mindustry-blueprint" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import mlogir          # noqa: E402
import mlogpack        # noqa: E402
import msch            # noqa: E402

CORPUS = Path.home() / "AppData" / "Roaming" / "Mindustry" / "schematics"
EMULATOR_HINTS = ("mlogv32", "linux", "riscv", "risc-v", "vm")


def is_emulator(name: str) -> bool:
    low = name.lower()
    return any(h in low for h in EMULATOR_HINTS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    item_count = 22
    try:
        import json
        ids = json.loads((TOOLS / "item_ids.json").read_text("utf-8"))
        item_count = len(ids.get("items") or {})
    except Exception:
        pass

    files = sorted(CORPUS.glob("*.msch"))
    if args.limit:
        files = files[:args.limit]

    t0 = time.time()
    blocks = 0
    skipped_files = 0
    with_pack: list[tuple[str, str, int, int]] = []   # file, tile, sites, peels
    warnings: collections.Counter[str] = collections.Counter()
    by_file: collections.Counter[str] = collections.Counter()
    failures: list[str] = []

    for path in files:
        if is_emulator(path.name):
            skipped_files += 1
            continue
        try:
            sch = msch.parse_file(str(path))
        except Exception as exc:              # noqa: BLE001
            failures.append(f"{path.name}: {exc}")
            continue
        for tile in sch.logic_tiles():
            if tile.logic is None:
                continue
            blocks += 1
            prog = mlogir.parse(tile.logic.code.split("\n"))
            sites = mlogpack.find_pack_sites(prog)
            peels = mlogpack.find_bit_peels(prog)
            if not sites and not peels:
                continue
            with_pack.append((path.name, f"{tile.block} @({tile.x},{tile.y})",
                              len(sites), len(peels)))
            by_file[path.name] += len(sites)
            for site in sites:
                if site.capacity_bits is not None and item_count > site.capacity_bits:
                    warnings[f"low field 1e{site.low_exp} -> "
                             f"{site.capacity_bits} ids only"] += 1
                for _, _, text in site.overlaps:
                    warnings["idiv fields overlap (needs status==0 guard)"] += 1

    dt = time.time() - t0
    print(f"corpus          : {CORPUS}")
    print(f"files           : {len(files)}  (skipped emulator: {skipped_files})")
    print(f"blocks          : {blocks}")
    print(f"elapsed         : {dt:.1f}s  ({1000 * dt / max(blocks, 1):.1f} ms/block)")
    print(f"blocks w/ idiom : {len(with_pack)} "
          f"({100 * len(with_pack) / max(blocks, 1):.1f}%)")
    print(f"  pack sites    : {sum(w[2] for w in with_pack)}")
    print(f"  bit peels     : {sum(w[3] for w in with_pack)}")
    if warnings:
        print("warnings:")
        for text, n in warnings.most_common():
            print(f"  {n:6d}  {text}")
    if by_file:
        print("worst files:")
        for name, n in by_file.most_common(8):
            print(f"  {n:6d}  {name}")
    if args.verbose:
        print("sites:")
        for name, tile, s, p in with_pack:
            print(f"  {name} [{tile}]  sites={s} peels={p}")
    for f in failures:
        print(f"!! {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
