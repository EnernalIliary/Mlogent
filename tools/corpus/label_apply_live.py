"""Write auto-derived labels straight into the game's schematic folder.

Safety model:

* only ADDS labels, never removes or reorders an existing one;
* only adds values whose rule scored >= MIN_PRECISION on held-out data;
* rewrites nothing but the `labels` tag -- every other byte of the payload is
  copied through, so block configs (wireless links etc.) cannot be damaged;
* copies the original of every file it touches to a timestamped backup dir and
  writes a manifest of the exact old -> new label lists;
* verifies each result by re-parsing: same tiles, same block names, byte-identical
  logic code, and labels == old + added. A file that fails verification is
  restored from its backup and reported.

    python tools/label_apply_live.py --dry-run
    python tools/label_apply_live.py
"""
from __future__ import annotations

import collections
import json
import pathlib
import shutil
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "mindustry-blueprint" / "tools"))
sys.path.insert(0, str(HERE))
import msch  # noqa: E402
import label_auto as L  # noqa: E402

SCHEM = pathlib.Path.home() / "AppData" / "Roaming" / "Mindustry" / "schematics"
SKIP_OVER = 20       # the palette file carries 69 labels; leave it alone


def canonical(rows) -> dict[str, str]:
    """value -> the most common full label markup the user actually typed."""
    tally: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for p in sorted(SCHEM.glob("*.msch")):
        try:
            sch = msch.parse_file(str(p))
        except Exception:
            continue
        for lab in sch.labels or []:
            _, text = L.split_label(lab)
            tally[text][lab] += 1
    return {v: c.most_common(1)[0][0] for v, c in tally.items() if c}


def logic_blob(sch) -> str:
    return "\n".join(t.logic.code for t in sch.logic_tiles())


def main() -> None:
    dry = "--dry-run" in sys.argv
    rules = json.loads(L.RULES.read_text("utf-8"))
    trusted = {v: r for v, r in rules.items() if r.get("precision", 0) >= L.MIN_PRECISION}
    print(f"可信规则 {len(trusted)} 条 (留出集精确率 >= {L.MIN_PRECISION:.0%})")

    markup = canonical(None)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = ROOT / "out" / f"_label_backup_{stamp}"
    manifest: list[dict] = []
    changed = added_total = 0
    failed: list[str] = []

    for p in sorted(SCHEM.glob("*.msch")):
        try:
            sch = msch.parse_file(str(p))
        except Exception as e:
            failed.append(f"{p.name}: unreadable ({e})")
            continue
        old = [l for l in (sch.labels or []) if l.strip()]
        if len(old) >= SKIP_OVER:
            continue
        have = {L.split_label(l)[1] for l in old}
        blocks, toks, biggest = L.facts(sch)
        add_values = sorted(v for v, r in trusted.items()
                            if v not in have and L.predict(r, blocks, toks, biggest))
        if not add_values:
            continue
        new = old + [markup.get(v, v) for v in add_values]
        if dry:
            print(f"  +{len(add_values)}  {p.name}: {'、'.join(add_values)}")
            added_total += len(add_values)
            changed += 1
            continue

        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, backup / p.name)
        tmp = p.with_suffix(".msch.tmp")
        tmp.write_bytes(L.rewrite_labels(p, new, p.parent).read_bytes())
        tmp.replace(p)

        # verify
        ok = True
        try:
            after = msch.parse_file(str(p))
            if len(after.tiles) != len(sch.tiles):
                ok = False
            elif [t.block for t in after.tiles] != [t.block for t in sch.tiles]:
                ok = False
            elif logic_blob(after) != logic_blob(sch):
                ok = False
            elif [l for l in after.labels if l.strip()] != new:
                ok = False
        except Exception:
            ok = False
        if not ok:
            shutil.copy2(backup / p.name, p)
            failed.append(f"{p.name}: verification failed, restored")
            continue

        manifest.append({"file": p.name, "old": old, "added": add_values})
        added_total += len(add_values)
        changed += 1

    if not dry and manifest:
        (backup / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"备份与清单: {backup}")

    print(f"{'将修改' if dry else '已修改'} {changed} 份，新增标签 {added_total} 条")
    for line in failed:
        print(f"  !! {line}")


if __name__ == "__main__":
    main()
