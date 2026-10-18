"""Add the ILI label to every schematic that carries this author's signature.

Reuses the same safety model as label_apply_live.py: additions only, tags segment
only, per-file backup + manifest, and a re-parse check that the tiles and the
logic code are untouched.
"""
import json
import pathlib
import shutil
import sys
import time

sys.path.insert(0, "mindustry-blueprint/tools")
sys.path.insert(0, "tools")
import msch  # noqa: E402
import label_auto as L  # noqa: E402
import label_apply_live as LIVE  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
C = pathlib.Path.home() / "AppData" / "Roaming" / "Mindustry" / "schematics"


def main() -> None:
    dry = "--dry-run" in sys.argv
    rows = json.loads((ROOT / "out" / "_ili_classified.json").read_text("utf-8"))
    markup = LIVE.canonical(None).get("ILI", "ILI")
    todo = [r for r in rows if not r["has_ili"]]
    print(f"ILI 标签写法: {ascii(markup)}")
    print(f"需要补 {len(todo)} 份（强署名 {sum(1 for r in todo if r['strong'])}，"
          f"弱提及 {sum(1 for r in todo if not r['strong'])}）")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = ROOT / "out" / f"_ili_backup_{stamp}"
    manifest = []
    failed = []

    for r in todo:
        p = C / r["file"]
        if dry:
            print(f"  +ILI  {p.name}  ({'strong' if r['strong'] else 'weak'})")
            continue
        sch = msch.parse_file(str(p))
        old = [l for l in (sch.labels or []) if l.strip()]
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, backup / p.name)
        tmp = p.with_suffix(".msch.tmp")
        tmp.write_bytes(L.rewrite_labels(p, old + [markup], p.parent).read_bytes())
        tmp.replace(p)

        ok = True
        try:
            after = msch.parse_file(str(p))
            if [t.block for t in after.tiles] != [t.block for t in sch.tiles]:
                ok = False
            elif LIVE.logic_blob(after) != LIVE.logic_blob(sch):
                ok = False
            elif [l for l in after.labels if l.strip()] != old + [markup]:
                ok = False
        except Exception:
            ok = False
        if not ok:
            shutil.copy2(backup / p.name, p)
            failed.append(p.name)
            continue
        manifest.append({"file": p.name, "old": old, "added": ["ILI"],
                         "strong": r["strong"]})

    if not dry and manifest:
        (backup / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"备份与清单: {backup}")
    print(f"{'将修改' if dry else '已修改'} {len(manifest) if not dry else len(todo)} 份"
          f"，失败 {len(failed)}")
    for n in failed:
        print("  !!", n)


if __name__ == "__main__":
    main()
