"""Full-corpus sweep: every check we own, over one blueprint folder.

    python tools/sweep_all.py <folder> --label mine --json out/sweep_mine.json

Outputs a per-block JSON row set plus a printed summary.  Giant generated
blueprints (pixel art, mlog emulators) dominate any average, so they are
skipped and *counted* rather than silently dropped:
  * any single logic block above --max-stmts  (default 5000)   -> skipped
  * any file above --max-bytes (default 2 MB)                  -> skipped
  * emulator-ish file names                                    -> skipped
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parent / "mindustry-blueprint" / "tools"
sys.path.insert(0, str(TOOLS))

import mlog as M          # noqa: E402
import mlogagent as AG    # noqa: E402
import mlogcross as CX    # noqa: E402

EMULATOR_HINTS = ("mlogv32", "mlogv64", "linux", "riscv", "risc-v", "vm")


def sweep(folder: pathlib.Path, max_stmts: int, max_bytes: int) -> dict:
    files = sorted(folder.rglob("*.msch"))
    t0 = time.time()
    rows: list[dict] = []
    bad: list[str] = []
    skipped_emul: list[str] = []
    skipped_big: list[str] = []
    cross_rows: list[dict] = []
    cross_errors: list[str] = []
    n_blocks = 0

    for path in files:
        rel = str(path.relative_to(folder))
        low = rel.lower()
        if any(h in low for h in EMULATOR_HINTS):
            skipped_emul.append(rel)
            continue
        try:
            if path.stat().st_size > max_bytes:
                skipped_big.append(f"{rel} (file > {max_bytes} B)")
                continue
            sch = M._load_schematic(str(path))
        except Exception as exc:                       # noqa: BLE001
            bad.append(f"{rel}: {type(exc).__name__}: {exc}")
            continue

        tiles = sch.logic_tiles()

        # cross-processor view is per schematic, not per block
        try:
            units = CX.units_from_schematic(sch)
            rep = CX.analyze_units(units)
            if rep.cross_reads:
                cross_rows.append({
                    "file": rel,
                    "units": len(units),
                    # cross_reads is a plain count, not a list -- len() on it
                    # raised TypeError, which the except below swallowed, so
                    # every schematic silently looked like "no cross reads".
                    "reads": rep.cross_reads,
                    "never_written": len(rep.never_written),
                    "always_null": len(rep.always_null),
                    "dead_writes": len(rep.dead_writes),
                })
        except Exception as exc:                       # noqa: BLE001
            cross_errors.append(f"{rel}: {type(exc).__name__}: {exc}")

        for t in tiles:
            code = t.logic.code or ""
            n_lines = code.count("\n") + 1 if code.strip() else 0
            if n_lines > max_stmts:
                skipped_big.append(f"{rel} [{t.block} @({t.x},{t.y})] {n_lines} stmts")
                continue
            lines = code.split("\n")
            links = [l.name for l in t.logic.links]
            try:
                m = AG._measure(lines, links)
            except Exception as exc:                   # noqa: BLE001
                bad.append(f"{rel} [{t.block} @({t.x},{t.y})]: {type(exc).__name__}: {exc}")
                continue
            n_blocks += 1
            find = [(f.sev, f.line, f.code, f.msg) for f in m["findings"]]
            by_code = collections.Counter(f[2] for f in find)
            rows.append({
                "file": rel,
                "cat": rel.split(os.sep)[0] if os.sep in rel else "",
                "block": t.block,
                "x": t.x, "y": t.y,
                "stmts": m["stmts"],
                "errs": m["errs"], "warns": m["warns"],
                "dead": m["dead"],
                "reported": m["reported"], "hidden": m["hidden"],
                "branches": m["branches"], "nulls": m["nulls"],
                "rounds": m["rounds"], "stable": m["stable"],
                "packs": m["packs"],
                "build": m["build"],
                "unknown": m["unknown"],
                "findings": find,
                "by_code": dict(by_code),
                "labels": list(sch.labels or []),
                "name": sch.name or "",
                "texts": len(sch.message_blocks()) if hasattr(sch, "message_blocks") else 0,
            })

    el = time.time() - t0
    return {
        "label": folder.name,
        "folder": str(folder),
        "files": len(files),
        "files_skipped_emulator": skipped_emul,
        "files_skipped_big": skipped_big,
        "failed": bad,
        "blocks": n_blocks,
        "seconds": round(el, 1),
        "rows": rows,
        "cross": cross_rows,
        "cross_errors": cross_errors,
    }


def summarise(data: dict, top: int) -> str:
    rows = data["rows"]
    n = len(rows) or 1
    out: list[str] = []
    w = out.append
    stmts = sum(r["stmts"] for r in rows)
    w(f"== {data['label']}  ({data['folder']})")
    w(f"   files {data['files']}   blocks {len(rows)}   statements {stmts:,}"
      f"   {data['seconds']}s")
    w(f"   skipped: {len(data['files_skipped_emulator'])} emulator file(s),"
      f" {len(data['files_skipped_big'])} oversized (file or block)")
    w(f"   failed to parse: {len(data['failed'])}")

    sev = collections.Counter()
    code = collections.Counter()
    for r in rows:
        for s, _ln, c, _m in r["findings"]:
            sev[s] += 1
            code[(s, c)] += 1
    w("")
    w("   findings by severity: " + ", ".join(f"{k} {v}" for k, v in sev.most_common()))
    w(f"   blocks with 0 ERR/SUSPECT: {sum(1 for r in rows if r['errs'] == 0)}"
      f" ({sum(1 for r in rows if r['errs'] == 0) * 100 / n:.1f}%)")
    for (s, c), v in code.most_common(top):
        w(f"     {s:<8} {c:<28} {v}")

    dead = sum(r["reported"] for r in rows)
    w("")
    w(f"   dead stores reported {dead} ({dead / n:.3f}/block),"
      f" hidden {sum(r['hidden'] for r in rows)}")
    w(f"   dead code {sum(r['dead'] for r in rows)}   "
      f"const branches {sum(r['branches'] for r in rows)}   "
      f"provable nulls {sum(r['nulls'] for r in rows)}   "
      f"pack sites {sum(r['packs'] for r in rows)}")
    gates = collections.Counter(r["build"] for r in rows if r["build"])
    if gates:
        w("   build gates: " + ", ".join(f">={k}: {v} block(s)" for k, v in sorted(gates.items())))
    unk = collections.Counter(u for r in rows for u in r["unknown"])
    if unk:
        w("   unknown mnemonics: " + ", ".join(f"{k}×{v}" for k, v in unk.most_common(8)))

    w("")
    w("   worst files by ERR/SUSPECT:")
    per_file = collections.Counter()
    for r in rows:
        per_file[r["file"]] += r["errs"]
    for f, v in per_file.most_common(top):
        if v:
            w(f"     {v:>4}  {f}")
    w("   worst files by dead stores:")
    per_file = collections.Counter()
    for r in rows:
        per_file[r["file"]] += r["reported"]
    for f, v in per_file.most_common(top):
        if v:
            w(f"     {v:>4}  {f}")
    if data["cross"]:
        w("")
        w(f"   cross-processor: {len(data['cross'])} schematic(s)")
        for c in sorted(data["cross"], key=lambda x: -x["reads"])[:top]:
            w(f"     {c['reads']:>3} read(s)  never-written {c['never_written']}"
              f"  dead-write {c['dead_writes']}  {c['file']}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--label", help="corpus name in the report")
    ap.add_argument("--json")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--max-stmts", type=int, default=5000)
    ap.add_argument("--max-bytes", type=int, default=2_000_000)
    args = ap.parse_args()

    folder = pathlib.Path(args.folder)
    data = sweep(folder, args.max_stmts, args.max_bytes)
    if args.label:
        data["label"] = args.label
    print(summarise(data, args.top))
    if data["failed"]:
        print("\n   parse failures:")
        for b in data["failed"][:10]:
            print("     " + b)
    if data["files_skipped_big"]:
        print(f"\n   oversized skipped ({len(data['files_skipped_big'])}), first 5:")
        for b in data["files_skipped_big"][:5]:
            print("     " + b)
    if args.json:
        p = pathlib.Path(args.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n   json -> {p}  ({p.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
