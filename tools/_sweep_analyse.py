"""Run the static checks over every processor in every save.

`map` tells you what is in a save; this tells you what is *wrong* in all of
them.  Aggregates by finding code so one code-level bug in my own checker
shows up as a spike instead of hiding in 105k individual reports.

Identical programs are analysed once.  The hash covers the source text only --
**not** the link list -- because the same 60-line program pasted onto forty
processors (or kept in a save plus its ``-backup`` twin) is one bug, not forty.
The first copy is the one that gets reported; every later copy only bumps a
count, so per-save rankings are not inflated by backups.
"""
import hashlib
import re
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mindustry-blueprint" / "tools"))
import mlogcheck as C  # noqa: E402
import map_logic as M  # noqa: E402

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


def main() -> int:
    files = sorted(SAVES.glob("*.msav"))
    codes = Counter()
    severity = Counter()
    per_save = defaultdict(lambda: [0, 0, 0])  # procs, errs, warns
    worst = []
    started = time.time()
    bad_files = []
    total_procs = 0

    seen: dict[str, dict] = {}          # hash -> first sighting
    dup_counter: Counter = Counter()     # hash -> extra copies

    for n, path in enumerate(files, 1):
        try:
            info = M.read_save(path)
        except Exception as exc:  # noqa: BLE001 - report, don't die
            bad_files.append((path.name, f"{type(exc).__name__}: {exc}"))
            continue
        bucket = per_save[path.name]
        for tile in info["logic"]:
            code = tile["code"]
            if not code.strip():
                continue
            total_procs += 1
            bucket[0] += 1
            h = code_hash(code)
            if h in seen:
                dup_counter[h] += 1
                continue
            seen[h] = {
                "save": path.name, "x": tile["x"], "y": tile["y"],
                "block": tile["block"], "stmts": len(code.splitlines()),
            }
            labels = [l["name"] for l in tile["links"]]
            try:
                found = C.analyse(code.splitlines(), labels)
            except Exception as exc:  # noqa: BLE001
                bad_files.append((f"{path.name}:{tile['x']},{tile['y']}",
                                  f"{type(exc).__name__}: {exc}"))
                continue
            for f in found:
                codes[(f.sev, finding_class(f.msg))] += 1
                severity[f.sev] += 1
                if f.sev in ("ERR", "SUSPECT"):
                    bucket[1] += 1
                    if bucket[1] <= 3:
                        worst.append({
                            "save": path.name, "x": tile["x"], "y": tile["y"],
                            "block": tile["block"],
                            "line": f.line, "code": f.code, "msg": f.msg,
                            "stmts": len(code.splitlines()),
                        })
                else:
                    bucket[2] += 1
        if n % 100 == 0:
            print(f"  {n}/{len(files)}  {time.time()-started:.0f}s  "
                  f"procs={total_procs} distinct={len(seen)} codes={len(codes)}",
                  flush=True)

    dups = sum(dup_counter.values())
    print(f"\ndone in {time.time()-started:.0f}s")
    print(f"saves read      : {len(files) - len([b for b in bad_files if b[0].endswith('.msav')])}")
    print(f"processors      : {total_procs}")
    print(f"distinct programs: {len(seen)}")
    print(f"duplicate copies : {dups} (skipped, {total_procs and 100.0*dups/total_procs:.1f}% of all)")
    print(f"findings        : {sum(severity.values())}  {dict(severity)}")
    print(f"hard (ERR+SUSP) : {sum(v for k, v in codes.items() if k[0] in ('ERR','SUSPECT'))}")
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

    ranked = sorted(per_save.items(), key=lambda kv: -kv[1][1])[:15]
    print("\nworst saves by hard findings:")
    for name, (procs, errs, warns) in ranked:
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
        "most_copied": [
            dict(seen[h], copies=extra + 1) for h, extra in dup_counter.most_common(50)
        ],
    }
    (OUT / "saves_analyse.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT / 'saves_analyse.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
