# -*- coding: utf-8 -*-
"""Measure the read-only-loop rule on the whole corpus.

Two severities, because they answer different questions:

* ``ERR  this loop deadlocks itself`` -- the body cannot change anything the
  guard reads (no ``ucontrol``, no ``ubind <type>``), so once the guard holds
  it holds forever. Provable from the text alone.
* ``WARN this loop only leaves once a unit of another controller is bound`` --
  the body does ``ubind <type>``, so each pass walks the round-robin. It ends
  as soon as a unit this processor does not control comes up; with a single
  such unit on the map it spins forever. Needs a runtime fact, hence WARN.

Skips emulator blueprints and oversized art blocks (both make ``analyse`` slow
for reasons that have nothing to do with this rule).
"""
import os
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "mindustry-blueprint" / "tools"))

import mlogcheck as C  # noqa: E402
import msch  # noqa: E402

CORPUS = Path(os.environ.get("MLOG_CORPUS")
              or Path.home() / "AppData" / "Roaming" / "Mindustry" / "schematics")
EMULATOR = ("mlogv32", "linux", "riscv", "risc-v", "vm")
MAX_STMTS = 5000


def main() -> int:
    files = sorted(CORPUS.glob("*.msch"))
    blocks = skipped_files = skipped_blocks = 0
    err_blocks = warn_blocks = 0
    err_sites = warn_sites = 0
    err_files, warn_files = Counter(), Counter()
    t0 = time.time()

    for p in files:
        if any(h in p.name.lower() for h in EMULATOR):
            skipped_files += 1
            continue
        try:
            sch = msch.parse_file(str(p))
        except Exception:                                  # noqa: BLE001
            skipped_files += 1
            continue
        for tile in sch.logic_tiles():
            code = tile.logic.code
            if len(code) > MAX_STMTS:
                skipped_blocks += 1
                continue
            blocks += 1
            try:
                found = C.analyse(code.split("\n"))
            except Exception as exc:                       # noqa: BLE001
                print(f"!! {p.name}: {exc}")
                continue
            e = sum(1 for x in found if x.msg.startswith("this loop deadlocks"))
            w = sum(1 for x in found if x.msg.startswith("this loop only leaves"))
            err_sites += e
            warn_sites += w
            if e:
                err_blocks += 1
                err_files[p.name] += e
            if w:
                warn_blocks += 1
                warn_files[p.name] += w

    dt = time.time() - t0
    print(f"files        : {len(files)} ({skipped_files} skipped)")
    print(f"blocks       : {blocks} ({skipped_blocks} too large)")
    print(f"deadlock ERR : {err_sites} site(s) in {err_blocks} block(s) "
          f"({err_blocks / max(blocks, 1):.4f}/block)")
    print(f"ubind    WARN: {warn_sites} site(s) in {warn_blocks} block(s) "
          f"({warn_blocks / max(blocks, 1):.4f}/block)")
    print(f"took         : {dt:.1f}s ({1000 * dt / max(blocks, 1):.0f} ms/block)")
    for title, counter in (("deadlock ERR", err_files), ("ubind WARN", warn_files)):
        if not counter:
            continue
        print(f"{title} by file:")
        for name, n in counter.most_common(12):
            print(f"  {n:3d}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
