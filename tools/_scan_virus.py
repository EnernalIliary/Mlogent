"""One-shot: 病毒逻辑 across saves AND both blueprint corpora."""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mindustry-blueprint" / "tools"))

import map_logic as ML  # noqa: E402
import msch  # noqa: E402
import parallel  # noqa: E402

SAVES = Path(r"C:\Users\lliary\AppData\Roaming\Mindustry\saves")
USER_SCHEM = SAVES.parent / "schematics"
CAIME = ROOT / "out" / "caime"

BUILD = re.compile(r"^\s*ucontrol\s+build\b", re.I | re.M)


def virus_lines(code: str) -> list[str]:
    this_vars = {"@this"}
    this_vars.update(re.findall(r"^\s*set\s+(\S+)\s+@this\b", code, re.M))
    hits = []
    for line in code.splitlines():
        t = line.split()
        if len(t) >= 5 and t[0].lower() == "ucontrol" and t[1].lower() == "build":
            if t[-1] in this_vars:
                hits.append(line.strip())
    return hits


def scan_save(path_str: str) -> dict:
    p = Path(path_str)
    out = {"kind": "save", "file": p.name, "error": None,
           "progs": 0, "builders": 0, "viruses": []}
    try:
        info = ML.read_save(p)
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    seen: set[str] = set()
    for tile in info["logic"]:
        code = tile["code"]
        if not code.strip():
            continue
        out["progs"] += 1
        if BUILD.search(code):
            out["builders"] += 1
        v = virus_lines(code)
        if v:
            h = hashlib.sha1(code.encode()).hexdigest()[:10]
            out["viruses"].append({"where": f"{p.name}:{tile['x']},{tile['y']}",
                                   "hash": h, "line": v[0],
                                   "stmts": len(code.splitlines())})
            seen.add(h)
    return out


def scan_schem(path_str: str) -> dict:
    p = Path(path_str)
    out = {"kind": "schem", "file": p.name, "error": None,
           "progs": 0, "builders": 0, "viruses": []}
    try:
        sch = msch.parse_bytes(p.read_bytes())
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    for t in sch.tiles:
        code = (t.logic.code if t.logic is not None else "") or ""
        if not code.strip():
            continue
        out["progs"] += 1
        if BUILD.search(code):
            out["builders"] += 1
        v = virus_lines(code)
        if v:
            h = hashlib.sha1(code.encode()).hexdigest()[:10]
            out["viruses"].append({"where": f"{p.name}:{t.x},{t.y}",
                                   "hash": h, "line": v[0],
                                   "stmts": len(code.splitlines())})
    return out


def report(name: str, results: list[dict]) -> None:
    progs = sum(r["progs"] for r in results)
    builders = sum(r["builders"] for r in results)
    vir = [v for r in results for v in r["viruses"]]
    distinct = {v["hash"] for v in vir}
    bad = [r for r in results if r["error"]]
    print(f"\n== {name}")
    print(f"  files             : {len(results)} ({len(bad)} unreadable)")
    print(f"  programs          : {progs}")
    print(f"  use `ucontrol build`: {builders}")
    print(f"  VIRUS programs    : {len(vir)}  distinct {len(distinct)}")
    for r in sorted((r for r in results if r["viruses"]), key=lambda r: -len(r["viruses"]))[:12]:
        print(f"    {len(r['viruses']):>3}  {r['file']}")
    for v in vir[:6]:
        print(f"    {v['where']:<40} {v['stmts']:>4} stmt  {v['line']}")


def main() -> int:
    saves = sorted(SAVES.glob("*.msav"))
    report("saves", parallel.run(scan_save, [str(p) for p in saves], label="saves"))

    for name, d in (("my schematics", USER_SCHEM), ("caime pack", CAIME)):
        if not d.exists():
            print(f"\n== {name}: {d} missing")
            continue
        files = sorted(d.rglob("*.msch"))
        report(name, parallel.run(scan_schem, [str(p) for p in files], label=name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
