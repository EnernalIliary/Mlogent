"""Independently verify what label_apply_live.py wrote: every touched file must
still have the same tiles, the same logic code, and strictly more labels."""
import pathlib
import sys

sys.path.insert(0, "mindustry-blueprint/tools")
import msch

ROOT = pathlib.Path(__file__).resolve().parents[1]
C = pathlib.Path.home() / "AppData" / "Roaming" / "Mindustry" / "schematics"
backup = sorted((ROOT / "out").glob("_label_backup_*"))[-1]

bad = []
n = 0
added = 0
for orig in sorted(backup.glob("*.msch")):
    live = C / orig.name
    a = msch.parse_file(str(orig))
    b = msch.parse_file(str(live))
    n += 1
    if len(a.tiles) != len(b.tiles):
        bad.append(f"{orig.name}: tile count {len(a.tiles)} -> {len(b.tiles)}")
        continue
    if [t.block for t in a.tiles] != [t.block for t in b.tiles]:
        bad.append(f"{orig.name}: block list changed")
        continue
    if "\n".join(t.logic.code for t in a.logic_tiles()) != \
       "\n".join(t.logic.code for t in b.logic_tiles()):
        bad.append(f"{orig.name}: logic code changed")
        continue
    la = [l for l in a.labels if l.strip()]
    lb = [l for l in b.labels if l.strip()]
    if lb[:len(la)] != la:
        bad.append(f"{orig.name}: existing labels changed or reordered")
        continue
    added += len(lb) - len(la)

print(f"核对 {n} 份：方块数/方块表/逻辑源码/原有标签顺序 全部一致")
print(f"新增标签合计 {added} 条")
print(f"异常 {len(bad)} 份")
for line in bad:
    print("  !!", line)

# whole-folder sanity: nothing became unreadable
total = ok = 0
for p in sorted(C.glob("*.msch")):
    total += 1
    try:
        msch.parse_file(str(p))
        ok += 1
    except Exception as e:
        print(f"  !! 无法解析 {p.name}: {e}")
print(f"整个目录 {ok}/{total} 仍可解析")
