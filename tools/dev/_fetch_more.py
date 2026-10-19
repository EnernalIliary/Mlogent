"""Download a few more maps from the community site, keeping a local cache.

Usage:  python tools/_fetch_more.py [--want 24] [--pages 12]

Rate limited by map_site itself (1.1 s between requests).  Skips maps already in
out/maps/index.json, and deletes anything that arrives without a single logic
processor (the user asked not to keep dead weight).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mindustry-blueprint" / "tools"))

import map_logic as ML  # noqa: E402
import map_site as S  # noqa: E402

OUT = ROOT / "out" / "maps"
INDEX = OUT / "index.json"


def load_index() -> dict:
    if INDEX.exists():
        return json.loads(INDEX.read_text(encoding="utf-8"))
    return {}


def save_index(idx: dict) -> None:
    INDEX.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")


def main(argv: list[str]) -> int:
    want = 24
    pages = 12
    i = 0
    while i < len(argv):
        if argv[i] == "--want":
            want = int(argv[i + 1]); i += 2
        elif argv[i] == "--pages":
            pages = int(argv[i + 1]); i += 2
        else:
            i += 1

    OUT.mkdir(parents=True, exist_ok=True)
    idx = load_index()
    got = 0
    begin = 0
    tried = 0
    for page in range(pages):
        try:
            items = S.list_maps("", begin)
        except Exception as exc:  # noqa: BLE001
            print(f"list failed at begin={begin}: {exc}")
            break
        if not items:
            print(f"page {page + 1}: empty, stop")
            break
        print(f"page {page + 1}: {len(items)} map(s)")
        for it in items:
            mid = str(it["id"])
            begin = max(begin, it["id"])
            if mid in idx:
                continue
            tried += 1
            dest = OUT / f"mindustrytop-{mid}.msav"
            try:
                S.download(mid, dest)
            except Exception as exc:  # noqa: BLE001
                print(f"  {mid} download failed: {type(exc).__name__}: {exc}")
                continue
            try:
                info = ML.read_save(dest)
            except Exception as exc:  # noqa: BLE001
                print(f"  {mid} unreadable ({exc}), deleting")
                dest.unlink(missing_ok=True)
                continue
            n = len(info.get("logic") or [])
            if n == 0:
                dest.unlink(missing_ok=True)
                idx[mid] = {"name": it.get("name"), "logic": 0, "dropped": True}
                print(f"  {mid} no logic, deleted")
                continue
            idx[mid] = {
                "name": it.get("name"),
                "size": [info.get("width"), info.get("height")],
                "logic": n,
                "file": dest.name,
                "tags": it.get("tags"),
                "mode": it.get("mode"),
            }
            save_index(idx)
            got += 1
            print(f"  {mid} {info.get('width')}x{info.get('height')} {n} processor(s)  [{got}/{want}]")
            if got >= want:
                break
        if got >= want:
            break
    save_index(idx)
    kept = sum(1 for v in idx.values() if not v.get("dropped"))
    print(f"new {got}, tried {tried}, cache now {kept} map(s) with logic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
