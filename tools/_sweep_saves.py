#!/usr/bin/env python3
"""Sweep every .msav in the save folder through map_logic and report the hit rate."""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mindustry-blueprint" / "tools"))
import map_logic as ML  # noqa: E402

SAVES = Path.home() / "AppData/Roaming/Mindustry/saves"
OUT = Path(__file__).resolve().parents[1] / "out" / "saves_scan.json"


def main() -> int:
    files = sorted(SAVES.glob("*.msav"))
    print(f"scanning {len(files)} save(s) in {SAVES}", flush=True)
    rows = []
    by_ver_ok: Counter = Counter()
    by_ver_bad: Counter = Counter()
    errs: Counter = Counter()
    t0 = time.time()
    for i, p in enumerate(files, 1):
        try:
            info = ML.read_save(p)
        except Exception as e:
            try:
                import zlib
                import struct
                raw = zlib.decompress(p.read_bytes())
                ver = struct.unpack_from(">i", raw, 4)[0]
            except Exception:
                ver = -1
            by_ver_bad[ver] += 1
            errs[f"{type(e).__name__}: {str(e)[:60]}"] += 1
            continue
        by_ver_ok[info["version"]] += 1
        n = len(info["logic"])
        broken = sum(1 for t in info["logic"] if t["code"] is None)
        if n or broken:
            rows.append({
                "file": p.name,
                "version": info["version"],
                "size": f"{info['width']}x{info['height']}",
                "processors": n,
                "broken": broken,
                "lines": sum(len((t["code"] or "").splitlines()) for t in info["logic"]),
            })
        if i % 100 == 0:
            print(f"  {i}/{len(files)}  {time.time() - t0:.0f}s  "
                  f"ok={sum(by_ver_ok.values())} bad={sum(by_ver_bad.values())}", flush=True)

    rows.sort(key=lambda r: (-r["processors"], -r["lines"]))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

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
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
