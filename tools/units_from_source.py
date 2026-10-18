"""Extract unit stats from `UnitTypes.java` into `unit_attrs.json`.

Why this exists: writing logic starts with *picking a unit*. `ubind @flare` vs
`ubind @mace` is a decision about speed, health, payload and whether the thing
flies -- and before this table the only source was my memory of the game.

Only fields that the source actually sets are recorded; anything absent is the
engine default, which is printed from `UnitType.java` so "absent" is
interpretable instead of ambiguous.

Run:  python tools/units_from_source.py [--check]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "Mindustry-Source/core/src/mindustry"
UNITS = SRC / "content/UnitTypes.java"
TYPE = SRC / "type/UnitType.java"
OUT = pathlib.Path(__file__).resolve().parent / "unit_attrs.json"

# fields worth knowing before you write logic for a unit
FIELDS = ("speed", "health", "armor", "hitSize", "itemCapacity", "flying",
          "mineSpeed", "mineTier", "buildSpeed", "accel", "drag",
          "boostMultiplier", "payloadCapacity", "range")

_START = re.compile(r'^(\s*)(\w+) = new UnitType\("([a-z0-9-]+)"\)\{\{')
_NUM = r"(-?\d+(?:\.\d+)?)f?"


def defaults() -> dict[str, str]:
    """Engine defaults, parsed from the field declarations in UnitType.java.

    Declarations are grouped (`float speed = 1.1f, boostMultiplier = 1f;`), so
    each group is split before matching -- a naive per-field regex otherwise
    picks up the *next* field's value, which is how the first attempt reported
    `health -> 1f`.
    """
    t = TYPE.read_text("utf-8", errors="replace")
    out: dict[str, str] = {}
    for m in re.finditer(r"^\s*(?:public|protected)?\s*(?:float|int|boolean)\s+([^;]+);",
                         t, re.M):
        decl = m.group(1)
        if "(" in decl or "{" in decl:
            continue
        for part in decl.split(","):
            q = re.match(r"\s*(\w+)\s*=\s*([^,]+)$", part.strip())
            if not q:
                continue
            name, value = q.group(1), q.group(2).strip()
            out.setdefault(name, value.rstrip("f"))
    return out


def unit_blocks(text: str) -> list[tuple[str, str, list[str]]]:
    """Slice `x = new UnitType("x"){{ ... }};` bodies.

    The closing brace is `}};` (double-brace initializer), and its indent must be
    matched against the *opening* line's indent rather than hard-coded -- the
    first version assumed `};` at 8 spaces and silently extracted zero units.
    """
    lines = text.split("\n")
    blocks: list[tuple[str, str, list[str]]] = []
    cur: tuple[str, str, list[str]] | None = None
    indent = 0
    for line in lines:
        if cur is None:
            m = _START.match(line)
            if m:
                indent = len(m.group(1))
                cur = (m.group(2), m.group(3), [])
            continue
        if line.strip() in ("}};", "};") and len(line) - len(line.lstrip()) <= indent:
            blocks.append(cur)
            cur = None
            continue
        cur[2].append(line)
    return blocks


def scalar(body: list[str], field: str) -> str | None:
    pat = re.compile(r"^\s*" + field + r"\s*=\s*" + _NUM + r"\s*;")
    for line in body:
        m = pat.match(line)
        if m:
            return m.group(1)
    if re.search(r"^\s*" + field + r"\s*=\s*true\s*;", "\n".join(body), re.M):
        return "true"
    return None


def weapons(body: list[str]) -> dict:
    text = "\n".join(body)
    out: dict = {"count": text.count("new Weapon()")}
    reload = re.search(r"^\s*reload\s*=\s*" + _NUM + r"\s*;", text, re.M)
    if reload:
        out["reload"] = reload.group(1)          # ticks between shots
    bullet = re.search(r"bullet\s*=\s*new (\w+)\(" + _NUM + r"\s*,\s*" + _NUM, text)
    if bullet:
        out["bullet"] = bullet.group(1)
        out["bullet_speed"] = bullet.group(2)
        out["bullet_damage"] = bullet.group(3)
    return out


def build() -> dict:
    text = UNITS.read_text("utf-8", errors="replace")
    dflt = defaults()
    units: dict[str, dict] = {}
    for field, name, body in unit_blocks(text):
        rec: dict = {}
        for f in FIELDS:
            v = scalar(body, f)
            if v is not None:
                rec[f] = v
        w = weapons(body)
        if w.get("count"):
            rec["weapons"] = w
        units[name] = rec
    return {
        "_source": "Mindustry-Source/core/src/mindustry/content/UnitTypes.java",
        "_note": ("only fields the source sets are listed; absent ones are the "
                  "engine default in `defaults`"),
        "count": len(units),
        "defaults": {k: v for k, v in dflt.items()
                     if k in FIELDS or k in ("speed", "health")},
        "units": units,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="compare against the committed JSON instead of writing")
    args = ap.parse_args()
    data = build()
    text = json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if args.check:
        cur = OUT.read_text("utf-8") if OUT.exists() else ""
        same = cur == text
        print(("ok      " if same else "STALE   ") + f"{OUT.name}: {data['count']} units")
        return 0 if same else 1
    OUT.write_text(text, "utf-8")
    print(f"wrote {OUT.name}: {data['count']} units, "
          f"{sum(1 for u in data['units'].values() if 'weapons' in u)} armed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
