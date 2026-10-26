
"""Extract logic processors from downloaded .msav maps into a corpus directory.

Reads every *.msav under --src (default logic-corpus/_maps) with
tools/map_logic.read_save, strips blank lines, dedupes by the sha1 of the code,
and writes one <sha16>.mlog per unique program plus _meta.json holding the
provenance (source map, block kind, link names) that check_corpus.py expects.

    python tools/corpus/extract_maps.py
    python tools/corpus/check_corpus.py --procs _maps_procs --json out/_crawl/check-maps.json
"""
import argparse
import collections
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import map_logic  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main(argv=None):
    ap = argparse.ArgumentParser(description="extract logic programs from .msav maps")
    ap.add_argument("--src", default=str(ROOT / "logic-corpus" / "_maps"))
    ap.add_argument("--dst", default=str(ROOT / "logic-corpus" / "_maps_procs"))
    a = ap.parse_args(argv)

    src, dst = Path(a.src), Path(a.dst)
    dst.mkdir(parents=True, exist_ok=True)
    maps = sorted(src.glob("*.msav"))
    progs, bad = {}, []
    for p in maps:
        try:
            sv = map_logic.read_save(p)
        except Exception as e:
            bad.append([p.name, "%s: %s" % (type(e).__name__, str(e)[:100])])
            continue
        for ent in sv.get("logic") or []:
            stmts = [ln.strip() for ln in (ent.get("code") or "").split("\n") if ln.strip()]
            if not stmts:
                continue
            code = "\n".join(stmts)
            h = hashlib.sha1(code.encode("utf-8")).hexdigest()[:16]
            rec = progs.get(h)
            if rec is None:
                progs[h] = {
                    "sha": h, "block": ent.get("block"), "lines": len(stmts),
                    "link_names": [l["name"] for l in (ent.get("links") or [])],
                    "sources": [p.name], "labels": [], "code": code,
                }
            elif p.name not in rec["sources"]:
                rec["sources"].append(p.name)

    for h, rec in progs.items():
        (dst / (h + ".mlog")).write_text(rec["code"] + "\n", encoding="utf-8", newline="\n")
    meta = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "src": str(src), "maps": len(maps), "unreadable": bad,
        "unique_programs": len(progs),
        "programs": {h: {k: v for k, v in r.items() if k != "code"} for h, r in progs.items()},
    }
    (dst / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    by_block = collections.Counter(r["block"] for r in progs.values())
    print("maps: %d  unreadable: %d  unique programs: %d  lines: %d"
          % (len(maps), len(bad), len(progs), sum(r["lines"] for r in progs.values())))
    print("by block:", dict(by_block.most_common()))
    for fn, why in bad[:3]:
        print("  bad:", fn, why)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
