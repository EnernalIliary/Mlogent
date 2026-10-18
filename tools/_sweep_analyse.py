"""Run the static checks over every processor in every save.

`map` tells you what is in a save; this tells you what is *wrong* in all of
them.  Aggregates by rule so one code-level bug in my own checker shows up as a
spike instead of hiding in 105k individual reports.

Identical programs are analysed once.  The hash covers the source text only --
**not** the link list -- because the same 60-line program pasted onto forty
processors (or kept in a save plus its ``-backup`` twin) is one bug, not forty.
The first copy is the one that gets reported; every later copy only bumps a
count, so per-save rankings are not inflated by backups.

Parsing and checking one save share nothing with the next, so each file is a
worker task (see ``parallel.py`` for how the worker count is picked -- the
answer is bounded by free memory, because one save here holds 6600 processors).
Workers dedupe inside their own save; the parent dedupes across saves, which is
why the parent, not the worker, decides what a "first sighting" is.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mindustry-blueprint" / "tools"))

SAVES = Path(r"C:\Users\lliary\AppData\Roaming\Mindustry\saves")
OUT = ROOT / "out"


def code_hash(code: str) -> str:
    """Stable digest of the program text, ignoring links and line endings."""
    norm = "\n".join(line.rstrip() for line in code.replace("\r\n", "\n").split("\n"))
    return hashlib.sha1(norm.strip("\n").encode("utf-8")).hexdigest()


_NUM = re.compile(r"\b\d+(?:\.\d+)?\b")
_Q = re.compile(r"`[^`]*`")


def finding_class(msg: str) -> str:
    """Normalise a finding message into a class name.

    `Finding.code` holds the offending *source line*, so aggregating on it
    gives one bucket per statement -- 5000+ classes for 105k statements, which
    tells you nothing.  The message is the stable part: strip the numbers and
    the backticked names and what is left is the rule that fired.
    """
    head = msg.split(";")[0].split(" -- ")[0]
    head = _Q.sub("`X`", head)
    head = _NUM.sub("N", head)
    return head.strip()


def analyse_one(path_str: str) -> dict:
    """Worker: one save -> its distinct programs plus every finding they raise."""
    import map_logic as ML
    import mlogcheck as C

    path = Path(path_str)
    try:
        info = ML.read_save(path)
    except Exception as exc:  # noqa: BLE001 - report, don't die
        return {"file": path.name, "error": f"{type(exc).__name__}: {exc}",
                "processors": 0, "programs": []}

    procs = 0
    local: dict[str, dict] = {}
    order: list[str] = []
    for tile in info["logic"]:
        code = tile["code"]
        if not code.strip():
            continue
        procs += 1
        h = code_hash(code)
        if h in local:
            local[h]["copies"] += 1
            continue
        labels = [l["name"] for l in tile["links"]]
        try:
            found = C.analyse(code.splitlines(), labels)
        except Exception as exc:  # noqa: BLE001
            return {"file": path.name,
                    "error": f"{path.name}:{tile['x']},{tile['y']}: {type(exc).__name__}: {exc}",
                    "processors": procs, "programs": []}
        local[h] = {
            "hash": h,
            "x": tile["x"], "y": tile["y"], "block": tile["block"],
            "stmts": len(code.splitlines()),
            "copies": 1,
            "findings": [[f.sev, finding_class(f.msg), f.line, f.code, f.msg] for f in found],
        }
        order.append(h)
    return {"file": path.name, "error": None, "processors": procs,
            "programs": [local[h] for h in order]}


def main(argv: list[str]) -> int:
    import argparse

    import parallel

    ap = argparse.ArgumentParser(description="check every processor in every save")
    ap.add_argument("--save-dir", default=str(SAVES))
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--serial", action="store_true")
    ap.add_argument("--json", default=str(OUT / "saves_analyse.json"))
    a = ap.parse_args(argv)

    files = sorted(Path(a.save_dir).glob("*.msav"))
    started = time.time()
    results = parallel.run(
        analyse_one, [str(p) for p in files],
        workers=1 if a.serial else a.workers,
        label="analyse saves",
    )

    codes: Counter = Counter()
    severity: Counter = Counter()
    per_save: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    worst: list[dict] = []
    bad_files: list[tuple[str, str]] = []
    seen: dict[str, dict] = {}
    dup_counter: Counter = Counter()
    total_procs = 0

    for res in results:
        if res["error"]:
            bad_files.append((res["file"], res["error"]))
        total_procs += res["processors"]
        bucket = per_save[res["file"]]
        bucket[0] += res["processors"]
        for prog in res["programs"]:
            h = prog["hash"]
            if h in seen:
                dup_counter[h] += prog["copies"]      # every copy here is a duplicate
                continue
            dup_counter[h] += prog["copies"] - 1      # the first copy is the one analysed
            seen[h] = {k: prog[k] for k in ("x", "y", "block", "stmts")} | {"save": res["file"]}
            for sev, cls, line, code, msg in prog["findings"]:
                codes[(sev, cls)] += 1
                severity[sev] += 1
                if sev in ("ERR", "SUSPECT"):
                    bucket[1] += 1
                    if bucket[1] <= 3:
                        worst.append({"save": res["file"], "x": prog["x"], "y": prog["y"],
                                      "block": prog["block"], "line": line,
                                      "code": code, "msg": msg, "stmts": prog["stmts"]})
                else:
                    bucket[2] += 1

    dups = sum(dup_counter.values())
    print(f"\ndone in {time.time() - started:.0f}s")
    print(f"saves read      : {len(files) - len([b for b in bad_files if b[0].endswith('.msav')])}")
    print(f"processors      : {total_procs}")
    print(f"distinct programs: {len(seen)}")
    print(f"duplicate copies : {dups} (skipped, {total_procs and 100.0 * dups / total_procs:.1f}% of all)")
    print(f"findings        : {sum(severity.values())}  {dict(severity)}")
    print(f"hard (ERR+SUSP) : {sum(v for k, v in codes.items() if k[0] in ('ERR', 'SUSPECT'))}")

    print("\nby rule (per distinct program):")
    for (sev, code), count in codes.most_common(40):
        print(f"  {count:>7}  {sev:<7} {code}")

    print("\nmost copied programs:")
    for h, extra in dup_counter.most_common(10):
        head = seen[h]
        print(f"  {extra + 1:>5}x  {head['stmts']:>5} stmt  "
              f"{head['save']}:{head['x']},{head['y']}")

    if bad_files:
        print(f"\nunreadable: {len(bad_files)}")
        for name, why in bad_files[:10]:
            print(f"  {name}: {why}")

    print("\nworst saves by hard findings:")
    for name, (procs, errs, warns) in sorted(per_save.items(), key=lambda kv: -kv[1][1])[:15]:
        if errs:
            print(f"  {errs:>5} err  {procs:>5} proc  {warns:>5} warn  {name}")

    payload = {
        "saves": len(files),
        "processors": total_procs,
        "distinct": len(seen),
        "duplicates": dups,
        "severity": dict(severity),
        "codes": {f"{k[0]}|{k[1]}": v for k, v in codes.items()},
        "per_save": {k: v for k, v in per_save.items()},
        "examples": worst,
        "unreadable": bad_files,
        "most_copied": [dict(seen[h], copies=extra + 1) for h, extra in dup_counter.most_common(50)],
    }
    out = Path(a.json)
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
