"""Download specific map ids (or search results) from the community site.

Usage:
    python tools/_fetch_ids.py 25872 25390 25780 20445 14962
    python tools/_fetch_ids.py --search 逻辑 --pages 4
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
    return json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else {}


def save_index(idx: dict) -> None:
    INDEX.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")


def grab(mid: str, idx: dict, meta: dict | None = None) -> bool:
    dest = OUT / f"mindustrytop-{mid}.msav"
    if dest.exists() and idx.get(mid, {}).get("logic"):
        print(f"  {mid} cached")
        return False
    try:
        S.download(mid, dest)
        info = ML.read_save(dest)
    except Exception as exc:  # noqa: BLE001
        print(f"  {mid} failed: {type(exc).__name__}: {exc}")
        dest.unlink(missing_ok=True)
        return False
    n = len(info.get("logic") or [])
    if n == 0:
        dest.unlink(missing_ok=True)
        idx[mid] = {"name": (meta or {}).get("name"), "logic": 0, "dropped": True}
        print(f"  {mid} no logic, deleted")
        save_index(idx)
        return False
    idx[mid] = {
        "name": (meta or {}).get("name"),
        "size": [info.get("width"), info.get("height")],
        "logic": n,
        "file": dest.name,
        "tags": (meta or {}).get("tags"),
        "mode": (meta or {}).get("mode"),
    }
    save_index(idx)
    print(f"  {mid} {info.get('width')}x{info.get('height')} {n} processor(s)")
    return True


def main(argv: list[str]) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    idx = load_index()
    got = 0
    if argv and argv[0] == "--search":
        q = argv[1]
        pages = int(argv[argv.index("--pages") + 1]) if "--pages" in argv else 3
        for page in range(pages):
            items = S.list_maps(q, page * 15)
            if not items:
                break
            print(f"search '{q}' page {page + 1}: {len(items)}")
            for it in items:
                if grab(str(it["id"]), idx, it):
                    got += 1
    else:
        for mid in argv:
            if grab(mid, idx):
                got += 1
    kept = sum(1 for v in idx.values() if not v.get("dropped"))
    print(f"new {got}, cache now {kept} map(s) with logic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
