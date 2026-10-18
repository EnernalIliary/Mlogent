"""Run the static checks over every processor in every save.

`map` tells you what is in a save; this tells you what is *wrong* in all of
them.  Aggregates by finding code so one code-level bug in my own checker
shows up as a spike instead of hiding in 105k individual reports.
"""
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


def main() -> int:
    files = sorted(SAVES.glob("*.msav"))
    codes = Counter()
    severity = Counter()
    per_save = defaultdict(lambda: [0, 0, 0])  # procs, errs, warns
    worst = []
    started = time.time()
    bad_files = []
    total_procs = 0
    for n, path in enumerate(files, 1):
        try:
            info = M.read_save(path)
        except Exception as exc:  # noqa: BLE001 - report, don't die
            bad_files.append((path.name, f"{type(exc).__name__}: {exc}"))
            continue
        names = info["block_types"]
        bucket = per_save[path.name]
        for tile in info["logic"]:
            code = tile["code"]
            if not code.strip():
                continue
            total_procs += 1
            bucket[0] += 1
            labels = [l["name"] for l in tile["links"]]
            try:
                found = C.analyse(code.splitlines(), labels)
            except Exception as exc:  # noqa: BLE001
                bad_files.append((f"{path.name}:{tile['x']},{tile['y']}",
                                  f"{type(exc).__name__}: {exc}"))
                continue
            for f in found:
                codes[(f.sev, f.code)] += 1
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
                  f"procs={total_procs} codes={len(codes)}", flush=True)

    print(f"\ndone in {time.time()-started:.0f}s")
    print(f"saves read      : {len(files) - len([b for b in bad_files if b[0].endswith('.msav')])}")
    print(f"processors      : {total_procs}")
    print(f"findings        : {sum(severity.values())}  {dict(severity)}")
    print(f"hard (ERR+SUSP) : {sum(v for k, v in codes.items() if k[0] in ('ERR','SUSPECT'))}")
    print("\nby code:")
    for (sev, code), count in codes.most_common(40):
        print(f"  {count:>7}  {sev:<7} {code}")
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
        "severity": dict(severity),
        "codes": {f"{k[0]}|{k[1]}": v for k, v in codes.items()},
        "per_save": {k: v for k, v in per_save.items()},
        "examples": worst,
        "unreadable": bad_files,
    }
    (OUT / "saves_analyse.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT / 'saves_analyse.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
