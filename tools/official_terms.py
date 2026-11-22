"""Canonical vanilla content names from the shipped game language bundles.

Aliases help retrieval only; they never override the official Chinese name.
No generated prose, mlog operands or blueprint bytes are rewritten here.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
SOURCE = "data/game/bundles/bundle_zh_CN.properties"


def properties(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = re.match(r"\s*((?:block|unit|item|liquid|status)\.[^\s=]+\.name)\s*=\s*(.*)$", line)
        if match:
            value = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m[1], 16)), match[2])
            out[match[1]] = re.sub(r"\[[^\]]*\]", "", value).strip()
    return out


@lru_cache(maxsize=1)
def catalog() -> list[dict]:
    zh = properties(ROOT / SOURCE)
    en = properties(ROOT / "data/game/bundles/bundle.properties")
    aliases_path = ROOT / "data/game/aliases.json"
    aliases = json.loads(aliases_path.read_text(encoding="utf-8-sig")) if aliases_path.exists() else {}
    # The dump supplies categories; translations come exclusively from the bundle.
    blocks = json.loads((ROOT / "data/game/blocks.json").read_text(encoding="utf-8-sig"))
    turret_ids = {b['name'] for b in blocks if b.get('category') == 'turret'}
    rows = []
    for key, name in sorted(zh.items()):
        kind, ident, _ = key.split(".", 2)
        plural = 'statuses' if kind == 'status' else kind + 's'
        group = aliases.get(kind, aliases.get(plural, {}))
        names = group.get(ident, []) if isinstance(group, dict) else []
        rows.append({"kind": kind, "id": ident, "zh_CN": name,
                     "en": en.get(key, ident), "aliases": names,
                     "turret": kind == "block" and ident in turret_ids})
    return rows


def lookup(query: str, limit: int = 80, *, include_turrets: bool = False) -> list[dict]:
    """Return named entities, preferring longer Chinese names over substrings."""
    ascii_terms = set(re.findall(r"[a-z0-9_-]+", query.casefold()))
    candidates = []
    for row in catalog():
        names = [row['zh_CN'], *row['aliases']]
        for name in names:
            if query.strip() == name:
                candidates.append((0, len(query), row))
                continue
            if len(name) < 2:
                continue
            for m in re.finditer(re.escape(name), query):
                candidates.append((m.start(), m.end(), row))
    spans = []
    matched = set()
    for start, end, row in sorted(candidates, key=lambda c: -(c[1] - c[0])):
        if not any(start < b and end > a for a, b in spans):
            spans.append((start, end))
            matched.add((row['kind'], row['id']))
    selected = []
    for row in catalog():
        if ((row['kind'], row['id']) in matched or row['id'].casefold() in ascii_terms
                or row['en'].casefold() == query.strip().casefold()
                or (include_turrets and row['turret'])):
            selected.append({k: row[k] for k in ('kind', 'id', 'zh_CN', 'en')})
    return selected[:limit]
