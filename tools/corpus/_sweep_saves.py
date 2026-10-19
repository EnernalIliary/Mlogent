#!/usr/bin/env python3
"""Sweep every .msav in the save folder through map_logic and report the hit rate.

Parsing one save is pure CPU work with no shared state, so this runs one file
per process across the machine (see ``parallel.py`` for how the worker count is
chosen).  Was 280 s serially; check the tail line for what it costs now.

    python tools/_sweep_saves.py                 # all cores it can afford
    python tools/_sweep_saves.py --workers 4     # or a fixed number
    python tools/_sweep_saves.py --serial
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mindustry-blueprint" / "tools"))

SAVES = Path.home() / "AppData/Roaming/Mindustry/saves"
OUT = Path(__file__).resolve().parents[2] / "out" / "saves_scan.json"


def scan_one(path_str: str) -> dict:
    """Worker: parse one save, return counts only.

    Source code must not come back over the pipe -- 1421 saves hold ~9.6M
    lines, and shipping that through pickling would cost more than the parse.
    """
    import map_logic as ML

    p = Path(path_str)
    try:
        info = ML.read_save(p)
    except Exception as exc:
        try:
            import struct
            import zlib

            raw = zlib.decompress(p.read_bytes())
            ver = struct.unpack_from(">i", raw, 4)[0]
        except Exception:
            ver = -1
        return {"ok": False, "file": p.name, "version": ver,
                "error": f"{type(exc).__name__}: {str(exc)[:60]}"}

    logic = info["logic"]
    return {
        "ok": True,
        "file": p.name,
        "version": info["version"],
        "size": f"{info['width']}x{info['height']}",
        "processors": len(logic),
        "broken": sum(1 for t in logic if t["code"] is None),
        "lines": sum(len((t["code"] or "").splitlines()) for t in logic),
    }


def main(argv: list[str]) -> int:
    import argparse

    import parallel

    ap = argparse.ArgumentParser(description="scan every save for logic processors")
    ap.add_argument("--workers", type=int, default=None, help="force a worker count")
    ap.add_argument("--serial", action="store_true", help="no processes")
    ap.add_argument("--saves", default=str(SAVES))
    ap.add_argument("--json", default=str(OUT))
    a = ap.parse_args(argv)

    folder = Path(a.saves)
    files = sorted(folder.glob("*.msav"))
    print(f"scanning {len(files)} save(s) in {folder}", flush=True)
    t0 = time.time()
    results = parallel.run(
        scan_one, [str(p) for p in files],
        workers=1 if a.serial else a.workers,
        label="scan saves",
    )

    by_ver_ok: Counter = Counter()
    by_ver_bad: Counter = Counter()
    errs: Counter = Counter()
    rows = []
    for r in results:
        if not r["ok"]:
            by_ver_bad[r["version"]] += 1
            errs[r["error"]] += 1
            continue
        by_ver_ok[r["version"]] += 1
        if r["processors"] or r["broken"]:
            rows.append({k: r[k] for k in ("file", "version", "size", "processors", "broken", "lines")})

    rows.sort(key=lambda r: (-r["processors"], -r["lines"]))
    out = Path(a.json)
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\ndone in {time.time() - t0:.0f}s")
    print(f"parsed ok : {sum(by_ver_ok.values())}  by version {dict(sorted(by_ver_ok.items()))}")
    print(f"failed    : {sum(by_ver_bad.values())}  by version {dict(sorted(by_ver_bad.items()))}")
    if errs:
        print("failure kinds:")
        for k, v in errs.most_common(6):
            print(f"  {v:5d}  {k}")
    print(f"\n{len(rows)} save(s) contain logic, "
          f"{sum(r['processors'] for r in rows)} processor(s), "
          f"{sum(r['lines'] for r in rows)} line(s) of code")
    for r in rows[:15]:
        print(f"  {r['processors']:4d} proc {r['lines']:7d} line  v{r['version']} "
              f"{r['size']:>9}  {r['file']}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
